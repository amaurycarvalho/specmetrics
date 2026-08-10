"""Internal OTLP export helpers for the publisher instance."""

from __future__ import annotations

import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def do_export(exporter: object, batch: list[dict[str, Any]]) -> None:
    """Export a batch of metrics through a MetricExporter."""
    from opentelemetry.sdk.metrics.export import (
        MetricExporter,
        MetricExportResult,
        NumberDataPoint,
    )

    if not isinstance(exporter, MetricExporter):
        logger.warning(
            "exporter_not_metric_exporter",
            exporter_type=type(exporter).__name__,
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

    result = exporter.export(data_points)
    if result is None or result.status != MetricExportResult.SUCCESS:
        status_name = result.status.name if result else "unknown"
        raise ConnectionError(f"Export failed with status: {status_name}")