from __future__ import annotations

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement
from specmetrics.plugins.publisher.otel_publisher import convert_measurements


class TestMetricConversion:
    def test_empty_measurements(self) -> None:
        metadata = ExportMetadata(run_id="test-run")
        metrics = convert_measurements([], metadata)
        assert len(metrics) == 2  # function_points.total (0) + functions.count (0)

    def test_single_measurement(self) -> None:
        metadata = ExportMetadata(run_id="test-run", specmetrics_version="0.1.0")
        measurements = [
            Measurement(
                function_id="proc-1",
                function_name="Process Order",
                category="EI",
                complexity="Average",
                functional_size=4.0,
            )
        ]
        metrics = convert_measurements(measurements, metadata)
        names = {m["name"] for m in metrics}
        assert "specmetrics.function_points.total" in names
        assert "specmetrics.functions.count" in names
        assert "specmetrics.functions.by_type" in names
        assert "specmetrics.functions.by_complexity" in names

    def test_function_points_sum(self) -> None:
        metadata = ExportMetadata(run_id="fp-test")
        measurements = [
            Measurement(
                function_id="a", function_name="A", category="EI", functional_size=4.0
            ),
            Measurement(
                function_id="b", function_name="B", category="EO", functional_size=5.0
            ),
            Measurement(
                function_id="c", function_name="C", category="EQ", functional_size=3.0
            ),
        ]
        metrics = convert_measurements(measurements, metadata)
        total_fp = next(
            m for m in metrics if m["name"] == "specmetrics.function_points.total"
        )
        assert total_fp["value"] == 12.0

    def test_resource_attributes(self) -> None:
        metadata = ExportMetadata(run_id="run-001", specmetrics_version="0.1.0")
        metrics = convert_measurements([], metadata)
        for m in metrics:
            attrs = m.get("attributes", {})
            assert attrs.get("run_id") == "run-001"
            assert attrs.get("service.name") == "specmetrics"

    def test_type_breakdown(self) -> None:
        metadata = ExportMetadata(run_id="type-test")
        measurements = [
            Measurement(function_id="a", function_name="A", category="EI"),
            Measurement(function_id="b", function_name="B", category="EI"),
            Measurement(function_id="c", function_name="C", category="EO"),
        ]
        metrics = convert_measurements(measurements, metadata)
        ei_metrics = [
            m
            for m in metrics
            if m["name"] == "specmetrics.functions.by_type"
            and m["attributes"].get("type") == "EI"
        ]
        assert len(ei_metrics) == 1
        assert ei_metrics[0]["value"] == 2
