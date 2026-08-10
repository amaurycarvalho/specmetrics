from __future__ import annotations

import json
from pathlib import Path

from specmetrics.application.export_writer import (
    _get_llm_info,
    _write_json_output,
)
from specmetrics.application.models import (
    ErrorOutputItem,
    MetricOutputItem,
    PipelineRequest,
    StageOutputItem,
)


class _FakeConfig:
    def __init__(self, provider: str = "", model: str = "") -> None:
        self.llm_provider = provider
        self.llm_model = model


class _FakeConfigSystem:
    def __init__(self, cfg: object, raise_on_load: bool = False) -> None:
        self._cfg = cfg
        self._raise = raise_on_load

    def load(self):
        if self._raise:
            raise RuntimeError("boom")
        return self._cfg


class TestGetLlmInfo:
    def test_returns_defaults_when_no_config_system(self) -> None:
        assert _get_llm_info(None) == ("none", "")

    def test_reads_provider_and_model_from_config(self) -> None:
        cfg = _FakeConfigSystem(_FakeConfig(provider="openai", model="gpt-4o"))
        assert _get_llm_info(cfg) == ("openai", "gpt-4o")

    def test_falls_back_to_none_when_config_empty(self) -> None:
        cfg = _FakeConfigSystem(_FakeConfig(provider="", model=""))
        assert _get_llm_info(cfg) == ("none", "")

    def test_empty_load_falls_back_to_defaults(self) -> None:
        cfg = _FakeConfigSystem(None)
        assert _get_llm_info(cfg) == ("none", "")

    def test_load_exception_returns_defaults(self) -> None:
        cfg = _FakeConfigSystem(None, raise_on_load=True)
        assert _get_llm_info(cfg) == ("none", "")


class TestWriteJsonOutput:
    def _request(self) -> PipelineRequest:
        return PipelineRequest(project_path=Path("/repo"), measure_id="m-1")

    def _write(
        self,
        tmp_path: Path,
        framework_detected: str = "",
        output_errors: list[ErrorOutputItem] | None = None,
        config_system: object | None = None,
    ) -> Path:
        metric_results = [
            MetricOutputItem(name="function_points", total=42, status="completed", duration_ms=3)
        ]
        stage_details = [
            StageOutputItem(name="discover", count=5, count_type="documents", duration_ms=1)
        ]
        return _write_json_output(
            self._request(),
            None,
            tmp_path,
            metric_results,
            stage_details,
            output_errors or [],
            config_system,
            framework_detected,
        )

    def test_writes_specmetrics_output_json(self, tmp_path: Path) -> None:
        export_file = self._write(tmp_path)
        assert export_file == tmp_path / "specmetrics-output.json"
        assert export_file.exists()

    def test_output_contains_measure_metadata(self, tmp_path: Path) -> None:
        export_file = self._write(tmp_path, framework_detected="openspec")
        data = json.loads(export_file.read_text())
        measure = data["measure"]
        assert measure["id"] == "m-1"
        assert measure["id_path"] == "m-1"
        assert measure["sdd_framework"] == "openspec"
        assert measure["project_path"] == "/repo"

    def test_framework_defaults_to_unknown(self, tmp_path: Path) -> None:
        export_file = self._write(tmp_path, framework_detected="")
        data = json.loads(export_file.read_text())
        assert data["measure"]["sdd_framework"] == "unknown"

    def test_llm_info_included(self, tmp_path: Path) -> None:
        config = _FakeConfigSystem(_FakeConfig(provider="openai", model="gpt-4o"))
        export_file = self._write(tmp_path, config_system=config)
        data = json.loads(export_file.read_text())
        assert data["measure"]["llm"] == {"provider": "openai", "model": "gpt-4o"}

    def test_llm_info_without_model(self, tmp_path: Path) -> None:
        config = _FakeConfigSystem(_FakeConfig(provider="none", model=""))
        export_file = self._write(tmp_path, config_system=config)
        data = json.loads(export_file.read_text())
        assert data["measure"]["llm"] == {"provider": "none"}

    def test_results_stage_details_errors_present(self, tmp_path: Path) -> None:
        output_errors = [
            ErrorOutputItem(stage="extract", message="bad doc", details={"doc": "x"})
        ]
        export_file = self._write(tmp_path, output_errors=output_errors)
        data = json.loads(export_file.read_text())
        result = data["results"][0]
        assert result["name"] == "function_points"
        assert result["total"] == 42
        assert result["status"] == "completed"
        assert result["duration_ms"] == 3
        stage = data["stages"][0]
        assert stage["name"] == "discover"
        assert stage["count"] == 5
        assert stage["count_type"] == "documents"
        assert stage["duration_ms"] == 1
        err = data["errors"][0]
        assert err["stage"] == "extract"
        assert err["message"] == "bad doc"
        assert err["details"] == {"doc": "x"}

    def test_output_json_is_indented(self, tmp_path: Path) -> None:
        export_file = self._write(tmp_path)
        content = export_file.read_text()
        assert content.startswith('{\n  "')
