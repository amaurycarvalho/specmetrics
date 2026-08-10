"""OpenTelemetry instrumentation for the T-Shirt sizing plugin."""
from __future__ import annotations

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.tshirt")
    _classify_duration = _meter.create_histogram(
        name="tshirt.classification.duration",
        description="Duration of T-Shirt classification execution",
        unit="ms",
    )
    _item_gauge = _meter.create_gauge(
        name="tshirt.classified_items",
        description="Number of Functional Processes classified",
    )
    _distribution_histogram = _meter.create_histogram(
        name="tshirt.distribution",
        description="Distribution of T-Shirt sizes",
        unit="1",
    )
except Exception:
    _classify_duration = None
    _item_gauge = None
    _distribution_histogram = None