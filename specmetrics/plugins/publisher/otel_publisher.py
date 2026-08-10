"""OpenTelemetry publisher plugin backed by an in-process metric batcher."""

from __future__ import annotations

import time
from typing import Any, Self

import structlog

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement

from ._export import do_export
from ._metrics import convert_measurements
from .base import (
    PublisherConfig,
    PublisherConfiguration,
    PublisherPlugin,
    PublisherStatus,
    PublishResult,
)
from .batcher import MetricBatcher
from .exporter import create_otlp_exporter
from .retry import with_exponential_backoff

logger = structlog.get_logger(__name__)


class OTelPublisher(PublisherPlugin):
    """Publisher that exports metrics to OpenTelemetry backends."""

    def __init__(self: Self) -> None:
        """Initialize the publisher with no configured instances."""
        self._instances: list[PublisherInstance] = []
        self._initialized = False

    def publisher_id(self: Self) -> str:
        """Return the unique identifier for this publisher."""
        return "otel"

    def name(self: Self) -> str:
        """Return the display name of this publisher."""
        return "OpenTelemetry"

    def initialize(self: Self, configs: list[PublisherConfiguration]) -> None:
        """Build a publisher instance for each enabled configuration."""
        self._instances = []
        for cfg in configs:
            if not cfg.enabled:
                continue
            exporter = create_otlp_exporter(cfg)
            instance = PublisherInstance(cfg, exporter)
            self._instances.append(instance)
        self._initialized = True

    def start(self: Self) -> None:
        """Start all configured publisher instances."""
        if not self._initialized:
            logger.warning("publisher_not_initialized")
            return
        for inst in self._instances:
            inst.start()
        logger.info("publisher_started", endpoints=len(self._instances))

    def publish(
        self: Self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult:
        """Convert and enqueue the measurements to all publisher instances."""
        metrics = convert_measurements(measurements, metadata)
        if not self._instances:
            logger.warning("no_publisher_endpoints_configured")
            return PublishResult(
                success=True, message="No endpoints configured", metrics_count=0
            )

        total_enqueued = 0
        for metric in metrics:
            for inst in self._instances:
                inst.enqueue(metric)
                total_enqueued += 1

        return PublishResult(
            success=True,
            message=f"Enqueued {len(metrics)} metrics across {len(self._instances)} endpoints",
            metrics_count=len(metrics),
        )

    def stop(self: Self) -> None:
        """Stop all configured publisher instances."""
        for inst in self._instances:
            inst.stop()
        logger.info("publisher_stopped")

    def get_status(self: Self) -> list[PublisherStatus]:
        """Return the status of every configured publisher instance."""
        return [inst.get_status() for inst in self._instances]


class PublisherInstance:
    """Wraps a single exporter with its own batcher and status tracking."""

    def __init__(
        self: Self, config: PublisherConfiguration, exporter: object
    ) -> None:
        """Initialize the instance with its config and OTLP exporter."""
        self.config = config
        self.exporter = exporter
        self.batcher = MetricBatcher(config, self._export_batch)
        self._started_at: float = 0.0
        self._last_error: str | None = None

    def start(self: Self) -> None:
        """Start the metric batcher for this instance."""
        self._started_at = time.time()
        self.batcher.start()

    def stop(self: Self) -> None:
        """Stop the metric batcher for this instance."""
        self.batcher.stop()

    def enqueue(self: Self, metric: dict[str, Any]) -> None:
        """Enqueue a single metric into the batcher."""
        self.batcher.enqueue(metric)

    def get_status(self: Self) -> PublisherStatus:
        """Return the current publishing status for this instance."""
        batcher_status = self.batcher.get_status()
        uptime = time.time() - self._started_at if self._started_at else 0.0
        return PublisherStatus(
            endpoint_url=self.config.endpoint_url,
            total_metrics_published=batcher_status["total_exported"],
            consecutive_errors=batcher_status["consecutive_errors"],
            queue_depth=batcher_status["queue_depth"],
            last_error_message=batcher_status["last_error"],
            uptime_seconds=uptime,
        )

    def _export_batch(self: Self, batch: list[dict[str, Any]]) -> None:
        with_exponential_backoff(
            lambda: do_export(self.exporter, batch),
            self.config,
            context=f"otel:{self.config.endpoint_url}",
        )