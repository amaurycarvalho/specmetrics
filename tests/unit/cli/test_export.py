from __future__ import annotations

import json
from pathlib import Path

from specmetrics.cli import _export


def _make_run(tmp_path: Path, mid: str = "rmid") -> Path:
    run_dir = tmp_path / ".specmetrics" / "runs" / mid
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "metadata.json").write_text(json.dumps({"id": mid}))
    (run_dir / "metrics.json").write_text(json.dumps({"m": 1}))
    (run_dir / "discover.json").write_text(json.dumps([{"name": "a", "count": 1}]))
    return run_dir


class TestAutoExportHelpers:
    def test_auto_export_json_skips_metadata_and_metrics(self, tmp_path):
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "metadata.json").write_text("{}")
        (run_dir / "metrics.json").write_text("{}")
        (run_dir / "a.json").write_text("{}")
        out = tmp_path / "out"
        out.mkdir()
        _export._auto_export_json(run_dir, out)
        assert (out / "a.json").exists()
        assert not (out / "metadata.json").exists()
        assert not (out / "metrics.json").exists()

    def test_auto_export_csv(self, tmp_path):
        artifacts = {"metadata": {}, "discover": [{"name": "a", "count": 1}]}
        _export._auto_export_csv(artifacts, tmp_path)
        assert (tmp_path / "discover.csv").exists()
        assert not (tmp_path / "metadata.csv").exists()

    def test_auto_export_xml(self, tmp_path):
        artifacts = {"metadata": {}, "discover": [{"name": "a", "count": 1}]}
        _export._auto_export_xml(artifacts, tmp_path)
        assert (tmp_path / "discover.xml").exists()
        assert not (tmp_path / "metadata.xml").exists()


class TestRunAutoExport:
    def test_missing_run_prints_and_returns(self, tmp_path, capsys):
        _export.run_auto_export(tmp_path, "ghost", "json")
        captured = capsys.readouterr().out
        assert "not found" in captured

    def test_exports_selected_formats(self, tmp_path, capsys):
        _make_run(tmp_path)
        out_dir = tmp_path / ".specmetrics" / "exports"
        _export.run_auto_export(tmp_path, "rmid", "json,csv,xml")
        assert (out_dir / "discover.csv").exists()
        assert (out_dir / "discover.xml").exists()
        assert (out_dir / "discover.json").exists()
        assert not (out_dir / "metadata.json").exists()
        assert "Auto-export complete" in capsys.readouterr().out

    def test_read_artifacts_excludes_metadata_and_metrics(self, tmp_path):
        _make_run(tmp_path)
        out_dir = tmp_path / ".specmetrics" / "exports"
        _export.run_auto_export(tmp_path, "rmid", "csv")
        assert (out_dir / "discover.csv").exists()
        assert not (out_dir / "metadata.csv").exists()


class TestRunExportRequested:
    def test_invalid_format_prints_error(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(_export, "run_auto_export", lambda *a, **k: None)
        result = _export.run_export_requested(tmp_path, "mid", "yaml")
        assert result == 0
        captured = capsys.readouterr().out
        assert "Invalid export format" in captured

    def test_valid_format_dispatches(self, tmp_path, monkeypatch):
        called = {}
        monkeypatch.setattr(
            _export, "run_auto_export", lambda *a, **k: called.update(args=a)
        )
        _export.run_export_requested(tmp_path, "mid", "csv, xml")
        assert called["args"][0] == tmp_path.resolve()
        assert called["args"][1] == "mid"
        assert called["args"][2] == "csv, xml"

    def test_none_format_defaults_to_json(self, tmp_path, monkeypatch):
        called = {}
        monkeypatch.setattr(
            _export, "run_auto_export", lambda *a, **k: called.update(args=a)
        )
        _export.run_export_requested(Path("/tmp/proj"), "mid", None)
        assert called["args"][2] == "json"