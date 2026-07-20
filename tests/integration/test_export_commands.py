from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from specmetrics.cli.app import app
from specmetrics.application.measure_id import generate_measure_id

runner = CliRunner()


def _make_run_dir(base: Path, measure_id: str, stage_data: dict | None = None) -> Path:
    run_dir = base / ".specmetrics" / "runs" / measure_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metadata.json").write_text(
        json.dumps({"id": measure_id, "created_at": "2026-01-01T00:00:00Z", "sdd_framework": "test", "llm": {"provider": "none"}}, indent=2)
    )
    if stage_data:
        for name, content in stage_data.items():
            (run_dir / f"{name}.json").write_text(json.dumps(content))
    return run_dir


class TestExportRunIntegration:
    def test_export_run_with_id_creates_json_files(self, tmp_path: Path):
        mid = generate_measure_id()
        _make_run_dir(tmp_path, mid, {
            "discovery": [{"name": "req1", "count": 5}],
            "extraction": [{"name": "req1", "count": 3}],
        })
        result = runner.invoke(app, ["export", "run", mid, str(tmp_path)])
        assert result.exit_code == 0, result.output
        exports = tmp_path / ".specmetrics" / "exports"
        assert exports.is_dir()
        json_files = list(exports.glob("*.json"))
        assert len(json_files) >= 1

    def test_export_run_with_missing_id_shows_error(self, tmp_path: Path):
        result = runner.invoke(app, ["export", "run", "nonexistent-id", str(tmp_path)])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_export_run_default_selects_latest_run(self, tmp_path: Path):
        mid1 = generate_measure_id()
        mid2 = generate_measure_id()
        _make_run_dir(tmp_path, mid1, {"discovery": [{"name": "a", "count": 1}]})
        _make_run_dir(tmp_path, mid2, {"discovery": [{"name": "b", "count": 2}]})
        cwd = Path.cwd().resolve()
        import os
        os.chdir(str(tmp_path))
        try:
            result = runner.invoke(app, ["export", "run"])
        finally:
            os.chdir(str(cwd))
        assert result.exit_code == 0, result.output
        exports = tmp_path / ".specmetrics" / "exports"
        assert exports.is_dir()

    def test_export_run_csv_format(self, tmp_path: Path):
        mid = generate_measure_id()
        _make_run_dir(tmp_path, mid, {
            "discovery": [{"name": "req1", "count": 5}],
        })
        result = runner.invoke(app, ["export", "run", mid, str(tmp_path), "--format", "csv"])
        assert result.exit_code == 0, result.output
        exports = tmp_path / ".specmetrics" / "exports"
        csv_files = list(exports.glob("*.csv"))
        assert len(csv_files) >= 1

    def test_export_run_missing_id_shows_error(self, tmp_path: Path):
        result = runner.invoke(app, ["export", "run", "nonexistent-id", str(tmp_path)])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_export_run_multiple_formats(self, tmp_path: Path):
        mid = generate_measure_id()
        _make_run_dir(tmp_path, mid, {
            "discovery": [{"name": "req1", "count": 5}],
        })
        result = runner.invoke(app, ["export", "run", mid, str(tmp_path), "--format", "json,csv,xml"])
        assert result.exit_code == 0, result.output
        exports = tmp_path / ".specmetrics" / "exports"
        assert len(list(exports.glob("*.json"))) >= 1
        assert len(list(exports.glob("*.csv"))) >= 1
        assert len(list(exports.glob("*.xml"))) >= 1
