from __future__ import annotations

from pathlib import Path

from specmetrics.application.enums import (
    OutputFormat,
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from specmetrics.application.models import (
    MeasurementResult,
    PipelineRequest,
    PipelineResult,
    PluginInfo,
    StageResult,
    VersionInfo,
)


class TestPipelineRequest:
    def test_default_project_path(self):
        req = PipelineRequest(project_path=Path("/test"))
        assert req.project_path == Path("/test")
        assert req.stages is None
        assert req.output_format == OutputFormat.NONE

    def test_with_stages(self):
        req = PipelineRequest(
            project_path=Path("."),
            stages=[StageName.MEASURE],
            verbose=True,
        )
        assert req.stages == [StageName.MEASURE]
        assert req.verbose is True


class TestPipelineResult:
    def test_success_result(self):
        result = PipelineResult(status=PipelineStatus.SUCCESS)
        assert result.status == PipelineStatus.SUCCESS
        assert result.stages_executed == []

    def test_with_measurement(self):
        m = MeasurementResult(total_function_points=42)
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            measurement=m,
        )
        assert result.measurement.total_function_points == 42


class TestStageResult:
    def test_completed_stage(self):
        sr = StageResult(
            stage=StageName.EXTRACT,
            status=StageExecutionStatus.COMPLETED,
            duration_seconds=1.5,
        )
        assert sr.stage == StageName.EXTRACT
        assert sr.duration_seconds == 1.5


class TestVersionInfo:
    def test_platform_version(self):
        vi = VersionInfo(platform_version="0.1.0", python_version="3.13")
        assert vi.platform_version == "0.1.0"
        assert vi.python_version == "3.13"

    def test_with_plugins(self):
        pi = PluginInfo(name="apf", version="0.1.0", type="measurement")
        vi = VersionInfo(
            platform_version="0.1.0",
            python_version="3.13",
            plugins=[pi],
        )
        assert len(vi.plugins) == 1
        assert vi.plugins[0].name == "apf"
