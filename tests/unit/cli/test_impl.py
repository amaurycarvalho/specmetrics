from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import typer

from specmetrics.application.enums import PipelineStatus
from specmetrics.application.models import PipelineResult
from specmetrics.cli import _impl
from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.plugins.exporter.base import ExporterPlugin


def _make_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="run-123",
        functional_processes={
            "fp1": FunctionalProcess(
                id="fp1",
                name="Process One",
                evidence=EvidenceRef(
                    graph_node_id="g1", document_id="doc1", text="evidence-a"
                ),
            ),
            "fp2": FunctionalProcess(
                id="fp2",
                name="Process Two",
                evidence=EvidenceRef(
                    graph_node_id="g2", document_id="doc2", text="evidence-b"
                ),
            ),
        },
        metadata=BuildMetadata(run_id="run-123"),
    )


class FakeExporter(ExporterPlugin):
    def format_id(self) -> str:
        return "json"

    def file_extension(self) -> str:
        return ".json"

    def content_type(self) -> str:
        return "application/json"

    def export(self, measurements, evidence_refs, metadata, output) -> None:
        output.write(json.dumps([m.function_id for m in measurements]))


class TestExportSelected:
    def test_export_selected_creates_all_formats_and_skips_metadata(
        self, tmp_path: Path, capsys
    ):
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "metadata.json").write_text(json.dumps({"id": "x"}))
        (run_dir / "discover.json").write_text(json.dumps([{"name": "a"}]))

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        artifacts = {"metadata": {"id": "x"}, "discover": [{"name": "a"}]}

        _impl.export_selected(["json", "csv", "xml"], run_dir, artifacts, out_dir)

        assert (out_dir / "discover.json").exists()
        assert (out_dir / "discover.csv").exists()
        assert (out_dir / "discover.xml").exists()
        assert not (out_dir / "metadata.json").exists()
        assert not (out_dir / "metadata.csv").exists()
        assert not (out_dir / "metadata.xml").exists()

        json.loads((out_dir / "discover.json").read_text())
        captured = capsys.readouterr()
        assert "json" in captured.out
        assert "csv" in captured.out
        assert "xml" in captured.out

    def test_export_json_skips_metadata(self, tmp_path: Path):
        run_dir = tmp_path / "run"
        run_dir.mkdir()
        (run_dir / "metadata.json").write_text(json.dumps({"id": "x"}))
        (run_dir / "a.json").write_text("{}")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        _impl._export_json(run_dir, out_dir)

        assert (out_dir / "a.json").exists()
        assert not (out_dir / "metadata.json").exists()

    def test_export_csv_skips_metadata(self, tmp_path: Path):
        artifacts = {"metadata": {"id": "x"}, "stage": [{"name": "a", "count": 1}]}
        _impl._export_csv(artifacts, tmp_path)
        assert (tmp_path / "stage.csv").exists()
        assert not (tmp_path / "metadata.csv").exists()

    def test_export_xml_skips_metadata(self, tmp_path: Path):
        artifacts = {"metadata": {"id": "x"}, "stage": [{"name": "a", "count": 1}]}
        _impl._export_xml(artifacts, tmp_path)
        assert (tmp_path / "stage.xml").exists()
        assert not (tmp_path / "metadata.xml").exists()


class TestRunPipelineExport:
    def test_failed_pipeline_exits(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            _impl.PipelineOrchestrator,
            "execute",
            lambda self, request: PipelineResult(
                status=PipelineStatus.FAILED, error="boom"
            ),
        )
        with pytest.raises(typer.Exit) as exc_info:
            _impl.run_pipeline_export(
                tmp_path, tmp_path / "out", ["json"], False, None, False
            )
        assert exc_info.value.exit_code == 1

    def test_success_with_canonical_model(self, tmp_path, monkeypatch, capsys):
        cfm = _make_cfm()
        monkeypatch.setattr(
            _impl.PipelineOrchestrator,
            "execute",
            lambda self, request: PipelineResult(
                status=PipelineStatus.SUCCESS, canonical_model=cfm
            ),
        )
        monkeypatch.setattr(
            _impl, "discover_exporter_plugins", lambda: [FakeExporter()]
        )

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        _impl.run_pipeline_export(tmp_path, out_dir, ["json"], False, None, False)

        out_file = out_dir / "measurements.json"
        assert out_file.exists()
        content = json.loads(out_file.read_text())
        assert content == ["fp1", "fp2"]
        assert "measurements.json" in capsys.readouterr().out

    def test_no_exporter_plugins_exits(self, tmp_path, monkeypatch):
        cfm = _make_cfm()
        monkeypatch.setattr(
            _impl.PipelineOrchestrator,
            "execute",
            lambda self, request: PipelineResult(
                status=PipelineStatus.SUCCESS, canonical_model=cfm
            ),
        )
        monkeypatch.setattr(_impl, "discover_exporter_plugins", list)

        with pytest.raises(typer.Exit) as exc_info:
            _impl.run_pipeline_export(
                tmp_path, tmp_path / "out", ["json"], False, None, False
            )
        assert exc_info.value.exit_code == 1

    def test_publish_path(self, tmp_path, monkeypatch, capsys):
        cfm = _make_cfm()
        monkeypatch.setattr(
            _impl.PipelineOrchestrator,
            "execute",
            lambda self, request: PipelineResult(
                status=PipelineStatus.SUCCESS, canonical_model=cfm
            ),
        )
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [FakeExporter()])
        monkeypatch.setattr(
            _impl, "publish_all", lambda *a, **kw: [
                {"publisher": "otel", "success": True, "message": "sent"}
            ]
        )

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        _impl.run_pipeline_export(
            tmp_path, out_dir, ["json"], True, "http://localhost:4317", False
        )
        captured = capsys.readouterr()
        assert "otel" in captured.out

    def test_publish_without_endpoint(self, tmp_path, monkeypatch, capsys):
        cfm = _make_cfm()
        monkeypatch.setattr(
            _impl.PipelineOrchestrator,
            "execute",
            lambda self, request: PipelineResult(
                status=PipelineStatus.SUCCESS, canonical_model=cfm
            ),
        )
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [FakeExporter()])
        monkeypatch.setattr(
            _impl, "publish_all", lambda *a, **k: [
                {"publisher": "x", "success": False, "message": "no"}
            ]
        )
        out_dir = tmp_path / "out"
        out_dir.mkdir()
        _impl.run_pipeline_export(tmp_path, out_dir, ["json"], True, None, False)
        captured = capsys.readouterr()
        assert "x" in captured.out


