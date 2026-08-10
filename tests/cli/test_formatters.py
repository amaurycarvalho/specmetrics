from __future__ import annotations

import json
from pathlib import Path

from specmetrics.application.enums import (
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from specmetrics.application.models import MetricOutputItem, PipelineResult, StageResult
from specmetrics.cli.formatters import (
    _header_lines,
    _metric_header_line,
    _results_lines,
    _stage_line,
    _status_icon,
    format_json_result,
    format_progress,
)
from specmetrics.cli.formatters import (
    format_text_result as format_result,
)


class TestFormatResult:
    def test_format_success(self):
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            stages_executed=[
                StageResult(stage=StageName.MEASURE, status="completed"),
            ],
        )
        text = format_result(result)
        assert "Measurement Complete" in text

    def test_format_with_measurement(self):
        from specmetrics.application.models import MeasurementResult

        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            measurement=MeasurementResult(total_function_points=42),
        )
        text = format_result(result)
        assert "42" in text or "function" in text


class TestHeaderLines:
    def test_rule_line_is_exactly_48_rule_chars(self):
        """Kills _header_lines__mutmut_5/6 (48 rule chars -> prefixed or 49)."""
        result = PipelineResult(status=PipelineStatus.SUCCESS)
        lines = _header_lines(result)
        assert "\u2500" * 48 in lines
        assert any(len(line) == 48 and line == "\u2500" * 48 for line in lines)

    def test_header_ends_with_blank_line(self):
        """Kills _header_lines__mutmut_11 (blank line -> XXXX)."""
        result = PipelineResult(status=PipelineStatus.SUCCESS)
        lines = _header_lines(result)
        assert lines[-1] == ""

    def test_project_path_line_rendered_when_set(self):
        """Kills _header_lines__mutmut_7 (Project line -> None)."""
        result = PipelineResult(
            status=PipelineStatus.SUCCESS, project_path=Path("/proj")
        )
        lines = _header_lines(result)
        assert "Project: /proj" in lines

    def test_project_path_line_omitted_when_missing(self):
        """Targets _header_lines__mutmut_7 project_path conditional."""
        result = PipelineResult(status=PipelineStatus.SUCCESS)
        lines = _header_lines(result)
        assert all("Project:" not in line for line in lines)


class TestResultsLines:
    def test_results_header_with_metric_results(self):
        """Kills _results_lines__mutmut_3/4/5/19/20/21 (Results: literal)."""
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            metric_results=[MetricOutputItem(name="function_points", total=10)],
        )
        lines = _results_lines(result)
        assert "Results:" in lines

    def test_metric_header_line_included(self):
        """Kills _results_lines__mutmut_7 (metric header -> None result arg)."""
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            metric_results=[MetricOutputItem(name="function_points", total=10)],
        )
        lines = _results_lines(result)
        assert any("Function Points: 10" in line for line in lines)

    def test_measurement_fallback_breakdown_line(self):
        """Kills _results_lines__mutmut_24 (breakdown line -> None)."""
        from specmetrics.application.models import MeasurementResult

        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            measurement=MeasurementResult(
                total_function_points=5, breakdown={"data": 2}
            ),
        )
        lines = _results_lines(result)
        assert "  \u251c\u2500 data: 2" in lines

    def test_stages_header_always_rendered(self):
        """Kills _results_lines__mutmut_28/29/30 (Stages: literal)."""
        result = PipelineResult(status=PipelineStatus.SUCCESS)
        lines = _results_lines(result)
        assert "Stages:" in lines

    def test_stage_line_included(self):
        """Kills _results_lines__mutmut_32 (stage line -> None result arg)."""
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            stages_executed=[
                StageResult(
                    stage=StageName.MEASURE,
                    status=StageExecutionStatus.COMPLETED,
                    entities_found=2,
                    duration_seconds=1.0,
                )
            ],
        )
        lines = _results_lines(result)
        assert any("measure" in line for line in lines)


