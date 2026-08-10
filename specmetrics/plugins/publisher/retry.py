"""Retry helper with exponential backoff for publisher batch exports."""

from __future__ import annotations

import time
from collections.abc import Callable

import structlog

from .base import PublisherConfiguration

logger = structlog.get_logger(__name__)


def with_exponential_backoff(
    fn: Callable[[], object],
    config: PublisherConfiguration,
    context: str = "",
) -> object:
    """Call ``fn`` with exponential backoff up to the configured attempt limit."""
    if config.retry_max_attempts <= 0:
        return fn()

    last_exc: Exception | None = None
    for attempt in range(1, config.retry_max_attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < config.retry_max_attempts:
                delay = min(
                    config.retry_base_delay_seconds * (2 ** (attempt - 1)),
                    config.retry_max_delay_seconds,
                )
                logger.info(
                    "retrying",
                    attempt=attempt,
                    delay=delay,
                    context=context,
                    error=str(exc),
                )
                time.sleep(delay)

    if last_exc:
        logger.error("max_retries_exceeded", context=context, error=str(last_exc))
        raise last_exc

    raise RuntimeError(
        f"Unexpected: retry loop completed without result or exception for {context}"
    )
