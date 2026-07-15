from __future__ import annotations


import structlog

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement

from .base import PublishResult, PublisherConfig, PublisherPlugin

logger = structlog.get_logger(__name__)


class OTelPublisher(PublisherPlugin):
    def publisher_id(self) -> str:
        return "otel"

    def name(self) -> str:
        return "OpenTelemetry"

    def publish(
        self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult:
        try:
            from opentelemetry import metrics
            from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
                OTLPMetricExporter,
            )
            from opentelemetry.sdk.metrics import MeterProvider
            from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
            from opentelemetry.sdk.resources import Resource

            resource = Resource.create({"service.name": "specmetrics"})
            exporter = OTLPMetricExporter(endpoint=config.endpoint_url)
            reader = PeriodicExportingMetricReader(exporter)
            provider = MeterProvider(resource=resource, metric_readers=[reader])
            metrics.set_meter_provider(provider)

            meter = metrics.get_meter("specmetrics", metadata.specmetrics_version or "0.1.0")

            function_counter = meter.create_counter(
                name="specmetrics.functions.total",
                description="Total number of measured functions",
                unit="1",
            )
            function_counter.add(metadata.function_count)

            if measurements:
                complexity_counter = meter.create_counter(
                    name="specmetrics.functions.by_complexity",
                    description="Functions grouped by complexity",
                    unit="1",
                )
                for m in measurements:
                    attrs = {"complexity": m.complexity or "unknown", "category": m.category or "unknown"}
                    complexity_counter.add(1, attributes=attrs)

            provider.force_flush()
            provider.shutdown()

            return PublishResult(
                success=True,
                message=f"Published {metadata.function_count} functions",
                metrics_count=2,
            )
        except Exception as exc:
            logger.warning("otel_publish_failed", error=str(exc))
            return PublishResult(
                success=False,
                message=f"Publishing failed: {exc}",
                metrics_count=0,
            )
