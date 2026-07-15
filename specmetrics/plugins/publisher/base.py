from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement


class PublisherConfigError(Exception):
    pass


class Protocol(str, Enum):
    GRPC = "grpc"
    HTTP = "http"


class ConnectionState(str, Enum):
    INITIALIZED = "initialized"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class PublisherConfiguration(BaseModel):
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
    def _validate_retry_delay(cls, v, info):
        base = info.data.get("retry_base_delay_seconds", 1.0)
        if v < base:
            raise ValueError(
                "retry_max_delay_seconds must be >= retry_base_delay_seconds"
            )
        return v

    @field_validator("endpoint_url")
    @classmethod
    def _validate_endpoint_url(cls, v):
        if v and not v.startswith(("http://", "https://", "grpc://")):
            raise ValueError(
                "endpoint_url must start with http://, https://, or grpc://"
            )
        return v


class PublisherStatus(BaseModel):
    endpoint_url: str = ""
    connection_state: ConnectionState = ConnectionState.INITIALIZED
    last_successful_publish_at: datetime | None = None
    total_metrics_published: int = 0
    consecutive_errors: int = 0
    queue_depth: int = 0
    last_error_message: str | None = None
    uptime_seconds: float = 0.0


class PublishResult(BaseModel):
    success: bool
    message: str = ""
    metrics_count: int = 0


class PublisherConfig(BaseModel):
    endpoint_url: str = ""
    auth_credentials: dict | None = None
    publishing_interval: int = 30


class PublisherPlugin(ABC):
    @abstractmethod
    def publisher_id(self) -> str: ...

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def publish(
        self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult: ...

    def get_status(self) -> PublisherStatus:
        return PublisherStatus()