class TestExtractMeasurements:
    def test_extracts_measurements(self):
        cfm = _make_cfm()
        measurements = _impl.extract_measurements(cfm)
        assert len(measurements) == 2
        assert {m.function_id for m in measurements} == {"fp1", "fp2"}
        assert {m.function_name for m in measurements} == {
            "Process One",
            "Process Two",
        }
        assert all(m.category == "functional_process" for m in measurements)

    def test_missing_processes_returns_empty(self):
        cfm = SimpleNamespace()
        assert _impl.extract_measurements(cfm) == []

    def test_exception_path_returns_empty(self):
        obj = SimpleNamespace()
        obj.functional_processes = None
        assert _impl.extract_measurements(obj) == []

    def test_process_without_evidence(self):
        proc = SimpleNamespace(id="fp3", name="P3")
        ev = EvidenceRef(graph_node_id="g1", document_id="d1", text="t")
        cfm = SimpleNamespace(
            functional_processes={
                "fp1": SimpleNamespace(id="fp1", name="P1", evidence=ev),
                "fp3": proc,
            }
        )
        measurements = _impl.extract_measurements(cfm)
        found = next(m for m in measurements if m.function_id == "fp3")
        assert found.evidence == []
        assert any(m.function_id == "fp1" and m.evidence == [ev] for m in measurements)


class TestDiscoverExporterPlugins:
    def test_discovers_and_instantiates(self, monkeypatch):
        class Good(ExporterPlugin):
            def format_id(self):
                return "json"

            def file_extension(self):
                return ".json"

            def content_type(self):
                return "application/json"

            def export(self, measurements, evidence_refs, metadata, output):
                pass

        ep1 = SimpleNamespace(name="good", load=lambda: Good)
        monkeypatch.setattr(_impl, "entry_points", lambda group: [ep1])
        plugins = _impl.discover_exporter_plugins()
        assert len(plugins) == 1
        assert isinstance(plugins[0], Good)

    def test_ignores_faulty_entry_point(self, monkeypatch):
        class Bad(Exception):
            pass

        def raiser():
            raise Bad("load boom")

        ep_bad = SimpleNamespace(name="bad", load=raiser)
        monkeypatch.setattr(_impl, "entry_points", lambda group: [ep_bad])
        assert _impl.discover_exporter_plugins() == []

    def test_skips_non_exporter_class(self, monkeypatch):
        ep = SimpleNamespace(name="notexporter", load=lambda: str)
        monkeypatch.setattr(_impl, "entry_points", lambda group: [ep])
        assert _impl.discover_exporter_plugins() == []


class TestExportCanonicalModel:
    def test_reports_completed_and_failed(self, tmp_path, monkeypatch, capsys):
        class Plugin:
            def __init__(self, ok):
                self.ok = ok

            def format_id(self):
                return "ok" if self.ok else "bad"

        exp = MagicMock()
        exp.export_to_dir.return_value = [
            {"format": "ok", "path": "p.json", "status": "completed"},
            {"format": "bad", "status": "failed", "error": "nope"},
        ]
        monkeypatch.setattr(_impl, "ExportOrchestrator", lambda *args: exp)

        cfm = _make_cfm()
        _impl._export_canonical_model(
            cfm, [Plugin(True)], tmp_path, ["ok", "bad"]
        )
        captured = capsys.readouterr()
        assert "✓" in captured.out
        assert "✗" in captured.out