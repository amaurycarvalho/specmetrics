from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

from specmetrics.cli.measure import run_measure


from specmetrics.application.enums import (
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from specmetrics.application.models import StageResult


class TestRunMeasure:
    def _make_mock_result(self, status: str = "success"):
        from specmetrics.application.models import MeasurementResult
        m = MagicMock()
        m.status = PipelineStatus.SUCCESS if status == "success" else PipelineStatus.FAILED
        m.project_path = None
        m.stages_executed = [
            StageResult(
                stage=StageName.MEASURE,
                status=StageExecutionStatus.COMPLETED,
                duration_seconds=0.5,
            ),
        ]
        m.duration_seconds = 0.5
        m.measurement = MeasurementResult(total_function_points=42)
        m.error = ""
        m.export_path = None
        m.run_id = "test-run"
        return m

    @patch("specmetrics.cli.measure.PipelineOrchestrator")
    def test_run_measure_defaults(self, MockOrch: MagicMock):
        mock_orch = MockOrch.return_value
        mock_orch.execute.return_value = self._make_mock_result()

        exit_code = run_measure(
            project_path=Path("."),
            output=None,
            stage=None,
            from_stage=None,
            verbose=False,
            quiet=False,
            log_file=None,
            config_path=None,
        )
        assert exit_code == 0
        mock_orch.execute.assert_called_once()

    @patch("specmetrics.cli.measure.PipelineOrchestrator")
    def test_run_measure_with_stage(self, MockOrch: MagicMock):
        mock_orch = MockOrch.return_value
        mock_orch.execute.return_value = self._make_mock_result()

        exit_code = run_measure(
            project_path=Path("/test"),
            output="json:/tmp/out.json",
            stage="extract",
            from_stage=None,
            verbose=True,
            quiet=False,
            log_file=None,
            config_path=None,
        )
        assert exit_code == 0
