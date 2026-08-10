from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from specmetrics.cli import export_commands
from specmetrics.cli.app import app
from specmetrics.cli.export_commands import list_measure_runs

runner = CliRunner()


class TestExportRunUnit:
    def test_json_export_copies_files(self, tmp_path: Path):
        mid = "20260720-120000-a1b2c3d4"
        run_dir = tmp_path / ".specmetrics" / "runs" / mid
        run_dir.mkdir(parents=True)
        (run_dir / "metadata.json").write_text(json.dumps({"id": mid}))
        (run_dir / "discovery.json").write_text(json.dumps([{"name": "x", "count": 1}]))

        out_dir = tmp_path / ".specmetrics" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        from specmetrics.application.orchestrator import read_run_artifacts

        artifacts = read_run_artifacts(run_dir)
        for fname, data in artifacts.items():
            if fname == "metadata":
                continue
            (out_dir / f"{fname}.json").write_text(json.dumps(data))

        assert (out_dir / "discovery.json").exists()
        assert json.loads((out_dir / "discovery.json").read_text()) == [
            {"name": "x", "count": 1}
        ]

    def test_csv_export_normalization(self, tmp_path: Path):
        from specmetrics.plugins.exporter.orchestrator import stage_to_csv

        data = [{"name": "req1", "count": 5}, {"name": "req2", "count": 3}]
        csv_out = stage_to_csv("discovery", data)
        assert "name" in csv_out
        assert "count" in csv_out
        assert "req1" in csv_out
        assert "5" in csv_out
        lines = csv_out.strip().split("\n")
        assert len(lines) == 3

    def test_csv_export_empty_data(self):
        from specmetrics.plugins.exporter.orchestrator import stage_to_csv

        csv_out = stage_to_csv("discovery", [])
        assert "name" in csv_out  # headers still present
        lines = csv_out.strip().split("\n")
        assert len(lines) == 1  # only header, no data rows

    def test_xml_export_normalization(self, tmp_path: Path):
        from specmetrics.plugins.exporter.orchestrator import stage_to_xml

        data = [{"name": "req1", "count": 5}]
        xml_out = stage_to_xml("discovery", data)
        assert "<name>" in xml_out
        assert "<count>" in xml_out
        assert "<entry>" in xml_out
        assert "discovery" in xml_out

    def test_xml_export_empty_data(self):
        from specmetrics.plugins.exporter.orchestrator import stage_to_xml

        xml_out = stage_to_xml("discovery", [])
        assert "<stage" in xml_out
        assert "discovery" in xml_out


class TestExportRunErrors:
    def test_nonexistent_id_shows_not_found(self, tmp_path: Path):
        result = runner.invoke(app, ["export", "run", "bad-id", str(tmp_path)])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_error_includes_available_runs(self, tmp_path: Path):
        mid = "20260720-120000-aaaabbbb"
        runs_dir = tmp_path / ".specmetrics" / "runs" / mid
        runs_dir.mkdir(parents=True)
        (runs_dir / "metadata.json").write_text(
            json.dumps({"id": mid, "created_at": "2026-01-01T00:00:00Z"})
        )

        result = runner.invoke(app, ["export", "run", "nonexistent-id", str(tmp_path)])
        assert result.exit_code != 0
        assert mid in result.output


