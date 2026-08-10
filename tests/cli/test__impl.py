from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest
import typer

from specmetrics.application.enums import OutputFormat
from specmetrics.cli import _impl
from specmetrics.plugins.exporter.base import ExporterPlugin


class _FakeExporter(ExporterPlugin):
    def format_id(self) -> str:
        return "fake"

    def file_extension(self) -> str:
        return ".fake"

    def content_type(self) -> str:
        return "text/plain"

    def export(self, measurements, evidence_refs, metadata, output) -> None:
        return None


class _OtherExporter(_FakeExporter):
    def format_id(self) -> str:
        return "other"


class TestDiscoverExporterPlugins:
    def test_loads_exporter_plugin_entry_points(self, monkeypatch):
        """Kills discover_exporter_plugins__mutmut_2/3/4 (entry_points group)."""
        called: list[str] = []

        class EP:
            def __init__(self, name, cls):
                self.name = name
                self._cls = cls

            def load(self):
                called.append(self.name)
                return self._cls

        monkeypatch.setattr(
            _impl, "entry_points", lambda group: [EP("fake", _FakeExporter), EP("other", _OtherExporter)]
        )
        plugins = _impl.discover_exporter_plugins()
        assert called == ["fake", "other"]
        assert isinstance(plugins[0], _FakeExporter)
        assert isinstance(plugins[1], _OtherExporter)

    def test_skips_non_exporter_classes(self, monkeypatch):
        """Targets discover_exporter_plugins__mutmut_2/3/4 subclass filtering."""
        class EP:
            def __init__(self, name, cls):
                self.name = name
                self._cls = cls

            def load(self):
                return self._cls

        monkeypatch.setattr(
            _impl, "entry_points", lambda group: [EP("not-plugin", dict)]
        )
        assert _impl.discover_exporter_plugins() == []

    def test_load_failure_logs_warning(self, monkeypatch):
        """Kills discover_exporter_plugins__mutmut_12 (logger.warning event -> None)."""
        class EP:
            name = "broken"

            def load(self):
                raise RuntimeError("nope")

        monkeypatch.setattr(_impl, "entry_points", lambda group: [EP()])
        warnings: list[tuple] = []
        monkeypatch.setattr(_impl.logger, "warning", lambda *args, **kwargs: warnings.append((args, kwargs)))
        assert _impl.discover_exporter_plugins() == []
        assert warnings
        assert warnings[0][0][0] == "exporter_load_failed"
        assert warnings[0][1]["entry_point"] == "broken"


class TestExportJson:
    def test_copies_all_json_except_metadata(self, tmp_path: Path, monkeypatch):
        """Kills _export_json__mutmut_7 (continue -> break)."""
        copied: list[str] = []
        monkeypatch.setattr(_impl.shutil, "copy2", lambda src, dst: copied.append(dst.name))
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        class FakeRunDir:
            def glob(self, pattern):
                assert pattern == "*.json"
                return [Path("a.json"), Path("metadata.json"), Path("z.json")]

        _impl._export_json(FakeRunDir(), out_dir)
        assert copied == ["a.json", "z.json"]


class TestExportCsv:
    def test_passes_stage_name_and_data_to_stage_to_csv(self, tmp_path: Path, monkeypatch):
        """Kills _export_csv__mutmut_6/7 (stage_to_csv args -> None)."""
        recorded: list[tuple] = []
        monkeypatch.setattr(_impl, "stage_to_csv", lambda fname, data: recorded.append((fname, data)) or "csv")
        artifacts = {"metadata": {"x": 1}, "discovery": [{"name": "req"}]}
        _impl._export_csv(artifacts, tmp_path)
        assert recorded == [("discovery", [{"name": "req"}])]
        assert (tmp_path / "discovery.csv").exists()


class TestExportXml:
    def test_passes_stage_name_and_data_to_stage_to_xml(self, tmp_path: Path, monkeypatch):
        """Kills _export_xml__mutmut_7 (stage_to_xml data -> None)."""
        recorded: list[tuple] = []
        monkeypatch.setattr(_impl, "stage_to_xml", lambda fname, data: recorded.append((fname, data)) or "<x/>")
        artifacts = {"metadata": {"x": 1}, "discovery": [{"name": "req"}]}
        _impl._export_xml(artifacts, tmp_path)
        assert recorded == [("discovery", [{"name": "req"}])]
        assert (tmp_path / "discovery.xml").exists()


class _Recorder:
    def __init__(self):
        self.requests: list = []
        self.export_calls: list = []
        self.publish_calls: list = []

    def orch(self):
        orch = self
        orch._last_request = None

        def execute(request):
            self._last_request = request
            return self._result

        self.execute = execute
        return self