class TestStageLine:
    def _result(self, **kwargs) -> PipelineResult:
        return PipelineResult(status=PipelineStatus.SUCCESS, **kwargs)

    def test_discover_shows_framework_and_documents(self):
        """Kills _stage_line__mutmut_3/4/5/6/7/8/9/10/11/12/13/14 (discover extras)."""
        result = self._result(_framework_detected="django")
        sr = StageResult(
            stage=StageName.DISCOVER,
            status=StageExecutionStatus.COMPLETED,
            entities_found=3,
            duration_seconds=1.5,
        )
        line = _stage_line(result, sr)
        assert "[django]" in line
        assert "(3 documents)" in line

    def test_discover_without_framework_no_bracket(self):
        """Targets _stage_line__mutmut_6/7/8/9/10/11/12/13/14 framework None handling."""
        result = self._result()
        sr = StageResult(
            stage=StageName.DISCOVER,
            status=StageExecutionStatus.COMPLETED,
            entities_found=3,
        )
        line = _stage_line(result, sr)
        assert "[" not in line
        assert "(3 documents)" in line

    def test_discover_zero_entities_no_extra(self):
        """Kills _stage_line__mutmut_15/16 (entities_found > 0 boundary)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.DISCOVER,
            status=StageExecutionStatus.COMPLETED,
            entities_found=0,
        )
        line = _stage_line(result, sr)
        assert "(0 documents)" not in line
        assert line.endswith(")")

    def test_measure_stage_label_metrics(self):
        """Kills _stage_line__mutmut_21/22/23/24/25/26/29 (measure label)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.MEASURE,
            status=StageExecutionStatus.COMPLETED,
            entities_found=2,
        )
        line = _stage_line(result, sr)
        assert "(2 metrics)" in line
        assert "items" not in line

    def test_non_measure_stage_label_items(self):
        """Kills _stage_line__mutmut_27/28 (items label)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.EXTRACT,
            status=StageExecutionStatus.COMPLETED,
            entities_found=2,
        )
        line = _stage_line(result, sr)
        assert "(2 items)" in line

    def test_non_discover_zero_entities_no_extra(self):
        """Kills _stage_line__mutmut_19/20 (elif entities_found boundary)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.EXTRACT,
            status=StageExecutionStatus.COMPLETED,
            entities_found=0,
        )
        line = _stage_line(result, sr)
        assert "(0 items)" not in line
        assert line.endswith(")")

    def test_stage_line_uses_status_icon(self):
        """Kills _stage_line__mutmut_30 (status icon -> None)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.MEASURE,
            status=StageExecutionStatus.FAILED,
            entities_found=0,
        )
        line = _stage_line(result, sr)
        assert "\u2717" in line

    def test_extra_default_is_empty(self):
        """Kills _stage_line__mutmut_1/2 (extra = '' -> None/XXXX)."""
        result = self._result()
        sr = StageResult(
            stage=StageName.MEASURE,
            status=StageExecutionStatus.COMPLETED,
            entities_found=0,
        )
        line = _stage_line(result, sr)
        assert "XXXX" not in line
        assert "None" not in line
        assert line.endswith(")")


class TestMetricHeaderLine:
    def _result(self, **kwargs) -> PipelineResult:
        return PipelineResult(status=PipelineStatus.SUCCESS, **kwargs)

    def test_display_name_mapping_applied(self):
        """Kills _metric_header_line__mutmut_3/4/5 (display name fallback)."""
        line = _metric_header_line(
            self._result(), MetricOutputItem(name="function_points", total=10)
        )
        assert "Function Points: 10" in line

    def test_unknown_name_uses_raw_name(self):
        """Targets _metric_header_line__mutmut_3/4/5 unknown-name fallback."""
        line = _metric_header_line(
            self._result(), MetricOutputItem(name="mystery", total=10)
        )
        assert "mystery: 10" in line

    def test_skipped_status_tag(self):
        """Kills _metric_header_line__mutmut_8/9/10/11/12/13 (skipped tag)."""
        line = _metric_header_line(
            self._result(),
            MetricOutputItem(name="mystery", total=10, status="skipped"),
        )
        assert " (skipped)" in line

    def test_failed_status_tag(self):
        """Kills _metric_header_line__mutmut_14/15/16/17/18/19 (failed tag)."""
        line = _metric_header_line(
            self._result(),
            MetricOutputItem(name="mystery", total=10, status="failed"),
        )
        assert " (failed)" in line

    def test_completed_status_no_tag(self):
        """Targets _metric_header_line__mutmut_8/9/10/14/15/16 default status."""
        line = _metric_header_line(
            self._result(),
            MetricOutputItem(name="mystery", total=10, status="completed"),
        )
        assert "(skipped)" not in line
        assert "(failed)" not in line

    def test_tshirt_uses_entities_label(self):
        """Kills _metric_header_line__mutmut_20/21/22 (tshirt branch)."""
        line = _metric_header_line(
            self._result(), MetricOutputItem(name="tshirt", total=5)
        )
        assert "TShirt: 5 entities" in line

    def test_bcp_with_warnings_adds_sdk_tag(self):
        """Kills _metric_header_line__mutmut_25/26/27/28/29/30/31/32/33/34/35/36/37/38/39 (bcp sdk tag)."""
        result = self._result(measurement_result_raw={"bcp_warnings": ["w1"]})
        line = _metric_header_line(
            result, MetricOutputItem(name="business_complexity_points", total=10)
        )
        assert "Business Complexity Points: 10 (SDK is missing)" in line

    def test_bcp_without_warnings_no_sdk_tag(self):
        """Targets _metric_header_line__mutmut_29/30/31/32/33/34/35 bcp empty-warnings branch."""
        result = self._result(measurement_result_raw={"bcp_warnings": []})
        line = _metric_header_line(
            result, MetricOutputItem(name="business_complexity_points", total=10)
        )
        assert "(SDK is missing)" not in line

    def test_non_bcp_metric_with_raw_no_sdk_tag(self):
        """Kills _metric_header_line__mutmut_25 (and -> or)."""
        result = self._result(measurement_result_raw={"bcp_warnings": ["w1"]})
        line = _metric_header_line(
            result, MetricOutputItem(name="mystery", total=10)
        )
        assert "(SDK is missing)" not in line

    def test_cognitive_points_uses_one_decimal(self):
        """Kills _metric_header_line__mutmut_40/41/42/43/44 (cp/tp formatting)."""
        result = self._result()
        line = _metric_header_line(
            result, MetricOutputItem(name="cognitive_points", total=3.55)
        )
        assert "Cognitive Points: 3.5" in line

    def test_token_points_uses_one_decimal(self):
        """Kills _metric_header_line__mutmut_43/44 (token_points literal)."""
        result = self._result()
        line = _metric_header_line(
            result, MetricOutputItem(name="token_points", total=3.55)
        )
        assert "Token Points: 3.5" in line

    def test_regular_metric_plain_total(self):
        """Kills _metric_header_line__mutmut_23/24 (extra_tag default)."""
        result = self._result()
        line = _metric_header_line(
            result, MetricOutputItem(name="function_points", total=3.55)
        )
        assert "Function Points: 3.55" in line


class TestFormatJsonResult:
    def _result(self, **kwargs) -> PipelineResult:
        return PipelineResult(status=PipelineStatus.SUCCESS, **kwargs)

    def test_json_result_exact_structure(self):
        """Kills format_json_result__mutmut_1/6/36/37/38/40/41 (data/dumps mutations)."""
        result = self._result(
            project_path=Path("/proj"),
            export_path=Path("/out/m.json"),
            duration_seconds=1.25,
            stages_executed=[
                StageResult(
                    stage=StageName.DISCOVER,
                    status=StageExecutionStatus.COMPLETED,
                    duration_seconds=1.0,
                    entities_found=4,
                )
            ],
        )
        expected = {
            "status": "success",
            "project_path": "/proj",
            "duration_seconds": 1.25,
            "stages": [
                {
                    "stage": "discover",
                    "status": "completed",
                    "duration_seconds": 1.0,
                    "entities_found": 4,
                }
            ],
            "measurement": None,
            "error": None,
            "export_path": "/out/m.json",
        }
        assert format_json_result(result) == json.dumps(expected, indent=2)

    def test_json_result_none_optional_values(self):
        """Targets format_json_result__mutmut_6/36 optional value None handling."""
        result = self._result()
        payload = json.loads(format_json_result(result))
        assert payload["project_path"] is None
        assert payload["export_path"] is None
        assert payload["error"] is None
        assert payload["measurement"] is None


class TestStatusIcon:
    def test_icons_for_each_status(self):
        """Kills _status_icon__mutmut_1/2/3/4/5/6/7/8/10/11 (icon returns)."""
        assert _status_icon(StageExecutionStatus.COMPLETED) == "\u2713"
        assert _status_icon(StageExecutionStatus.FAILED) == "\u2717"
        assert _status_icon(StageExecutionStatus.SKIPPED) == "\u2014"
        assert _status_icon(StageExecutionStatus.RUNNING) == "\u25b6"
        assert _status_icon(StageExecutionStatus.PENDING) == "\u25cb"

    def test_format_progress_includes_icon(self):
        """Targets _status_icon__mutmut_1/2/3/4/5/6/7/8/10/11 format_progress icon embedding."""
        assert format_progress("discover", StageExecutionStatus.COMPLETED) == (
            "\u2713 discover"
        )


class TestFormatTextResultErrorOutput:
    def test_error_block_with_blank_line(self):
        """Kills _header_lines__mutmut_11/_results_lines__mutmut_17/26 (blank lines)."""
        result = PipelineResult(
            status=PipelineStatus.FAILED,
            error="something broke",
            export_path=Path("/out/x.json"),
        )
        text = format_result(result)
        lines = text.split("\n")
        assert "" in lines
        assert "Error: something broke" in lines
        assert "Output: /out/x.json" in lines
