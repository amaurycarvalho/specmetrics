from __future__ import annotations

from specmetrics.application.enums import PipelineStatus, StageName
from specmetrics.application.models import PipelineResult, StageResult
from specmetrics.cli.formatters import format_text_result as format_result


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
