"""LLM gateway for rate-limited, retrying batch completions."""

from __future__ import annotations

from typing import Any, Self

import structlog

from ._batch import BatchMixin
from ._completion import HAS_LITELLM
from ._config import LLMGatewayConfig
from ._gateway_complete import CompleteMixin
from ._models import (
    BatchRequest,
    DocumentPayload,
    LLMCallRecord,
    RateLimiter,
)
from ._parsing import parse_batch_response

logger = structlog.get_logger(__name__)


__all__ = [
    "HAS_LITELLM",
    "BatchRequest",
    "DocumentPayload",
    "LLMGateway",
    "LLMGatewayConfig",
    "RateLimiter",
    "litellm",  # noqa: F822  # lazily resolved via __getattr__
    "parse_batch_response",
]


def __getattr__(name: str) -> object:
    """Lazily resolve the ``litellm`` reference used by the gateway mixins.

    ``litellm`` is data exported so that tests can ``patch`` it on this module's
    namespace. It is imported lazily to avoid paying litellm's expensive import
    cost whenever this module is imported.
    """
    if name != "litellm":
        raise AttributeError(name)
    if not HAS_LITELLM:
        return None
    from ._completion import _load_litellm

    return _load_litellm()


class LLMGateway(CompleteMixin, BatchMixin):
    """Gateway issuing rate-limited, retrying LLM completion calls."""

    config: LLMGatewayConfig
    rate_limiter: RateLimiter
    call_records: list[LLMCallRecord]

    def __init__(self: Self, config: LLMGatewayConfig) -> None:
        """Initialize the gateway with its configuration and a rate limiter."""
        self.config = config
        self.rate_limiter = RateLimiter(config.rpm_limit)
        self.call_records: list[LLMCallRecord] = []

    def get_summary_stats(self: Self) -> dict[str, Any]:
        """Return aggregate statistics across all recorded LLM calls."""
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