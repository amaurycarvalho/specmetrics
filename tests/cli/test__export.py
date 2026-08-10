from __future__ import annotations

import json
from pathlib import Path

from specmetrics.cli import _export


class TestAutoExportCsv:
    def test_passes_stage_name_and_data_to_stage_to_csv(self, tmp_path: Path, monkeypatch):
        """Kills _auto_export_csv__mutmut_7/8 (stage_to_csv args -> None)."""
        recorded: list[tuple] = []
        monkeypatch.setattr(_export, "stage_to_csv", lambda fname, data: recorded.append((fname, data)) or "csv")
        artifacts = {"metadata": {"x": 1}, "discovery": [{"name": "req", "count": 2}]}
        _export._auto_export_csv(artifacts, tmp_path)
        assert recorded == [("discovery", [{"name": "req", "count": 2}])]
        assert (tmp_path / "discovery.csv").exists()

    def test_skips_metadata_stage(self, tmp_path: Path, monkeypatch):
        """Targets _auto_export_csv metadata skip (guards _auto_export_csv__mutmut_7/8)."""
        recorded: list[tuple] = []
        monkeypatch.setattr(_export, "stage_to_csv", lambda fname, data: recorded.append(fname) or "csv")
        _export._auto_export_csv({"metadata": {"x": 1}}, tmp_path)
        assert recorded == []


class TestAutoExportXml:
    def test_passes_stage_name_and_data_to_stage_to_xml(self, tmp_path: Path, monkeypatch):
        """Kills _auto_export_xml__mutmut_8 (stage_to_xml data -> None)."""
        recorded: list[tuple] = []
        monkeypatch.setattr(_export, "stage_to_xml", lambda fname, data: recorded.append((fname, data)) or "<x/>")
        artifacts = {"metadata": {"x": 1}, "discovery": [{"name": "req"}]}
        _export._auto_export_xml(artifacts, tmp_path)
        assert recorded == [("discovery", [{"name": "req"}])]
        assert (tmp_path / "discovery.xml").exists()


class TestRunAutoExport:
    def test_creates_nested_exports_dir(self, tmp_path: Path, monkeypatch):
        """Kills run_auto_export__mutmut_18/19/20/21/22/23 (mkdir parents/exist_ok)."""
        run_dir = tmp_path / ".specmetrics" / "runs" / "20260720-120000-a1b2c3d4"
        run_dir.mkdir(parents=True)
        (run_dir / "discovery.json").write_text(json.dumps([{"name": "req", "count": 1}]))
        monkeypatch.setattr(_export, "read_run_artifacts", lambda rd: {"discovery": [{"name": "req", "count": 1}]})
        _export.run_auto_export(tmp_path, "20260720-120000-a1b2c3d4", "json")
        assert (tmp_path / ".specmetrics" / "exports" / "discovery.json").exists()

    def test_calls_run_twice_when_out_dir_exists(self, tmp_path: Path, monkeypatch):
        """Kills run_auto_export__mutmut_22/23 (exist_ok=False would raise on 2nd call)."""
        run_dir = tmp_path / ".specmetrics" / "runs" / "20260720-120000-a1b2c3d4"
        run_dir.mkdir(parents=True)
        (run_dir / "discovery.json").write_text(json.dumps([{"name": "req", "count": 1}]))
        monkeypatch.setattr(_export, "read_run_artifacts", lambda rd: {"discovery": [{"name": "req", "count": 1}]})
        _export.run_auto_export(tmp_path, "20260720-120000-a1b2c3d4", "json")
        _export.run_auto_export(tmp_path, "20260720-120000-a1b2c3d4", "json")
        assert (tmp_path / ".specmetrics" / "exports" / "discovery.json").exists()

    def test_missing_run_prints_not_found(self, tmp_path: Path, capsys):
        """Targets run_auto_export missing-run branch (guards run_auto_export__mutmut_18-23)."""
        _export.run_auto_export(tmp_path, "does-not-exist", "json")
        out = capsys.readouterr().out
        assert "Measure run 'does-not-exist' not found." in out


class TestRunExportRequested:
    def test_invalid_formats_joined_with_comma_space(self, capsys):
        """Kills run_export_requested__mutmut_18 (', ' separator -> 'XX, XX')."""
        _export.run_export_requested(Path("."), "mid", "pdf,doc")
        out = capsys.readouterr().out
        assert "pdf, doc" in out
        assert "Error: Invalid export format(s): pdf, doc. Use json, csv, xml." in out

    def test_valid_formats_delegate_to_auto_export(self, tmp_path: Path, monkeypatch, capsys):
        """Targets run_export_requested__mutmut_18 delegation for valid formats."""
        run_dir = tmp_path / ".specmetrics" / "runs" / "mid"
        run_dir.mkdir(parents=True)
        (run_dir / "discovery.json").write_text("[]")
        monkeypatch.setattr(_export, "read_run_artifacts", lambda rd: {})
        _export.run_export_requested(tmp_path, "mid", "json")
        out = capsys.readouterr().out
        assert "Auto-export complete" in out

    def test_none_format_defaults_to_json(self, tmp_path: Path, monkeypatch, capsys):
        """Targets run_export_requested__mutmut_18 default format json."""
        run_dir = tmp_path / ".specmetrics" / "runs" / "mid"
        run_dir.mkdir(parents=True)
        (run_dir / "discovery.json").write_text("[]")
        monkeypatch.setattr(_export, "read_run_artifacts", lambda rd: {})
        _export.run_export_requested(tmp_path, "mid", None)
        out = capsys.readouterr().out
        assert "Auto-export complete" in out
