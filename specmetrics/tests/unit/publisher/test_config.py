from __future__ import annotations

import pytest
from pydantic import ValidationError

from specmetrics.plugins.publisher.base import PublisherConfiguration


class TestPublisherConfiguration:
    def test_default_config(self) -> None:
        cfg = PublisherConfiguration(endpoint_url="http://localhost:4318")
        assert cfg.protocol.value == "grpc"
        assert cfg.timeout_seconds == 10
        assert cfg.batch_interval_seconds == 5
        assert cfg.enabled is True

    def test_minimal_valid_config(self) -> None:
        cfg = PublisherConfiguration(endpoint_url="grpc://otlp.example.com:4317")
        assert cfg.endpoint_url == "grpc://otlp.example.com:4317"

    def test_invalid_endpoint_url(self) -> None:
        with pytest.raises(ValidationError):
            PublisherConfiguration(endpoint_url="ftp://bad-scheme.com:4318")

    def test_invalid_retry_delay(self) -> None:
        with pytest.raises(ValidationError):
            PublisherConfiguration(
                endpoint_url="http://localhost:4318",
                retry_base_delay_seconds=10.0,
                retry_max_delay_seconds=5.0,
            )

    def test_negative_timeout(self) -> None:
        with pytest.raises(ValidationError):
            PublisherConfiguration(
                endpoint_url="http://localhost:4318", timeout_seconds=0
            )

    def test_zero_batch_size(self) -> None:
        with pytest.raises(ValidationError):
            PublisherConfiguration(
                endpoint_url="http://localhost:4318", batch_max_size=0
            )

    def test_api_key_config(self) -> None:
        cfg = PublisherConfiguration(
            endpoint_url="https://otlp.example.com",
            api_key="sk-secret-key",
            protocol="http",
        )
        assert cfg.api_key == "sk-secret-key"
        assert cfg.protocol.value == "http"

    def test_disabled_config(self) -> None:
        cfg = PublisherConfiguration(
            endpoint_url="http://localhost:4318",
            enabled=False,
        )
        assert cfg.enabled is False
