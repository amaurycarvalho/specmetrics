from __future__ import annotations

import json
from pathlib import Path

from specmetrics.application.artifact_persistence import (
    _serialize_stage_data,
    read_run_artifacts,
    save_run_artifacts,
)
from specmetrics.application.models import (
    PipelineResult,
    PipelineStatus,
    StageOutputItem,
)


def _make_result(
    stage_entities: dict[str, list[dict]] | None = None,
    framework: object = None,
    llm_provider: str = "",
    llm_model: str = "",
) -> PipelineResult:
    stage_details = [
        StageOutputItem(name=name, count=len(entities))
        for name, entities in (stage_entities or {}).items()
    ]
    return PipelineResult(
        status=PipelineStatus.SUCCESS,
        project_path=Path("."),
        stage_details=stage_details,
        stage_entities=stage_entities or {},
        _framework_detected=framework,
        llm_provider=llm_provider,
        llm_model=llm_model,
    )


class TestSerializeStageData:
    def test_default_max_entities_per_stage_is_5000(self) -> None:
        import inspect

        sig = inspect.signature(_serialize_stage_data)
        assert sig.parameters["max_entities_per_stage"].default == 5000
        assert sig.parameters["max_entities_per_stage"].default == 5000

    def test_csm_stage_entities_truncated_per_category(self) -> None:
        result = _make_result(
            stage_entities={
                "csm": [
                    {"type": "decision"},
                    {"type": "decision"},
                    {"type": "assumption"},
                ]
            }
        )
        stages = _serialize_stage_data(result, max_entities_per_stage=1)
        entry = stages["csm"][0]
        assert len(entry["entities"]) == 3
        assert entry["entities"][-1]["_truncated"] is True

    def test_non_csm_stage_entities_truncated_by_count(self) -> None:
        result = _make_result(
            stage_entities={
                "extract": [
                    {"type": "a"},
                    {"type": "a"},
                    {"type": "b"},
                ]
            }
        )
        stages = _serialize_stage_data(result, max_entities_per_stage=1)
        entry = stages["extract"][0]
        assert len(entry["entities"]) == 2
        assert entry["entities"][-1]["_truncated"] is True

    def test_stage_entry_has_canonical_keys(self) -> None:
        result = _make_result(stage_entities={"discover": [{"id": "1"}]})
        stages = _serialize_stage_data(result)
        entry = stages["discover"][0]
        assert set(entry.keys()) == {"name", "count", "count_type", "duration_ms", "entities"}
        assert entry["name"] == "discover"
        assert entry["count"] == 1

    def test_missing_stage_entities_uses_empty_list(self) -> None:
        result = _make_result(stage_entities={"discover": []})
        stages = _serialize_stage_data(result)
        entry = stages["discover"][0]
        assert entry["entities"] == []

    def test_present_stage_entities_flow_through(self) -> None:
        raw = [{"id": "cfm:x", "name": "X"}]
        result = _make_result(stage_entities={"discover": raw})
        stages = _serialize_stage_data(result)
        assert stages["discover"][0]["entities"] == raw

    def test_under_limit_entities_not_truncated(self) -> None:
        raw = [{"id": "1"}, {"id": "2"}]
        result = _make_result(stage_entities={"extract": raw})
        stages = _serialize_stage_data(result, max_entities_per_stage=10)
        assert stages["extract"][0]["entities"] == raw


class TestSaveRunArtifacts:
    def test_writes_under_dot_specmetrics_runs_dir(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(stage_entities={"csm": [{"id": "1"}]})
        run_dir = save_run_artifacts(project_path, "run-1", result)
        assert run_dir == project_path / ".specmetrics" / "runs" / "run-1"
        assert (project_path / ".specmetrics" / "runs" / "run-1" / "metadata.json").exists()
        assert (project_path / ".specmetrics" / "runs" / "run-1" / "csm.json").exists()

    def test_second_save_succeeds_when_dir_exists(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result()
        save_run_artifacts(project_path, "run-1", result)
        save_run_artifacts(project_path, "run-1", result)

    def test_metadata_contains_canonical_keys(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(llm_provider="openai", llm_model="gpt-4o")
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert "id" in metadata
        assert "created_at" in metadata
        assert "sdd_framework" in metadata
        assert "llm" in metadata
        assert "project_path" in metadata

    def test_metadata_json_is_indented_with_two_spaces(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        run_dir = save_run_artifacts(project_path, "run-1", _make_result())
        content = (run_dir / "metadata.json").read_text()
        assert content.startswith('{\n  "')

    def test_metadata_llm_none_provider_excludes_model(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(llm_provider="none", llm_model="gpt-4o")
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["llm"] == {"provider": "none"}

    def test_metadata_llm_with_provider_includes_model(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(llm_provider="openai", llm_model="gpt-4o")
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["llm"] == {"provider": "openai", "model": "gpt-4o"}

    def test_metadata_framework_detected_string(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(framework="openspec")
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["sdd_framework"] == "openspec"

    def test_metadata_framework_non_string_falls_back_to_unknown(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(framework=42)
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["sdd_framework"] == "unknown"

    def test_metadata_missing_framework_is_unknown(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = PipelineResult(
            status=PipelineStatus.SUCCESS,
            project_path=Path("."),
        )
        run_dir = save_run_artifacts(project_path, "run-1", result)
        metadata = json.loads((run_dir / "metadata.json").read_text())
        assert metadata["sdd_framework"] == "unknown"

    def test_entities_truncated_when_max_entities_exceeded(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(
            stage_entities={"extract": [{"id": str(i)} for i in range(5)]}
        )
        run_dir = save_run_artifacts(
            project_path, "run-1", result, max_entities_per_stage=2
        )
        stage_data = json.loads((run_dir / "extract.json").read_text())
        assert stage_data[0]["entities"][-1]["_truncated"] is True

    def test_logs_run_artifacts_saved(self, tmp_path: Path) -> None:
        from structlog.testing import capture_logs

        project_path = tmp_path / "project"
        project_path.mkdir()
        with capture_logs() as captured:
            save_run_artifacts(project_path, "run-1", _make_result())
        assert any(e["event"] == "run_artifacts_saved" for e in captured)


class TestReadRunArtifacts:
    def test_reads_metadata_and_stages(self, tmp_path: Path) -> None:
        project_path = tmp_path / "project"
        project_path.mkdir()
        result = _make_result(stage_entities={"csm": [{"id": "1"}]})
        run_dir = save_run_artifacts(project_path, "run-1", result)
        artifacts = read_run_artifacts(run_dir)
        assert "metadata" in artifacts
        assert artifacts["metadata"]["id"] == "run-1"
        assert "csm" in artifacts

    def test_skips_metrics_and_metadata_as_stages(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "metadata.json").write_text('{"id": "run-1"}')
        (run_dir / "metrics.json").write_text('[{"name": "fpa"}]')
        (run_dir / "csm.json").write_text('[{"name": "csm"}]')
        artifacts = read_run_artifacts(run_dir)
        assert artifacts["metadata"]["id"] == "run-1"
        assert "metrics" not in artifacts
        assert "csm" in artifacts

    def test_reads_files_after_skipped_ones(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "metadata.json").write_text('{"id": "run-1"}')
        (run_dir / "zzz.json").write_text('[{"name": "zzz"}]')
        artifacts = read_run_artifacts(run_dir)
        assert "zzz" in artifacts