class TestListMeasureRuns:
    def test_empty_runs_dir_returns_empty_list(self, tmp_path: Path):
        runs = list_measure_runs(tmp_path)
        assert runs == []

    def test_nonexistent_runs_dir_returns_empty_list(self, tmp_path: Path):
        runs = list_measure_runs(tmp_path / "nonexistent")
        assert runs == []

    def test_returns_sorted_runs(self, tmp_path: Path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        run_a = runs_dir / "20260720-100000-a1b2c3d4"
        run_b = runs_dir / "20260720-110000-b5e6f7a8"
        run_a.mkdir(parents=True)
        run_b.mkdir(parents=True)
        meta_a = {"created_at": "2026-07-20T10:00:00"}
        meta_b = {"created_at": "2026-07-20T11:00:00"}
        (run_a / "metadata.json").write_text(json.dumps(meta_a))
        (run_b / "metadata.json").write_text(json.dumps(meta_b))

        runs = list_measure_runs(tmp_path)
        assert len(runs) == 2
        assert runs[0]["id"] == "20260720-110000-b5e6f7a8"
        assert runs[1]["id"] == "20260720-100000-a1b2c3d4"

    def test_handles_missing_metadata(self, tmp_path: Path):
        runs_dir = tmp_path / ".specmetrics" / "runs"
        run_dir = runs_dir / "20260720-100000-a1b2c3d4"
        run_dir.mkdir(parents=True)
        runs = list_measure_runs(tmp_path)
        assert len(runs) == 1
        assert runs[0]["id"] == "20260720-100000-a1b2c3d4"


def _echo_recorder(monkeypatch) -> list[tuple]:
    calls: list[tuple] = []
    monkeypatch.setattr(export_commands.typer, "echo", lambda *a, **k: calls.append((a, k)))
    return calls


class TestResolveTargetRun:
    def test_explicit_measure_id_returned_directly(self, monkeypatch):
        """Targets _resolve_target_run__mutmut_2/4/22 explicit-id branch."""
        assert (
            export_commands._resolve_target_run(
                "abc", Path("/proj"), Path("/out"), ["json"], False, None, False
            )
            == "abc"
        )

    def test_no_runs_returns_none_and_echoes(self, tmp_path: Path, monkeypatch):
        """Kills _resolve_target_run__mutmut_4/5/6/7/8 (no-runs branch)."""
        monkeypatch.setattr(export_commands, "list_measure_runs", lambda p: [])
        calls = _echo_recorder(monkeypatch)
        pipeline_calls = []
        monkeypatch.setattr(
            export_commands,
            "run_pipeline_export",
            lambda *a: pipeline_calls.append(a),
        )
        result = export_commands._resolve_target_run(
            None, tmp_path, Path("/out"), ["json"], True, "http://otel", True
        )
        assert result is None
        assert pipeline_calls == [(tmp_path, Path("/out"), ["json"], True, "http://otel", True)]
        assert ("No measure runs found. Running measurement pipeline directly...",) in [
            a for a, _ in calls
        ]
        assert ("Export complete \u2014 /out",) in [a for a, _ in calls]

    def test_runs_exist_returns_first_id(self, tmp_path: Path, monkeypatch):
        """Kills _resolve_target_run__mutmut_2/4/22 (runs None / return index)."""
        monkeypatch.setattr(
            export_commands,
            "list_measure_runs",
            lambda p: [{"id": "run-b"}, {"id": "run-a"}],
        )
        calls = _echo_recorder(monkeypatch)
        pipeline_calls = []
        monkeypatch.setattr(export_commands, "run_pipeline_export", lambda *a: pipeline_calls.append(a))
        result = export_commands._resolve_target_run(
            None, tmp_path, Path("/out"), ["json"], False, None, False
        )
        assert result == "run-b"
        assert pipeline_calls == []
        assert calls == []

    def test_runs_echo_complete_via_pipeline_path(self, tmp_path: Path, monkeypatch):
        """Kills _resolve_target_run__mutmut_21 (Export complete -> None)."""
        monkeypatch.setattr(export_commands, "list_measure_runs", lambda p: [])
        calls = _echo_recorder(monkeypatch)
        monkeypatch.setattr(export_commands, "run_pipeline_export", lambda *a: None)
        export_commands._resolve_target_run(None, tmp_path, Path("/out"), [], False, None, False)
        assert ("Export complete \u2014 /out",) in [a for a, _ in calls]


class TestFailRunNotFound:
    def test_missing_run_no_available_echoes_err(self, tmp_path: Path, monkeypatch):
        """Kills _fail_run_not_found__mutmut_13/15/16/18 (echo err + exit code)."""
        monkeypatch.setattr(export_commands, "list_measure_runs", lambda p: [])
        calls = _echo_recorder(monkeypatch)
        with pytest.raises(typer.Exit) as exc:
            export_commands._fail_run_not_found("bad-id", tmp_path)
        assert exc.value.exit_code == 1
        assert calls == [(('Measure run "bad-id" not found.',), {"err": True})]

    def test_available_runs_listed_with_comma_space(self, tmp_path: Path, monkeypatch):
        """Kills _fail_run_not_found__mutmut_6/9/10 (ids join + prefix + limit)."""
        runs = [{"id": f"run-{i:02d}"} for i in range(6)]
        monkeypatch.setattr(export_commands, "list_measure_runs", lambda p: runs)
        calls = _echo_recorder(monkeypatch)
        with pytest.raises(typer.Exit) as exc:
            export_commands._fail_run_not_found("bad-id", tmp_path)
        assert exc.value.exit_code == 1
        msg = calls[0][0][0]
        assert 'Measure run "bad-id" not found.' in msg
        assert " Available runs: run-00, run-01, run-02, run-03, run-04" in msg
        assert "run-05" not in msg
