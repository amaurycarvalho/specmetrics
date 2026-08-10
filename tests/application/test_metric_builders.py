from __future__ import annotations

from unittest.mock import MagicMock

from specmetrics.application.metric_builders import (
    _build_metric_results,
    _extract_measurement,
)
from specmetrics.application.models import MeasurementResult


def _ctx(measurement_result) -> MagicMock:
    ctx = MagicMock()
    ctx.measurement_result = measurement_result
    return ctx


class TestBuildMetricResults:
    def test_known_metric_uses_mapped_json_name(self) -> None:
        ctx = _ctx({"fpa_total_function_points": 42})
        results = _build_metric_results(ctx, metrics_filter=["fpa"])
        assert results[0].name == "function_points"

    def test_unknown_metric_id_passthrough_as_name(self) -> None:
        ctx = _ctx({})
        results = _build_metric_results(ctx, metrics_filter=["custom_metric"])
        assert len(results) == 1
        assert results[0].name == "custom_metric"

    def test_missing_total_defaults_to_zero(self) -> None:
        ctx = _ctx({})
        results = _build_metric_results(ctx, metrics_filter=["fpa"])
        assert results[0].total == 0

    def test_total_read_from_measurement_result(self) -> None:
        ctx = _ctx({"fpa_total_function_points": 42})
        results = _build_metric_results(ctx, metrics_filter=["fpa"])
        assert results[0].total == 42

    def test_status_and_duration_defaults(self) -> None:
        ctx = _ctx({})
        results = _build_metric_results(ctx, metrics_filter=["fpa"])
        assert results[0].status == "completed"
        assert results[0].duration_ms == 0

    def test_returns_empty_for_non_dict_result(self) -> None:
        ctx = _ctx(None)
        assert _build_metric_results(ctx, metrics_filter=["fpa"]) == []


class TestExtractMeasurement:
    def test_returns_none_when_result_is_none(self) -> None:
        assert _extract_measurement(_ctx(None)) is None

    def test_dict_result_populates_measurement(self) -> None:
        ctx = _ctx(
            {
                "fpa_total_function_points": 42,
                "fpa_breakdown": {"ILF": 3},
                "fpa_complexity_distribution": [{"Low": 2}],
                "evidence_refs": ["ref-1"],
                "storypoints_applied_rule_pack": "default-v1",
            }
        )
        result = _extract_measurement(ctx)
        assert isinstance(result, MeasurementResult)
        assert result.total_function_points == 42
        assert result.breakdown == {"ILF": 3}
        assert result.complexity_distribution == [{"Low": 2}]
        assert result.evidence_refs == ["ref-1"]
        assert result.applied_rule_pack == "default-v1"

    def test_non_dict_result_returns_empty_measurement(self) -> None:
        result = _extract_measurement(_ctx("not-a-dict"))
        assert isinstance(result, MeasurementResult)
        assert result.total_function_points == 0
        assert result.breakdown == {}
