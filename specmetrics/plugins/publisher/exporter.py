"""Factory functions for OpenTelemetry metric exporters."""

from __future__ import annotations

from typing import Any

import structlog

from .base import Protocol, PublisherConfiguration

logger = structlog.get_logger(__name__)


def create_otlp_exporter(config: PublisherConfiguration) -> object:
    """Create an OTLP metric exporter matching the configured protocol."""
    if config.protocol == Protocol.GRPC:
        return _create_grpc_exporter(config)
    return _create_http_exporter(config)


def _create_grpc_exporter(config: PublisherConfiguration) -> object:
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter,
    )

    kwargs: dict[str, Any] = {
        "endpoint": config.endpoint_url,
        "timeout": config.timeout_seconds,
    }

    if config.api_key:
        kwargs["headers"] = {"Authorization": f"Bearer {config.api_key}"}

    if not config.tls_enabled:
        kwargs["insecure"] = True
    elif not config.tls_verify and config.tls_ca_cert_path:
        import grpc

        with open(config.tls_ca_cert_path, "rb") as fh:
            root_certificates = fh.read()
        ssl_creds = grpc.ssl_channel_credentials(root_certificates=root_certificates)
        kwargs["credentials"] = ssl_creds

    return OTLPMetricExporter(**kwargs)


def _create_http_exporter(config: PublisherConfiguration) -> object:
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter,
    )

    kwargs: dict[str, Any] = {
        "endpoint": config.endpoint_url,
        "timeout": config.timeout_seconds,
    }

    if config.api_key:
        kwargs["headers"] = {"Authorization": f"Bearer {config.api_key}"}

    return OTLPMetricExporter(**kwargs)
