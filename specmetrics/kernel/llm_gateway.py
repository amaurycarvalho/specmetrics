from __future__ import annotations

import json
import os
import time
import uuid
from collections import deque
from pathlib import Path
from threading import Lock
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

try:
    import litellm

    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    litellm = None  # type: ignore[assignment]

_DEFAULT_RPM_LIMIT = 15
_DEFAULT_MAX_TOKENS = 4096
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BATCH_MAX_CHARS = 100000

_LITELLM_EXCEPTIONS: tuple[type[Exception], ...] = ()
if HAS_LITELLM:
    _LITELLM_EXCEPTIONS = (
        getattr(litellm, "AuthenticationError", Exception),
        getattr(litellm, "RateLimitError", Exception),
        getattr(litellm, "Timeout", Exception),
        getattr(litellm, "APIError", Exception),
        getattr(litellm, "ServiceUnavailableError", Exception),
        Exception,
    )


_CONFIG_SEARCH_PATHS = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "specmetrics",
    Path("/etc/specmetrics"),
]


def _load_llm_config_rpm() -> int | None:
    for base in _CONFIG_SEARCH_PATHS:
        for fname in ("config.yml", "config.yaml", "config.json"):
            path = base / fname
            if path.exists():
                try:
                    import ruamel.yaml

                    yaml = ruamel.yaml.YAML(typ="safe")
                    data = yaml.load(path.read_text(encoding="utf-8"))
                    rpm = (
                        (data or {})
                        .get("plugins", {})
                        .get("extraction_stage", {})
                        .get("llm", {})
                        .get("rpm_limit")
                    )
                    if rpm is not None:
                        return int(rpm)
                except Exception:
                    return None
    return None


class LLMGatewayConfig:
    provider: str
    model: str
    api_key: str | None
    api_url: str | None
    rpm_limit: int
    max_tokens: int
    max_retries: int
    batch_max_chars: int

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        api_url: str | None = None,
        rpm_limit: int | None = None,
        max_tokens: int = _DEFAULT_MAX_TOKENS,
        max_retries: int = _DEFAULT_MAX_RETRIES,
        batch_max_chars: int = _DEFAULT_BATCH_MAX_CHARS,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.api_url = api_url
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.batch_max_chars = batch_max_chars

        if rpm_limit is not None:
            self.rpm_limit = rpm_limit
        else:
            env_rpm = os.environ.get("SPECMETRICS_LLM_RPM_LIMIT")
            if env_rpm is not None:
                try:
                    self.rpm_limit = int(env_rpm)
                except (ValueError, TypeError):
                    self.rpm_limit = _DEFAULT_RPM_LIMIT
            else:
                cfg_rpm = _load_llm_config_rpm()
                self.rpm_limit = cfg_rpm if cfg_rpm is not None else _DEFAULT_RPM_LIMIT


class LLMCallRecord:
    call_id: str
    provider: str
    model: str
    prompt_tokens: int
    response_tokens: int
    duration_ms: int
    rate_limit_delay_ms: int
    retry_count: int
    status: str
    error_message: str | None
    timestamp: str

    def __init__(
        self,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        response_tokens: int = 0,
        duration_ms: int = 0,
        rate_limit_delay_ms: int = 0,
        retry_count: int = 0,
        status: str = "success",
        error_message: str | None = None,
    ) -> None:
        self.call_id = str(uuid.uuid4())
        self.provider = provider
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.response_tokens = response_tokens
        self.duration_ms = duration_ms
        self.rate_limit_delay_ms = rate_limit_delay_ms
        self.retry_count = retry_count
        self.status = status
        self.error_message = error_message
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "provider": self.provider,
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "response_tokens": self.response_tokens,
            "duration_ms": self.duration_ms,
            "rate_limit_delay_ms": self.rate_limit_delay_ms,
            "retry_count": self.retry_count,
            "status": self.status,
            "error_message": self.error_message,
            "timestamp": self.timestamp,
        }


class RateLimiter:
    rpm_limit: int
    timestamps: deque[float]
    _lock: Lock

    def __init__(self, rpm_limit: int) -> None:
        self.rpm_limit = rpm_limit
        self.timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> float:
        if self.rpm_limit <= 0:
            return 0.0

        with self._lock:
            now = time.monotonic()
            cutoff = now - 60.0

            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.rpm_limit:
                oldest = self.timestamps[0]
                delay = 60.0 - (now - oldest)
                if delay > 0:
                    return delay

            return 0.0

    def wait_and_record(self) -> float:
        delay = self.acquire()
        if delay > 0:
            try:
                time.sleep(delay)
            except KeyboardInterrupt:
                logger.warning(
                    "rate_limiter_interrupted",
                    completed_calls=len(self.timestamps),
                )
                raise
        with self._lock:
            self.timestamps.append(time.monotonic())
        return delay


class DocumentPayload:
    document_id: str
    content: str
    document_type: str

    def __init__(self, document_id: str, content: str, document_type: str) -> None:
        self.document_id = document_id
        self.content = content
        self.document_type = document_type


