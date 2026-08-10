from __future__ import annotations

from specmetrics.application.models import (
    MeasurementResult,
    MetricOutputItem,
    PipelineResult,
)
from specmetrics.cli import _breakdowns


def _result(measurement=None, raw=None) -> PipelineResult:
    r = PipelineResult(status=None, measurement=measurement)
    r.measurement_result_raw = raw or {}
    return r


class TestMetricBreakdownLines:
    def test_cognitive_dispatch(self):
        result = _result(
            None, {"cognitive_bloom_breakdown": {"remember": {"total": 3.0}}}
        )
        lines = _breakdowns.metric_breakdown_lines(result, MetricOutputItem(name="cognitive_points"))
        assert lines == ["    Remember: 3.0"]

    def test_tshirt_dispatch(self):
        result = _result(None, {"tshirt_breakdown": {"M": {"count": 2}}})
        lines = _breakdowns.metric_breakdown_lines(result, MetricOutputItem(name="tshirt"))
        assert lines == ["    M: 2"]

    def test_function_points_dispatch(self):
        measurement = MeasurementResult(breakdown={"ILF": {"count": 3, "total_ufp": 30}})
        result = _result(measurement)
        lines = _breakdowns.metric_breakdown_lines(result, MetricOutputItem(name="function_points"))
        assert lines == ["    ├─ ILF: count=3, subtot=30"]

    def test_unknown_metric_returns_empty(self):
        result = _result(None, {})
        assert (
            _breakdowns.metric_breakdown_lines(result, MetricOutputItem(name="other"))
            == []
        )


class TestCognitiveBloomLines:
    def test_no_raw_returns_empty(self):
        assert _breakdowns.cognitive_bloom_lines(_result(raw=None)) == []

    def test_non_dict_breakdown_returns_empty(self):
        assert _breakdowns.cognitive_bloom_lines(_result(None, {"cognitive_bloom_breakdown": None})) == []

    def test_empty_dict_returns_empty(self):
        assert _breakdowns.cognitive_bloom_lines(_result(None, {"cognitive_bloom_breakdown": {}})) == []

    def test_valid_breakdown(self):
        result = _result(
            None,
            {"cognitive_bloom_breakdown": {"apply": {"total": 4.0}, "analyze": {"total": 1.5}}},
        )
        lines = _breakdowns.cognitive_bloom_lines(result)
        assert len(lines) == 2
        assert any("Apply: 4.0" in l for l in lines)
        assert any("Analyze: 1.5" in l for l in lines)


class TestTshirtLines:
    def test_no_raw_returns_empty(self):
        assert _breakdowns.tshirt_lines(_result(raw=None)) == []

    def test_non_dict_breakdown(self):
        assert _breakdowns.tshirt_lines(_result(None, {"tshirt_breakdown": "nope"})) == []

    def test_dict_with_objects(self):
        result = _result(None, {"tshirt_breakdown": {"M": {"count": 2}, "S": {"count": 3}}})
        lines = _breakdowns.tshirt_lines(result)
        assert lines == ["    M: 2  S: 3"]

    def test_empty_dict_returns_empty(self):
        assert _breakdowns.tshirt_lines(_result(None, {"tshirt_breakdown": {}})) == []


class TestFunctionPointsLines:
    def test_no_measurement(self):
        assert _breakdowns.function_points_lines(_result(None)) == []

    def test_no_breakdown(self):
        assert _breakdowns.function_points_lines(_result(MeasurementResult())) == []

    def test_with_breakdown(self):
        measurement = MeasurementResult(
            breakdown={"ILF": {"count": 3, "total_ufp": 30}, "EIF": {"count": 1, "total_ufp": 7}}
        )
        lines = _breakdowns.function_points_lines(_result(measurement))
        assert len(lines) == 2
        assert "EIF" in lines[0]
        assert "count=1" in lines[0]
        assert "ILF" in lines[1]

    def test_scalar_breakdown_values(self):
        measurement = MeasurementResult(breakdown={"REQ": 5})
        lines = _breakdowns.function_points_lines(_result(measurement))
        assert lines == ["    ├─ REQ: count=5, subtot=5"]


class TestBreakdownTotal:
    def test_dict(self):
        assert _breakdowns.breakdown_total({"total": 2.0}) == 2.0

    def test_dict_missing_total(self):
        assert _breakdowns.breakdown_total({"x": 1}) == 0

    def test_scalar(self):
        assert _breakdowns.breakdown_total("4") == 4.0