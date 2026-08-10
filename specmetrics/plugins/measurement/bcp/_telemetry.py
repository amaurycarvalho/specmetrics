"""OpenTelemetry instrumentation for the BCP measurement plugin."""
from __future__ import annotations

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.bcp")
    _sdk_duration = _meter.create_histogram(
        name="bcp.sdk.execution.duration",
        description="Duration of BCP SDK execution per item",
        unit="ms",
    )
    _story_gauge = _meter.create_gauge(
        name="bcp.processed_stories",
        description="Number of stories processed",
    )
    _sdk_requests = _meter.create_counter(
        name="bcp.sdk.requests",
        description="Total SDK requests made",
    )
    _sdk_errors = _meter.create_counter(
        name="bcp.sdk.errors",
        description="Total SDK errors encountered",
    )
except Exception:
    _sdk_duration = None
    _story_gauge = None
    _sdk_requests = None
    _sdk_errors = None