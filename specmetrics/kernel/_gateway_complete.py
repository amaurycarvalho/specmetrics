"""Complete-message logic for the LLM gateway, provided as a mixin."""

from __future__ import annotations

import json
import time
from types import ModuleType
from typing import Protocol, Self

import structlog

from ._completion import (
    HAS_LITELLM,
    build_completion_kwargs,
    build_json_instruction,
    detect_provider,
    get_litellm_exceptions,
    supports_json_mode,
)
from ._config import LLMGatewayConfig
from ._models import LLMCallRecord, RateLimiter

logger = structlog.get_logger(__name__)


class _TokenUsage(Protocol):
    """Token counts reported by a completion response usage block."""

    prompt_tokens: int
    completion_tokens: int


class _CompletionResponse(Protocol):
    """Minimal shape of a litellm completion response used by this mixin."""

    usage: _TokenUsage


def _current_litellm() -> ModuleType:
    """Return the litellm module bound on the llm_gateway namespace.

    The gateway tests patch ``llm_gateway.litellm``; resolving the reference
    lazily keeps that contract intact after the completion logic was split
    into this mixin.
    """
    from . import llm_gateway

    return llm_gateway.litellm


class CompleteMixin:
    """Provide the single-message completion flow for the LLM gateway."""

    config: LLMGatewayConfig
    rate_limiter: RateLimiter
    call_records: list[LLMCallRecord]

    def complete(
        self: Self,
        system_prompt: str,
        user_message: str,
        json_mode: bool = True,
    ) -> str:
        """Complete a message, retrying on transient failures and enforcing JSON."""
        if not HAS_LITELLM:
            raise RuntimeError(
                "LiteLLM is not installed. Install with: pip install litellm"
            )

        provider = detect_provider(self.config.model)
        rate_limit_delay = self.rate_limiter.wait_and_record()
        rate_limit_delay_ms = int(rate_limit_delay * 1000)

        messages = self._build_messages(
            system_prompt, user_message, json_mode, provider
        )

        completion_kwargs = build_completion_kwargs(self.config)

        if json_mode and supports_json_mode(provider):
            completion_kwargs["response_format"] = {"type": "json_object"}

        last_error: str | None = None
        retry_count = 0
        start_time = time.monotonic()
        litellm_exceptions = get_litellm_exceptions()

        for attempt in range(1 + self.config.max_retries):
            try:
                response = _current_litellm().completion(
                    **completion_kwargs,
                    messages=messages,
                )
                duration_ms = int((time.monotonic() - start_time) * 1000)
                content = response.choices[0].message.content

                if json_mode and self._enforce_json_response(
                    content, attempt, messages, user_message
                ):
                    retry_count += 1
                    continue

                prompt_tokens, response_tokens = self._extract_token_counts(response)
                self._record_success(
                    provider,
                    duration_ms,
                    rate_limit_delay_ms,
                    retry_count,
                    prompt_tokens,
                    response_tokens,
                )
                return content

            except litellm_exceptions as exc:
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
                    self._sleep_with_interrupt(backoff, attempt)
                    continue

                self._record_failure(
                    provider,
                    int((time.monotonic() - start_time) * 1000),
                    rate_limit_delay_ms,
                    retry_count,
                    last_error,
                )
                raise RuntimeError(last_error) from exc

        self._record_failure(
            provider,
            int((time.monotonic() - start_time) * 1000),
            rate_limit_delay_ms,
            retry_count,
            last_error or "Max retries exceeded",
        )
        raise RuntimeError(
            f"LLM call failed after {self.config.max_retries} retries: {last_error}"
        )

    def _build_messages(
        self: Self,
        system_prompt: str,
        user_message: str,
        json_mode: bool,
        provider: str,
    ) -> list[dict[str, str]]:
        system = system_prompt
        if json_mode and not supports_json_mode(provider):
            system += build_json_instruction(provider)

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ]

    def _enforce_json_response(
        self: Self,
        content: str,
        attempt: int,
        messages: list[dict[str, str]],
        user_message: str,
    ) -> bool:
        """Validate JSON output, arming a retry with a corrected prompt when needed."""
        try:
            json.loads(content)
        except json.JSONDecodeError:
            if attempt < self.config.max_retries:
                messages[-1]["content"] = (
                    "You MUST respond with valid JSON only. "
                    "No explanatory text. No markdown fences.\n\n" + user_message
                )
                return True
            raise
        return False

    def _extract_token_counts(self: Self, response: _CompletionResponse) -> tuple[int, int]:
        """Extract prompt and response token counts from a completion response."""
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        response_tokens = getattr(usage, "completion_tokens", 0) or 0
        return prompt_tokens, response_tokens

    def _record_success(
        self: Self,
        provider: str,
        duration_ms: int,
        rate_limit_delay_ms: int,
        retry_count: int,
        prompt_tokens: int,
        response_tokens: int,
    ) -> None:
        """Record and log a successful LLM call."""
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

    def _record_failure(
        self: Self,
        provider: str,
        duration_ms: int,
        rate_limit_delay_ms: int,
        retry_count: int,
        error_message: str | None,
    ) -> None:
        """Record and log a failed LLM call."""
        record = LLMCallRecord(
            provider=provider,
            model=self.config.model,
            duration_ms=duration_ms,
            rate_limit_delay_ms=rate_limit_delay_ms,
            retry_count=retry_count,
            status="failed",
            error_message=error_message,
        )
        self.call_records.append(record)
        logger.error("llm_call_failed", **record.to_dict())

    def _sleep_with_interrupt(self: Self, backoff: int, attempt: int) -> None:
        """Sleep, re-raising KeyboardInterrupt while logging the interruption."""
        try:
            time.sleep(backoff)
        except KeyboardInterrupt:
            logger.warning(
                "llm_retry_interrupted",
                completed_calls=len(self.rate_limiter.timestamps),
            )
            raise