class BatchRequest:
    system_prompt: str
    documents: list[DocumentPayload]
    json_schema: dict[str, Any] | None

    def __init__(
        self,
        system_prompt: str,
        documents: list[DocumentPayload],
        json_schema: dict[str, Any] | None = None,
    ) -> None:
        self.system_prompt = system_prompt
        self.documents = documents
        self.json_schema = json_schema

    def assemble_prompt(self) -> str:
        parts: list[str] = []
        for doc in self.documents:
            parts.append(f'Document "{doc.document_id}": {doc.content}')
        doc_list = ", ".join(
            f'"{d.document_id}": {{"elements": [...]}}' for d in self.documents
        )
        parts.append(f"Respond with a JSON object keyed by document ID: {{{doc_list}}}")
        return "\n\n".join(parts)

    def _estimate_chars(self) -> int:
        total = len(self.system_prompt)
        for doc in self.documents:
            total += len(doc.content) + len(doc.document_id) + 50
        return total

    def split(self, max_chars: int) -> list[BatchRequest]:
        if self._estimate_chars() <= max_chars:
            return [self]

        sub_batches: list[BatchRequest] = []
        current_docs: list[DocumentPayload] = []
        current_size = len(self.system_prompt)

        for doc in self.documents:
            doc_size = len(doc.content) + len(doc.document_id) + 50
            if current_size + doc_size > max_chars and current_docs:
                sub_batches.append(
                    BatchRequest(
                        system_prompt=self.system_prompt,
                        documents=current_docs,
                        json_schema=self.json_schema,
                    )
                )
                current_docs = []
                current_size = len(self.system_prompt)
            current_docs.append(doc)
            current_size += doc_size

        if current_docs:
            sub_batches.append(
                BatchRequest(
                    system_prompt=self.system_prompt,
                    documents=current_docs,
                    json_schema=self.json_schema,
                )
            )

        return sub_batches


def parse_batch_response(
    response_text: str, batch: BatchRequest
) -> dict[str, list[dict[str, Any]]]:
    data = json.loads(response_text)
    if not isinstance(data, dict):
        raise ValueError("Batch response is not a JSON object")

    expected_ids = {doc.document_id for doc in batch.documents}
    returned_ids = set(data.keys())
    missing_ids = expected_ids - returned_ids
    if missing_ids:
        raise ValueError(
            f"Batch response missing document IDs: {', '.join(sorted(missing_ids))}"
        )

    results: dict[str, list[dict[str, Any]]] = {}
    for doc in batch.documents:
        doc_id = doc.document_id
        doc_data = data.get(doc_id, {})
        if isinstance(doc_data, dict):
            results[doc_id] = doc_data.get("elements", [])
        elif isinstance(doc_data, list):
            results[doc_id] = doc_data
        else:
            results[doc_id] = []
    return results


def _detect_provider(model: str) -> str:
    if (
        model.startswith("gpt-")
        or model.startswith("text-")
        or model.startswith("ft:gpt")
    ):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gemini-"):
        return "google"
    if model.startswith("ollama/"):
        return "ollama"
    if model.startswith("azure/"):
        return "azure"
    return "openai"


def _supports_json_mode(provider: str) -> bool:
    return provider in ("openai", "azure")


def _build_json_instruction(provider: str) -> str:
    if _supports_json_mode(provider):
        return ""
    return "\n\nRespond with valid JSON only. No markdown fences."


def _build_completion_kwargs(
    config: LLMGatewayConfig,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": config.model,
    }
    if config.api_url:
        kwargs["api_base"] = config.api_url
        kwargs["custom_llm_provider"] = "openai"
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.max_tokens:
        kwargs["max_tokens"] = config.max_tokens
    return kwargs


