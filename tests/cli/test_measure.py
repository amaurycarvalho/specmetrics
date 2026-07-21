from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

from specmetrics.application.measure_id import generate_measure_id
from specmetrics.cli.measure import run_measure, _parse_metrics


from specmetrics.application.enums import (
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from specmetrics.application.models import StageResult


class TestParseMetrics:
    def test_none_returns_none(self):
        assert _parse_metrics(None) is None

    def test_empty_string_returns_none(self):
        assert _parse_metrics("") is None

    def test_all_returns_none(self):
        assert _parse_metrics("all") is None

    def test_single_metric(self):
        assert _parse_metrics("fpa") == ["fpa"]

    def test_multiple_metrics(self):
        assert _parse_metrics("fpa, sfp") == ["fpa", "sfp"]

    def test_whitespace_trimmed(self):
        assert _parse_metrics(" fpa , sfp ") == ["fpa", "sfp"]

    def test_duplicates_removed(self):
        assert _parse_metrics("fpa, fpa") == ["fpa"]

    def test_all_overrides_others(self):
        assert _parse_metrics("all, fpa") is None

    def test_invalid_metric_returns_none(self):
        result = _parse_metrics("invalid")
        assert result is None

    def test_mixed_valid_invalid_returns_none(self):
        result = _parse_metrics("fpa, unknown")
        assert result is None

    def test_all_valid_ids_accepted(self):
        result = _parse_metrics("bcp, fpa, sfp, snap, sp, tshirt, tp, cp")
        assert result is not None
        assert len(result) == 8


class TestGenerateMeasureId:
    def test_format_matches_pattern(self):
        mid = generate_measure_id()
        import re

        assert re.match(r"^\d{8}-\d{6}-[a-f0-9]{8}$", mid), f"Unexpected format: {mid}"

    def test_unique_ids(self):
        ids = {generate_measure_id() for _ in range(100)}
        assert len(ids) == 100, "Measure IDs should be unique across 100 generations"

    def test_ordering_by_timestamp(self):
        ids = [generate_measure_id() for _ in range(5)]
        timestamps = [mid[:15] for mid in ids]
        assert timestamps == sorted(timestamps), (
            "Measure IDs should be lexicographically sortable by creation time"
        )


class TestRunMeasure:
    def _make_mock_result(self, status: str = "success"):
        from specmetrics.application.models import MeasurementResult

        m = MagicMock()
        m.status = (
            PipelineStatus.SUCCESS if status == "success" else PipelineStatus.FAILED
        )
        m.project_path = None
        m.llm_provider = "none"
        m.llm_model = None
        m.stage_details = []
        m.metric_results = []
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
    def test_run_measure_defaults(self, MockOrch: MagicMock, tmp_path: Path):
        mock_orch = MockOrch.return_value
        mock_orch.execute.return_value = self._make_mock_result()

        exit_code = run_measure(
            project_path=tmp_path,
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
    def test_run_measure_with_stage(self, MockOrch: MagicMock, tmp_path: Path):
        mock_orch = MockOrch.return_value
        mock_orch.execute.return_value = self._make_mock_result()

        exit_code = run_measure(
            project_path=tmp_path,
            output="json:/tmp/out.json",
            stage="extract",
            from_stage=None,
            verbose=True,
            quiet=False,
            log_file=None,
            config_path=None,
        )
        assert exit_code == 0
