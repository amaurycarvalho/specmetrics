"""Data models for the LLM gateway."""

from __future__ import annotations

import time
import uuid
from collections import deque
from threading import Lock
from typing import Any, Self

import structlog

logger = structlog.get_logger(__name__)

_EXTRA_CHARS_PER_DOC = 50


class LLMCallRecord:
    """Record of a single LLM call for observability."""

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
        self: Self,
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
        """Initialize the call record with metadata about the LLM call."""
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

    def to_dict(self: Self) -> dict[str, Any]:
        """Return the call record as a serializable dict."""
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
    """Rate limiter enforcing a requests-per-minute ceiling."""

    rpm_limit: int
    timestamps: deque[float]
    _lock: Lock

    def __init__(self: Self, rpm_limit: int) -> None:
        """Initialize the rate limiter with the given RPM limit."""
        self.rpm_limit = rpm_limit
        self.timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self: Self) -> float:
        """Return the delay in seconds before the next call, or zero if allowed."""
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

    def wait_and_record(self: Self) -> float:
        """Sleep until a slot is available, record the call, and return the delay."""
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
    """A single document submitted to the LLM for extraction."""

    document_id: str
    content: str
    document_type: str

    def __init__(self: Self, document_id: str, content: str, document_type: str) -> None:
        """Initialize the payload with a document's ID, content, and type."""
        self.document_id = document_id
        self.content = content
        self.document_type = document_type


class BatchRequest:
    """A request to extract structured data from multiple documents."""

    system_prompt: str
    documents: list[DocumentPayload]
    json_schema: dict[str, Any] | None

    def __init__(
        self: Self,
        system_prompt: str,
        documents: list[DocumentPayload],
        json_schema: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the batch request with its prompt, documents, and schema."""
        self.system_prompt = system_prompt
        self.documents = documents
        self.json_schema = json_schema

    def assemble_prompt(self: Self) -> str:
        """Assemble the user-facing prompt for this batch request."""
        parts: list[str] = []
        for doc in self.documents:
            parts.append(f'Document "{doc.document_id}": {doc.content}')
        doc_list = ", ".join(
            f'"{d.document_id}": {{"elements": [...]}}' for d in self.documents
        )
        parts.append(f"Respond with a JSON object keyed by document ID: {{{doc_list}}}")
        return "\n\n".join(parts)

    def _estimate_chars(self: Self) -> int:
        total = len(self.system_prompt)
        for doc in self.documents:
            total += len(doc.content) + len(doc.document_id) + _EXTRA_CHARS_PER_DOC
        return total

    def split(self: Self, max_chars: int) -> list[BatchRequest]:
        """Split the batch into sub-batches that each fit within max_chars."""
        if self._estimate_chars() <= max_chars:
            return [self]

        sub_batches: list[BatchRequest] = []
        current_docs: list[DocumentPayload] = []
        current_size = len(self.system_prompt)

        for doc in self.documents:
            doc_size = len(doc.content) + len(doc.document_id) + _EXTRA_CHARS_PER_DOC
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