class LLMGateway:
    config: LLMGatewayConfig
    rate_limiter: RateLimiter
    call_records: list[LLMCallRecord]

    def __init__(self, config: LLMGatewayConfig) -> None:
        self.config = config
        self.rate_limiter = RateLimiter(config.rpm_limit)
        self.call_records: list[LLMCallRecord] = []

    def complete(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = True,
    ) -> str:
        if not HAS_LITELLM:
            raise RuntimeError(
                "LiteLLM is not installed. Install with: pip install litellm"
            )

        provider = _detect_provider(self.config.model)
        rate_limit_delay = self.rate_limiter.wait_and_record()
        rate_limit_delay_ms = int(rate_limit_delay * 1000)

        messages = self._build_messages(
            system_prompt, user_message, json_mode, provider
        )

        completion_kwargs = _build_completion_kwargs(self.config)

        if json_mode and _supports_json_mode(provider):
            completion_kwargs["response_format"] = {"type": "json_object"}

        last_error: str | None = None
        retry_count = 0
        start_time = time.monotonic()

        for attempt in range(1 + self.config.max_retries):
            try:
                response = litellm.completion(
                    **completion_kwargs,
                    messages=messages,
                )
                duration_ms = int((time.monotonic() - start_time) * 1000)
                content = response.choices[0].message.content

                if json_mode:
                    try:
                        json.loads(content)
                    except json.JSONDecodeError:
                        if attempt < self.config.max_retries:
                            retry_count += 1
                            corrected_prompt = (
                                "You MUST respond with valid JSON only. "
                                "No explanatory text. No markdown fences.\n\n"
                                + user_message
                            )
                            messages[-1]["content"] = corrected_prompt
                            continue
                        raise

                prompt_tokens = (
                    getattr(response, "usage", None)
                    and getattr(response.usage, "prompt_tokens", 0)
                    or 0
                )
                response_tokens = (
                    getattr(response, "usage", None)
                    and getattr(response.usage, "completion_tokens", 0)
                    or 0
                )

                record = LLMCallRecord(
                    provider=provider,
                    model=self.config.model,
                    prompt_tokens=prompt_tokens,
                    response_tokens=response_tokens,
                    duration_ms=duration_ms,
                    rate_limit_delay_ms=rate_limit_delay_ms,
                    retry_count=retry_count,
                    status="success",
                )
                self.call_records.append(record)
                logger.info("llm_call", **record.to_dict())
                return content

            except _LITELLM_EXCEPTIONS as exc:
                retry_count += 1
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self.config.max_retries:
                    backoff = 2**attempt
                    logger.warning(
                        "llm_retry",
                        attempt=attempt + 1,
                        max_retries=self.config.max_retries,
                        delay_s=backoff,
                        error=last_error,
                    )
                    try:
                        time.sleep(backoff)
                    except KeyboardInterrupt:
                        logger.warning(
                            "llm_retry_interrupted",
                            completed_calls=len(self.rate_limiter.timestamps),
                        )
                        raise
                else:
                    duration_ms = int((time.monotonic() - start_time) * 1000)
                    record = LLMCallRecord(
                        provider=provider,
                        model=self.config.model,
                        duration_ms=duration_ms,
                        rate_limit_delay_ms=rate_limit_delay_ms,
                        retry_count=retry_count,
                        status="failed",
                        error_message=last_error,
                    )
                    self.call_records.append(record)
                    logger.error("llm_call_failed", **record.to_dict())
                    raise RuntimeError(last_error) from exc

        duration_ms = int((time.monotonic() - start_time) * 1000)
        record = LLMCallRecord(
            provider=provider,
            model=self.config.model,
            duration_ms=duration_ms,
            rate_limit_delay_ms=rate_limit_delay_ms,
            retry_count=retry_count,
            status="failed",
            error_message=last_error or "Max retries exceeded",
        )
        self.call_records.append(record)
        logger.error("llm_call_failed", **record.to_dict())
        raise RuntimeError(
            f"LLM call failed after {self.config.max_retries} retries: {last_error}"
        )

    def complete_batch(
        self, batch: BatchRequest, json_mode: bool = True
    ) -> dict[str, list[dict[str, Any]]]:
        sub_batches = batch.split(self.config.batch_max_chars)
        all_results: dict[str, list[dict[str, Any]]] = {}

        for sub_batch in sub_batches:
            provider = _detect_provider(self.config.model)
            user_message = sub_batch.assemble_prompt()
            json_instruction = _build_json_instruction(provider)
            system_prompt = sub_batch.system_prompt + json_instruction

            try:
                response_text = self.complete(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    json_mode=json_mode,
                )
                parsed = parse_batch_response(response_text, sub_batch)
                for doc_id, elements in parsed.items():
                    all_results.setdefault(doc_id, []).extend(elements)
            except (json.JSONDecodeError, ValueError, RuntimeError):
                logger.warning(
                    "batch_failed_retrying_individual",
                    doc_count=len(sub_batch.documents),
                )
                for doc in sub_batch.documents:
                    try:
                        single_prompt = f'Document "{doc.document_id}": {doc.content}'
                        response_text = self.complete(
                            system_prompt=system_prompt,
                            user_message=single_prompt,
                            json_mode=json_mode,
                        )
                        single_batch = BatchRequest(
                            system_prompt=sub_batch.system_prompt,
                            documents=[doc],
                            json_schema=sub_batch.json_schema,
                        )
                        parsed = parse_batch_response(response_text, single_batch)
                        all_results[doc.document_id] = parsed.get(doc.document_id, [])
                    except (json.JSONDecodeError, ValueError, RuntimeError):
                        logger.warning(
                            "individual_doc_failed",
                            doc_id=doc.document_id,
                        )
                        all_results[doc.document_id] = []

        return all_results

    def _build_messages(
        self,
        system_prompt: str,
        user_message: str,
        json_mode: bool,
        provider: str,
    ) -> list[dict[str, str]]:
        system = system_prompt
        if json_mode and not _supports_json_mode(provider):
            system += _build_json_instruction(provider)

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

    def get_summary_stats(self) -> dict[str, Any]:
        total_calls = len(self.call_records)
        total_tokens = sum(
            r.prompt_tokens + r.response_tokens for r in self.call_records
        )
        total_duration_ms = sum(r.duration_ms for r in self.call_records)
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "total_duration_ms": total_duration_ms,
        }
