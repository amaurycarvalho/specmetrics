from __future__ import annotations

import time
from typing import Any

import structlog

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement

from .base import (
    PublishResult,
    PublisherConfig,
    PublisherConfiguration,
    PublisherPlugin,
    PublisherStatus,
)
from .batcher import MetricBatcher
from .exporter import create_otlp_exporter
from .retry import with_exponential_backoff

logger = structlog.get_logger(__name__)


class OTelPublisher(PublisherPlugin):
    def __init__(self) -> None:
        self._instances: list[PublisherInstance] = []
        self._initialized = False

    def publisher_id(self) -> str:
        return "otel"

    def name(self) -> str:
        return "OpenTelemetry"

    def initialize(self, configs: list[PublisherConfiguration]) -> None:
        self._instances = []
        for cfg in configs:
            if not cfg.enabled:
                continue
            exporter = create_otlp_exporter(cfg)
            instance = PublisherInstance(cfg, exporter)
            self._instances.append(instance)
        self._initialized = True

    def start(self) -> None:
        if not self._initialized:
            logger.warning("publisher_not_initialized")
            return
        for inst in self._instances:
            inst.start()
        logger.info("publisher_started", endpoints=len(self._instances))

    def publish(
        self,
        measurements: list[Measurement],
        metadata: ExportMetadata,
        config: PublisherConfig,
    ) -> PublishResult:
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

    def stop(self) -> None:
        for inst in self._instances:
            inst.stop()
        logger.info("publisher_stopped")

    def get_status(self) -> list[PublisherStatus]:
        return [inst.get_status() for inst in self._instances]


class PublisherInstance:
    def __init__(self, config: PublisherConfiguration, exporter: Any) -> None:
        self.config = config
        self.exporter = exporter
        self.batcher = MetricBatcher(config, self._export_batch)
        self._started_at: float = 0.0
        self._last_error: str | None = None

    def start(self) -> None:
        self._started_at = time.time()
        self.batcher.start()

    def stop(self) -> None:
        self.batcher.stop()

    def enqueue(self, metric: dict[str, Any]) -> None:
        self.batcher.enqueue(metric)

    def get_status(self) -> PublisherStatus:
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

    def _export_batch(self, batch: list[dict[str, Any]]) -> None:
        with_exponential_backoff(
            lambda: self._do_export(batch),
            self.config,
            context=f"otel:{self.config.endpoint_url}",
        )

    def _do_export(self, batch: list[dict[str, Any]]) -> None:
        from opentelemetry.sdk.metrics.export import (
            MetricExporter,
            MetricExportResult,
            NumberDataPoint,
        )

        if not isinstance(self.exporter, MetricExporter):
            logger.warning(
                "exporter_not_metric_exporter",
                exporter_type=type(self.exporter).__name__,
            )
            return

        data_points: list[NumberDataPoint] = []
        for item in batch:
            try:
                dp = NumberDataPoint(
                    attributes=dict(item.get("attributes", {})),
                    start_time_unix_nano=int(time.time() * 1_000_000_000),
                    time_unix_nano=int(time.time() * 1_000_000_000),
                    value=item.get("value", 0),
                )
                data_points.append(dp)
            except Exception as exc:
                logger.warning("metric_skipped", name=item.get("name"), error=str(exc))

        if not data_points:
            return

        result = self.exporter.export(data_points)
        if result is None or result.status != MetricExportResult.SUCCESS:
            status_name = result.status.name if result else "unknown"
            raise ConnectionError(f"Export failed with status: {status_name}")


def _build_evidence_refs(measurements: list[Measurement]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for m in measurements:
        for ref in m.evidence:
            key = f"{ref.document_id}|{ref.section_id or ''}|{ref.graph_node_id or ''}"
            if key not in seen:
                seen.add(key)
                refs.append(
                    {
                        "spec_document": ref.document_id,
                        "spec_section": ref.section_id or "",
                        "spec_element_id": ref.graph_node_id or "",
                        "extracted_text": ref.text or "",
                    }
                )
    return refs


def convert_measurements(
    measurements: list[Measurement],
    metadata: ExportMetadata,
) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    evidence_refs = _build_evidence_refs(measurements)
    base_attrs = {
        "service.name": "specmetrics",
        "project_name": metadata.run_id or "unknown",
        "run_id": metadata.run_id or "",
        "specification_version": metadata.specmetrics_version or "",
    }

    total_fp = sum(m.functional_size for m in measurements)
    metrics.append(
        {
            "name": "specmetrics.function_points.total",
            "value": total_fp,
            "unit": "{function_points}",
            "description": "Total unadjusted function point count",
            "timestamp": time.time(),
            "attributes": {**base_attrs, "metric.type": "function_points_total"},
            "evidence_refs": evidence_refs,
        }
    )

    metrics.append(
        {
            "name": "specmetrics.functions.count",
            "value": len(measurements),
            "unit": "{functions}",
            "description": "Total number of identified functions",
            "timestamp": time.time(),
            "attributes": {**base_attrs, "metric.type": "functions_count"},
            "evidence_refs": evidence_refs,
        }
    )

    by_type: dict[str, int] = {}
    by_complexity: dict[str, int] = {}
    type_measurements: dict[str, list[Measurement]] = {}
    complexity_measurements: dict[str, list[Measurement]] = {}
    for m in measurements:
        cat = m.category or "unknown"
        by_type[cat] = by_type.get(cat, 0) + 1
        type_measurements.setdefault(cat, []).append(m)
        comp = m.complexity or "unknown"
        by_complexity[comp] = by_complexity.get(comp, 0) + 1
        complexity_measurements.setdefault(comp, []).append(m)

    for ftype, count in by_type.items():
        type_refs = _build_evidence_refs(type_measurements[ftype])
        metrics.append(
            {
                "name": "specmetrics.functions.by_type",
                "value": count,
                "unit": "{functions}",
                "description": f"Function count for type {ftype}",
                "timestamp": time.time(),
                "attributes": {
                    **base_attrs,
                    "type": ftype,
                    "metric.type": "functions_by_type",
                },
                "evidence_refs": type_refs,
            }
        )

    for comp, count in by_complexity.items():
        comp_refs = _build_evidence_refs(complexity_measurements[comp])
        metrics.append(
            {
                "name": "specmetrics.functions.by_complexity",
                "value": count,
                "unit": "{functions}",
                "description": f"Function count for complexity {comp}",
                "timestamp": time.time(),
                "attributes": {
                    **base_attrs,
                    "complexity": comp,
                    "metric.type": "functions_by_complexity",
                },
                "evidence_refs": comp_refs,
            }
        )

    return metrics
