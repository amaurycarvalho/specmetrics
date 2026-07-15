from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement


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
    def publisher_id(self) -> str:
        ...

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def publish(
        self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult:
        ...
