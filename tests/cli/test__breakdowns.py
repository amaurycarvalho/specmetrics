from __future__ import annotations

from specmetrics.application.enums import PipelineStatus
from specmetrics.application.models import MeasurementResult, PipelineResult
from specmetrics.cli._breakdowns import (
    cognitive_bloom_lines,
    function_points_lines,
    metric_breakdown_lines,
    tshirt_lines,
)


def _result(measurement_result_raw=None, measurement=None) -> PipelineResult:
    return PipelineResult(
        status=PipelineStatus.SUCCESS,
        measurement=measurement,
        measurement_result_raw=measurement_result_raw or {},
    )


class TestCognitiveBloomLines:
    def test_empty_raw_returns_no_lines(self):
        """Targets cognitive_bloom_lines__mutmut_6 early return for empty raw."""
        assert cognitive_bloom_lines(_result()) == []

    def test_non_mapping_breakdown_returns_no_lines(self):
        """Kills cognitive_bloom_lines__mutmut_6 (or -> and) via a falsy non-dict."""
        result = _result(measurement_result_raw={"cognitive_bloom_breakdown": 0})
        assert cognitive_bloom_lines(result) == []

    def test_dict_breakdown_renders_level_lines(self):
        """Targets cognitive_bloom_lines__mutmut_6 dict-breakdown rendering."""
        result = _result(
            measurement_result_raw={
                "cognitive_bloom_breakdown": {"create": {"total": 3.0}}
            }
        )
        assert cognitive_bloom_lines(result) == ["    Create: 3.0"]

    def test_dispatch_for_cognitive_points(self):
        """Targets metric_breakdown_lines dispatch for cognitive_points (guards cognitive_bloom_lines__mutmut_6)."""
        from specmetrics.application.models import MetricOutputItem

        result = _result(
            measurement_result_raw={
                "cognitive_bloom_breakdown": {"analyze": {"total": 1.5}}
            }
        )
        lines = metric_breakdown_lines(result, MetricOutputItem(name="cognitive_points"))
        assert lines == ["    Analyze: 1.5"]

    def test_dispatch_unknown_metric_returns_empty(self):
        """Targets metric_breakdown_lines fallthrough (guards cognitive_bloom_lines__mutmut_6/tshirt_lines__mutmut_9)."""
        from specmetrics.application.models import MetricOutputItem

        assert metric_breakdown_lines(_result(), MetricOutputItem(name="other")) == []


class TestTshirtLines:
    def test_size_with_count_renders_count(self):
        """Kills tshirt_lines__mutmut_9/11 (count default replaced with None)."""
        result = _result(
            measurement_result_raw={"tshirt_breakdown": {"M": {"count": 5}}}
        )
        assert tshirt_lines(result) == ["    M: 5"]

    def test_size_without_count_falls_back_to_info(self):
        """Kills tshirt_lines__mutmut_9/11 via a missing 'count' key."""
        result = _result(
            measurement_result_raw={"tshirt_breakdown": {"L": {"sizes": 2}}}
        )
        assert tshirt_lines(result) == ["    L: {'sizes': 2}"]

    def test_empty_breakdown_returns_no_lines(self):
        """Targets tshirt_lines__mutmut_9/11 early return for empty raw."""
        assert tshirt_lines(_result()) == []


class TestFunctionPointsLines:
    def test_dict_info_without_count_and_ufp_defaults_to_zero(self):
        """Kills function_points_lines__mutmut_8/10/13/16/18/21 (defaults -> None/1)."""
        result = _result(
            measurement=MeasurementResult(
                breakdown={"data_group": {"fname": "users"}}
            )
        )
        assert function_points_lines(result) == [
            "    \u251c\u2500 data_group: count=0, subtot=0"
        ]

    def test_dict_info_with_values_renders_them(self):
        """Targets function_points_lines__mutmut_8/10/13/16/18/21 value rendering."""
        result = _result(
            measurement=MeasurementResult(
                breakdown={"data_group": {"count": 3, "total_ufp": 7}}
            )
        )
        assert function_points_lines(result) == [
            "    \u251c\u2500 data_group: count=3, subtot=7"
        ]

    def test_plain_int_info_used_for_both(self):
        """Targets function_points_lines__mutmut_8/10/13/16/18/21 non-dict branch."""
        result = _result(measurement=MeasurementResult(breakdown={"data": 4}))
        assert function_points_lines(result) == [
            "    \u251c\u2500 data: count=4, subtot=4"
        ]

    def test_dispatch_for_function_points(self):
        """Targets metric_breakdown_lines dispatch for function_points (guards function_points_lines__mutmut_8/16)."""
        from specmetrics.application.models import MetricOutputItem

        result = _result(
            measurement=MeasurementResult(breakdown={"data": {"count": 2}})
        )
        lines = metric_breakdown_lines(
            result, MetricOutputItem(name="function_points")
        )
        assert lines == ["    \u251c\u2500 data: count=2, subtot=0"]
