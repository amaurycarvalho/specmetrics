from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

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
