from __future__ import annotations

import pytest

from specmetrics.plugins.publisher.base import PublisherConfiguration
from specmetrics.plugins.publisher.retry import with_exponential_backoff


class TestRetry:
    def test_success_on_first_attempt(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            retry_max_attempts=3,
        )
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            return "ok"

        result = with_exponential_backoff(fn, config)
        assert result == "ok"
        assert call_count == 1

    def test_retry_on_failure(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            retry_max_attempts=3,
            retry_base_delay_seconds=0.1,
        )
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("transient error")
            return "ok"

        result = with_exponential_backoff(fn, config)
        assert result == "ok"
        assert call_count == 3

    def test_max_retries_exceeded(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            retry_max_attempts=2,
            retry_base_delay_seconds=0.1,
        )
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionError("persistent error")

        with pytest.raises(ConnectionError):
            with_exponential_backoff(fn, config)
        assert call_count == 2

    def test_zero_retries(self) -> None:
        config = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            retry_max_attempts=0,
        )
        call_count = 0

        def fn() -> str:
            nonlocal call_count
            call_count += 1
            raise ConnectionError("no retry")

        with pytest.raises(RuntimeError):
            with_exponential_backoff(fn, config)
        assert call_count == 0