def _result(status: str = "success", error: str = "", cfm: object = object()):
    return SimpleNamespace(
        status=SimpleNamespace(value=status),
        error=error,
        canonical_model=cfm,
    )


class _RequestRecorder:
    last: dict | None = None

    def __init__(self, **kwargs):
        _RequestRecorder.last = kwargs
        self._kwargs = kwargs


class _ExportOrchestratorFake:
    def __init__(self, results):
        self._results = results
        self.export_to_dir_kwargs: dict | None = None

    def export_to_dir(self, **kwargs):
        self.export_to_dir_kwargs = kwargs
        return self._results


class TestRunPipelineExport:
    def test_builds_request_and_exports_selected_formats(self, tmp_path: Path, monkeypatch):
        """Kills run_pipeline_export__mutmut_2/3/4/5/7/8 (request kwargs mutations)."""
        captured = {}

        class Request:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        the_result = _result(cfm=object())

        class Orch:
            def execute(self, request):
                captured["_request"] = request
                return the_result

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        export_calls = []
        monkeypatch.setattr(
            _impl, "_export_canonical_model",
            lambda cfm, exporters, out_dir, selected_formats: export_calls.append((cfm, exporters, out_dir, selected_formats)),
        )
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [_FakeExporter()])
        _impl.run_pipeline_export(Path("/proj"), Path("/out"), ["json"], False, None, True)
        assert captured["project_path"] == Path("/proj")
        assert captured["output_format"] == OutputFormat.NONE
        assert captured["verbose"] is True
        assert export_calls[0][0] is the_result.canonical_model
        assert isinstance(export_calls[0][1][0], _FakeExporter)
        assert export_calls[0][2] == Path("/out")
        assert export_calls[0][3] == ["json"]

    def test_passes_request_object_to_orchestrator(self, tmp_path: Path, monkeypatch):
        """Kills run_pipeline_export__mutmut_10 (orch.execute(request) -> None)."""
        executed: list = []

        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                executed.append(request)
                return _result(cfm=object())

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        monkeypatch.setattr(_impl, "_export_canonical_model", lambda *a, **k: None)
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [_FakeExporter()])
        _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], False, None, False)
        assert len(executed) == 1
        assert executed[0].__class__.__name__ == "Request"

    def test_failed_pipeline_echoes_and_exits(self, monkeypatch, capsys):
        """Kills run_pipeline_export__mutmut_12/13/14/15/16/17/18/31/32 (failed path)."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(status="failed", error="boom")

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        echo_calls: list[tuple] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echo_calls.append((a, k)))
        with pytest.raises(typer.Exit) as exc:
            _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], False, None, False)
        assert exc.value.exit_code == 1
        assert echo_calls == [(("Pipeline failed: boom",), {"err": True})]

    def test_no_canonical_model_echoes_and_exits(self, monkeypatch):
        """Kills run_pipeline_export__mutmut_23/24/25/26/27/28/29/30 (no data path)."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(cfm=None)

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        echo_calls: list[tuple] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echo_calls.append((a, k)))
        with pytest.raises(typer.Exit) as exc:
            _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], False, None, False)
        assert exc.value.exit_code == 1
        assert echo_calls == [(("No measurement data available to export",), {"err": True})]

    def test_no_exporter_plugins_echoes_and_exits(self, monkeypatch):
        """Kills run_pipeline_export__mutmut_35/36/37/38/39/40/41/42 (no plugins path)."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(cfm=object())

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        monkeypatch.setattr(_impl, "discover_exporter_plugins", list)
        echo_calls: list[tuple] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echo_calls.append((a, k)))
        with pytest.raises(typer.Exit) as exc:
            _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], False, None, False)
        assert exc.value.exit_code == 1
        assert echo_calls == [(("No exporter plugins found",), {"err": True})]

    def test_csv_only_formats_skip_canonical_export(self, tmp_path: Path, monkeypatch):
        """Kills run_pipeline_export__mutmut_49 (or not selected_formats -> or selected_formats)."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(cfm=object())

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [_FakeExporter()])
        export_calls = []
        monkeypatch.setattr(_impl, "_export_canonical_model", lambda *a, **k: export_calls.append(a))
        _impl.run_pipeline_export(Path("/proj"), Path("/out"), ["csv"], False, None, False)
        assert export_calls == []

    def test_empty_formats_default_to_json_export(self, tmp_path: Path, monkeypatch):
        """Targets run_pipeline_export__mutmut_49 empty-formats default."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(cfm=object())

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [_FakeExporter()])
        export_calls = []
        monkeypatch.setattr(_impl, "_export_canonical_model", lambda cfm, exporters, out_dir, selected_formats: export_calls.append(selected_formats))
        _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], False, None, False)
        assert export_calls == [[]]

    def test_publish_passes_otel_endpoint(self, tmp_path: Path, monkeypatch):
        """Kills run_pipeline_export__mutmut_59 (_publish_canonical_model endpoint -> None)."""
        class Request:
            def __init__(self, **kwargs):
                pass

        class Orch:
            def execute(self, request):
                return _result(cfm=object())

        monkeypatch.setattr(_impl, "PipelineRequest", Request)
        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch)
        monkeypatch.setattr(_impl, "discover_exporter_plugins", lambda: [_FakeExporter()])
        monkeypatch.setattr(_impl, "_export_canonical_model", lambda *a, **k: None)
        publish_calls = []
        monkeypatch.setattr(_impl, "_publish_canonical_model", lambda cfm, endpoint: publish_calls.append((cfm, endpoint)))
        the_result = _result(cfm=object())

        class Orch2:
            def execute(self, request):
                return the_result

        monkeypatch.setattr(_impl, "PipelineOrchestrator", Orch2)
        _impl.run_pipeline_export(Path("/proj"), Path("/out"), [], True, "http://otel:4318", False)
        assert publish_calls == [(the_result.canonical_model, "http://otel:4318")]


class TestExportCanonicalModel:
    def test_passes_selected_formats_to_export_to_dir(self, monkeypatch):
        """Kills _export_canonical_model__mutmut_6/9 (formats kwarg -> None/removed)."""
        fake = _ExportOrchestratorFake(results=[])
        monkeypatch.setattr(_impl, "ExportOrchestrator", lambda exporters: fake)
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: None)
        _impl._export_canonical_model(object(), [_FakeExporter()], Path("/out"), ["json", "csv"])
        assert fake.export_to_dir_kwargs["formats"] == ["json", "csv"]
        assert fake.export_to_dir_kwargs["cfm"] is not None
        assert fake.export_to_dir_kwargs["output_dir"] == Path("/out")

    def test_completed_status_renders_checkmark(self, monkeypatch):
        """Kills _export_canonical_model__mutmut_11/14/17 (status icon + comparison)."""
        fake = _ExportOrchestratorFake(results=[{"format": "json", "path": "/out/m.json", "status": "completed"}])
        monkeypatch.setattr(_impl, "ExportOrchestrator", lambda exporters: fake)
        echoed: list[str] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echoed.append(a[0]))
        _impl._export_canonical_model(object(), [_FakeExporter()], Path("/out"), ["json"])
        assert echoed == ["  \u2713 json: /out/m.json"]

    def test_failed_status_renders_cross(self, monkeypatch):
        """Targets _export_canonical_model__mutmut_11/14/17 failed-status rendering."""
        fake = _ExportOrchestratorFake(results=[{"format": "json", "status": "failed", "error": "oops"}])
        monkeypatch.setattr(_impl, "ExportOrchestrator", lambda exporters: fake)
        echoed: list[str] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echoed.append(a[0]))
        _impl._export_canonical_model(object(), [_FakeExporter()], Path("/out"), ["json"])
        assert echoed == ["  \u2717 json: oops"]

    def test_unknown_fallback_when_no_path_or_error(self, monkeypatch):
        """Kills _export_canonical_model__mutmut_22/24/27/28/29/30/31/32/33/34 (fallback chain)."""
        fake = _ExportOrchestratorFake(results=[{"format": "json", "status": "failed"}])
        monkeypatch.setattr(_impl, "ExportOrchestrator", lambda exporters: fake)
        echoed: list[str] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echoed.append(a[0]))
        _impl._export_canonical_model(object(), [_FakeExporter()], Path("/out"), ["json"])
        assert echoed == ["  \u2717 json: unknown"]


class TestPublishCanonicalModel:
    def test_builds_metadata_and_publishes(self, monkeypatch):
        """Kills _publish_canonical_model__mutmut_2/3/6/7/16/17/18/19/20/21 (args)."""
        import specmetrics.plugins.exporter.models as exporter_models

        cfm = SimpleNamespace(run_id="run-123")
        measurements = ["m1", "m2"]
        monkeypatch.setattr(_impl, "extract_measurements", lambda c: measurements)
        metadata_kwargs: dict = {}

        class Metadata:
            def __init__(self, **kwargs):
                metadata_kwargs.update(kwargs)

        monkeypatch.setattr(exporter_models, "ExportMetadata", Metadata)
        publish_kwargs: dict = {}

        def publish_all(*args, **kwargs):
            publish_kwargs["args"] = args
            publish_kwargs["kwargs"] = kwargs
            return []

        monkeypatch.setattr(_impl, "publish_all", publish_all)
        echoed: list[str] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echoed.append(a[0]))
        _impl._publish_canonical_model(cfm, None)
        assert metadata_kwargs == {"run_id": "run-123", "function_count": 2}
        assert publish_kwargs["kwargs"] == {"configs": {}, "publisher_configs": []}
        assert publish_kwargs["args"][0] is measurements

    def test_otel_endpoint_adds_publisher_config(self, monkeypatch):
        """Kills _publish_canonical_model__mutmut_9/10/11 (otel config key/value)."""
        import specmetrics.plugins.exporter.models as exporter_models

        cfm = SimpleNamespace(run_id="run-1")
        monkeypatch.setattr(_impl, "extract_measurements", lambda c: [])
        monkeypatch.setattr(exporter_models, "ExportMetadata", lambda **kwargs: SimpleNamespace(**kwargs))
        captured: dict = {}

        def publish_all(*args, **kwargs):
            captured.update(kwargs)
            return []

        monkeypatch.setattr(_impl, "publish_all", publish_all)
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: None)
        _impl._publish_canonical_model(cfm, "http://otel:4318")
        from specmetrics.plugins.publisher.base import PublisherConfig

        cfg = captured["configs"].get("otel")
        assert isinstance(cfg, PublisherConfig)
        assert cfg.endpoint_url == "http://otel:4318"

    def test_publish_results_render_icons(self, monkeypatch):
        """Kills _publish_canonical_model__mutmut_22/23/26 (status icon rendering)."""
        import specmetrics.plugins.exporter.models as exporter_models

        cfm = SimpleNamespace(run_id="run-1")
        monkeypatch.setattr(_impl, "extract_measurements", lambda c: [])
        monkeypatch.setattr(exporter_models, "ExportMetadata", lambda **kwargs: SimpleNamespace(**kwargs))
        monkeypatch.setattr(
            _impl, "publish_all",
            lambda *args, **kwargs: [
                {"publisher": "otel", "success": True, "message": "sent", "metrics_count": 1},
                {"publisher": "file", "success": False, "message": "failed", "metrics_count": 0},
            ],
        )
        echoed: list[str] = []
        monkeypatch.setattr(_impl.typer, "echo", lambda *a, **k: echoed.append(a[0]))
        _impl._publish_canonical_model(cfm, None)
        assert echoed == ["  \u2713 otel: sent", "  \u2717 file: failed"]


class TestExtractMeasurements:
    def test_missing_functional_processes_returns_empty(self):
        """Kills extract_measurements__mutmut_5/8 (getattr default -> None/removed)."""
        assert _impl.extract_measurements(SimpleNamespace()) == []

    def test_processes_with_ids_and_names(self):
        """Kills extract_measurements__mutmut_22/25/28/31/34/37 (getattr defaults)."""
        from specmetrics.kernel.cfm.model import EvidenceRef

        evidence = EvidenceRef(graph_node_id="n1", document_id="doc-1", section_id="s1", text="t")
        proc = SimpleNamespace(id="fp-1", name="Calc", evidence=evidence)

        class Cfm:
            functional_processes: ClassVar = {"fp-1": proc}

        measurements = _impl.extract_measurements(Cfm())
        assert len(measurements) == 1
        assert measurements[0].function_id == "fp-1"
        assert measurements[0].function_name == "Calc"
        assert measurements[0].category == "functional_process"
        assert measurements[0].evidence == [evidence]

    def test_missing_id_and_name_use_empty_strings(self):
        """Kills extract_measurements__mutmut_22/25/28/31/34/37 getattr fallbacks."""
        proc = SimpleNamespace()

        class Cfm:
            functional_processes: ClassVar = {"fp-1": proc}

        measurements = _impl.extract_measurements(Cfm())
        assert measurements[0].function_id == ""
        assert measurements[0].function_name == ""

    def test_process_without_evidence_gets_empty_evidence(self):
        """Targets extract_measurements__mutmut_22/25/28/31/34/37 evidence fallback."""
        proc = SimpleNamespace(id="fp-1", name="N")

        class Cfm:
            functional_processes: ClassVar = {"fp-1": proc}

        measurements = _impl.extract_measurements(Cfm())
        assert measurements[0].evidence == []
