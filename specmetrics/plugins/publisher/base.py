"""Base classes, models, and shared types for publisher plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement


class PublisherConfigError(Exception):
    """Raised when publisher configuration data is invalid."""


class Protocol(str, Enum):
    """Transport protocol used when publishing metrics."""

    GRPC = "grpc"
    HTTP = "http"


class ConnectionState(str, Enum):
    """Lifecycle state of a publisher connection."""

    INITIALIZED = "initialized"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class PublisherConfiguration(BaseModel):
    """Runtime configuration for a single publisher endpoint."""

    endpoint_url: str = ""
    protocol: Protocol = Protocol.GRPC
    api_key: str | None = None
    tls_enabled: bool = True
    tls_verify: bool = True
    tls_ca_cert_path: str | None = None
    timeout_seconds: int = Field(default=10, ge=1)
    batch_interval_seconds: int = Field(default=5, ge=1)
    batch_max_size: int = Field(default=100, ge=1)
    queue_max_size: int = Field(default=4096, ge=1)
    retry_max_attempts: int = Field(default=3, ge=0)
    retry_base_delay_seconds: float = Field(default=1.0, ge=0.1)
    retry_max_delay_seconds: float = Field(default=30.0, ge=0.1)
    enabled: bool = True

    @field_validator("retry_max_delay_seconds")
    @classmethod
    def _validate_retry_delay(
        cls: type[Self], v: float, info: ValidationInfo
    ) -> float:
        base = info.data.get("retry_base_delay_seconds", 1.0)
        if v < base:
            raise ValueError(
                "retry_max_delay_seconds must be >= retry_base_delay_seconds"
            )
        return v

    @field_validator("endpoint_url")
    @classmethod
    def _validate_endpoint_url(cls: type[Self], v: str) -> str:
        if v and not v.startswith(("http://", "https://", "grpc://")):
            raise ValueError(
                "endpoint_url must start with http://, https://, or grpc://"
            )
        return v


class PublisherStatus(BaseModel):
    """Snapshot of a publisher instance's current runtime status."""

    endpoint_url: str = ""
    connection_state: ConnectionState = ConnectionState.INITIALIZED
    last_successful_publish_at: datetime | None = None
    total_metrics_published: int = 0
    consecutive_errors: int = 0
    queue_depth: int = 0
    last_error_message: str | None = None
    uptime_seconds: float = 0.0


class PublishResult(BaseModel):
    """Outcome of a single publish attempt."""

    success: bool
    message: str = ""
    metrics_count: int = 0


class PublisherConfig(BaseModel):
    """Per-publisher configuration used during a pipeline run."""

    endpoint_url: str = ""
    auth_credentials: dict | None = None
    publishing_interval: int = 30


class PublisherPlugin(ABC):
    """Base class that all publisher plugins must implement."""

    @abstractmethod
    def publisher_id(self: Self) -> str:
        """Return the unique identifier for this publisher."""
        ...

    @abstractmethod
    def name(self: Self) -> str:
        """Return the display name of this publisher."""
        ...

    @abstractmethod
    def publish(
        self: Self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult:
        """Publish the given measurements with the provided metadata."""
        ...

    def get_status(self: Self) -> PublisherStatus:
        """Return the current status of the publisher."""
        return PublisherStatus()
