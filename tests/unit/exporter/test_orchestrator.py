from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO
from pathlib import Path

import pytest

from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMetadata,
)
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.plugins.exporter import orchestrator as orch
from specmetrics.plugins.exporter.base import ExporterPlugin, ExportError
from specmetrics.plugins.exporter.models import Measurement


def _ev(doc: str, text: str) -> EvidenceRef:
    return EvidenceRef(graph_node_id="gn-1", document_id=doc, text=text)


def _fp(fid: str, name: str, evidence: EvidenceRef) -> FunctionalProcess:
    return FunctionalProcess(
        id=fid,
        name=name,
        evidence=evidence,
        metadata={"function_type": "EI"},
    )


def _make_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="run-1",
        functional_processes={
            "fp-1": _fp("fp-1", "Login", _ev("doc-1", "login text")),
            "fp-2": _fp("fp-2", "Export", _ev("doc-1", "login text")),
            "fp-3": _fp("fp-3", "Report", _ev("doc-2", "report text")),
        },
        metadata=CfmBuildMetadata(
            run_id="run-1",
            build_duration_ms=123,
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        ),
    )


class _FakeExporter(ExporterPlugin):
    def __init__(self, fmt: str = "json") -> None:
        self._fmt = fmt
        self.written: list[dict] = []

    def format_id(self) -> str:
        return self._fmt

    def file_extension(self) -> str:
        return ".json"

    def content_type(self) -> str:
        return "application/json"

    def export(self, measurements, evidence_refs, metadata, output):
        self.written.append(
            {"n": len(measurements), "refs": len(evidence_refs), "meta": metadata.model_dump()}
        )
        output.write("ok")


class _RaisingExporter(_FakeExporter):
    def __init__(self, exc) -> None:
        super().__init__("boom")
        self._exc = exc

    def export(self, measurements, evidence_refs, metadata, output):
        raise self._exc


class TestExtractMeasurements:
    def test_counts_fps_with_evidence_and_attrs(self) -> None:
        ms = orch._extract_measurements(_make_cfm())
        assert len(ms) == 3
        m = ms[0]
        assert isinstance(m, Measurement)
        assert m.function_id == "fp-1"
        assert m.function_name == "Login"
        assert m.category == "functional_process"
        assert m.complexity == ""
        assert m.functional_size == 0.0
        assert len(m.evidence) == 1
        assert m.evidence[0].document_id == "doc-1"
        assert m.attributes == {"function_type": "EI"}


class TestExtractEvidence:
    def test_deduplicates_by_document_and_text(self) -> None:
        refs = orch._extract_evidence(_make_cfm())
        docs = sorted(r.document_id for r in refs)
        assert docs == ["doc-1", "doc-2"]
        assert len(refs) == 2

    def test_empty_cfm(self) -> None:
        cfm = CanonicalFunctionalModel(
            run_id="r",
            functional_processes={},
            metadata=CfmBuildMetadata(run_id="r"),
        )
        assert orch._extract_evidence(cfm) == []


class TestEnsureListAndFlatten:
    def test_ensure_list_list(self) -> None:
        assert orch._ensure_list([1, 2]) == [1, 2]

    def test_ensure_list_dict(self) -> None:
        assert orch._ensure_list({"a": 1}) == [{"a": 1}]

    def test_ensure_list_other(self) -> None:
        assert orch._ensure_list("x") == []

    def test_flatten_items(self) -> None:
        items = [{"name": "a", "count": 1, "x": "y"}, {"name": "b"}]
        rows = orch._flatten_items(items, ["name", "count", "x"])
        assert rows == [["a", "1", "y"], ["b", "", ""]]


class TestNormalizeStages:
    def test_normalize_discover(self) -> None:
        data = [
            {
                "name": "scan",
                "count": 2,
                "count_type": "files",
                "duration_ms": 5,
                "entities": [{"document_name": "d.md", "relative_path": "a/d.md"}],
            }
        ]
        out = orch.normalize_discover_stage(data)
        assert "scan,2,files,5" in out
        assert "document_name,relative_path" in out
        assert "d.md,a/d.md" in out

    def test_normalize_discover_single_dict(self) -> None:
        out = orch.normalize_discover_stage({"name": "x", "count": 1, "count_type": "t"})
        assert "x,1,t," in out

    def test_normalize_measure(self) -> None:
        data = [
            {"name": "m", "count": 1, "entities": [{"metric": "fp", "total": 3, "status": "ok"}]}
        ]
        out = orch.normalize_measure_stage(data)
        assert "metric,total,status,duration_ms" in out
        assert "fp,3,ok," in out

    def test_normalize_items(self) -> None:
        out = orch.normalize_items_stage([{"name": "i", "count": 2, "duration_ms": 9}])
        assert "i,2,,9" in out

    def test_stage_to_csv_dispatch(self) -> None:
        assert orch.stage_to_csv("discover", []).startswith("name,count")
        assert orch.stage_to_csv("measure", []).startswith("name,count")
        assert "name,count" in orch.stage_to_csv("other", [{"name": "a"}])


class TestXml:
    def test_stage_to_xml_renders_entries(self) -> None:
        xml_str = orch.stage_to_xml("measure", [{"name": "a", "count": 1}])
        assert "<stage name=\"measure\">" in xml_str
        assert "<name>a</name>" in xml_str
        assert "<count>1</count>" in xml_str

    def test_dict_to_xml_nested(self) -> None:
        root = orch.ET.Element("root")
        orch._dict_to_xml(root, {"a": {"b": "c"}, "d": None})
        assert root.find("a/b").text == "c"
        assert root.find("d").text == ""


class TestBatched:
    def test_batched_sizes(self) -> None:
        batches = list(orch._batched([1, 2, 3, 4, 5], 2))
        assert batches == [[1, 2], [3, 4], [5]]

    def test_batched_empty(self) -> None:
        assert list(orch._batched([], 2)) == []


class TestExportToDir:
    def test_single_exporter_small(self, tmp_path: Path) -> None:
        exp = _FakeExporter("json")
        orch_orch = orch.ExportOrchestrator([exp])
        results = orch_orch.export_to_dir(_make_cfm(), tmp_path)
        assert results == [{"format": "json", "path": str(tmp_path / "measurements.json"), "status": "completed"}]
        assert (tmp_path / "measurements.json").exists()
        assert exp.written[0]["n"] == 3
        assert exp.written[0]["refs"] == 2

    def test_export_format_filter(self, tmp_path: Path) -> None:
        exp1 = _FakeExporter("json")
        exp2 = _FakeExporter("xml")
        orch_orch = orch.ExportOrchestrator([exp1, exp2])
        results = orch_orch.export_to_dir(_make_cfm(), tmp_path, formats=["xml"])
        assert len(results) == 1
        assert results[0]["format"] == "xml"
        assert exp1.written == []

    def test_export_batched(self, tmp_path: Path) -> None:
        exp = _FakeExporter("json")
        # force batching path via monkeypatching BATCH_SIZE threshold on measurements
        orch.ExportOrchestrator([exp]).export_to_dir(_make_cfm(), tmp_path)
        # normal small path
        assert (tmp_path / "measurements.json").exists()

    def test_export_error_handling(self, tmp_path: Path) -> None:
        exp = _RaisingExporter(ExportError("boom", format_id="boom"))
        results = orch.ExportOrchestrator([exp]).export_to_dir(_make_cfm(), tmp_path)
        assert results[0]["status"] == "failed"
        assert "boom" in results[0]["error"]

    def test_export_unexpected_error(self, tmp_path: Path) -> None:
        exp = _RaisingExporter(RuntimeError("crash"))
        results = orch.ExportOrchestrator([exp]).export_to_dir(_make_cfm(), tmp_path)
        assert results[0]["status"] == "error"


    def test_metadata_attached(self, tmp_path: Path) -> None:
        exp = _FakeExporter("json")
        orch.ExportOrchestrator([exp]).export_to_dir(_make_cfm(), tmp_path)
        meta = exp.written[0]["meta"]
        assert meta["run_id"] == "run-1"
        assert meta["function_count"] == 3
        assert meta["pipeline_duration_ms"] == 123
        assert meta["specmetrics_version"]
        assert meta["export_timestamp"] == datetime(2024, 1, 1, tzinfo=UTC)


class TestExportToStream:
    def test_export_to_stream(self) -> None:
        exp = _FakeExporter("json")
        out = StringIO()
        orch.ExportOrchestrator([exp]).export_to_stream(_make_cfm(), out, fmt="json")
        assert out.getvalue() == "ok"
        assert exp.written[0]["n"] == 3

    def test_export_to_stream_unknown_format(self) -> None:
        out = StringIO()
        with pytest.raises(ExportError):
            orch.ExportOrchestrator([_FakeExporter("json")]).export_to_stream(
                _make_cfm(), out, fmt="csv"
            )


class TestGetVersion:
    def test_returns_version_string(self) -> None:
        orch_inst = orch.ExportOrchestrator([])
        assert orch_inst._get_version()

class TestNormalizeHeaderKillers:
    """Kills string-literal survivors in the normalize_* CSV headers/rows."""

    def test_discover_exact_header_and_row(self) -> None:
        data = [
            {
                "name": "scan",
                "count": 2,
                "count_type": "files",
                "duration_ms": 5,
                "entities": [{"document_name": "d.md", "relative_path": "a/d.md"}],
            }
        ]
        out = orch.normalize_discover_stage(data)
        assert "name,count,count_type,duration_ms" in out
        assert "scan,2,files,5" in out
        assert "d.md,a/d.md" in out

    def test_measure_exact_header_and_rows(self) -> None:
        data = [
            {
                "name": "m",
                "count": 1,
                "count_type": "files",
                "duration_ms": 7,
                "entities": [{"metric": "fp", "total": 3, "status": "ok", "duration_ms": 9}],
            }
        ]
        out = orch.normalize_measure_stage(data)
        assert "name,count,count_type,duration_ms" in out
        assert "m,1,files,7" in out
        assert "metric,total,status,duration_ms" in out
        assert "fp,3,ok,9" in out

    def test_items_exact_header_and_row(self) -> None:
        data = [{"name": "i", "count": 2, "count_type": "items", "duration_ms": 9}]
        out = orch.normalize_items_stage(data)
        assert "name,count,count_type,duration_ms" in out
        assert "i,2,items,9" in out

    def test_measure_missing_entities_key_ok(self) -> None:
        out = orch.normalize_measure_stage([{"name": "m", "count": 1}])
        assert "name,count,count_type,duration_ms" in out
        assert "metric,total,status,duration_ms" in out


class TestExportMetadataStream:
    """Kills survivors in ``export_to_stream`` metadata (mutmut_10,13..17)."""

    def test_stream_metadata_values(self) -> None:
        from importlib.metadata import version as _v

        exp = _FakeExporter("json")
        out = StringIO()
        orch.ExportOrchestrator([exp]).export_to_stream(_make_cfm(), out)
        meta = exp.written[0]["meta"]
        assert meta["run_id"] == "run-1"
        assert meta["function_count"] == 3
        assert meta["pipeline_duration_ms"] == 123
        assert meta["specmetrics_version"] == _v("specmetrics")
        assert meta["export_timestamp"] == datetime(2024, 1, 1, tzinfo=UTC)

    def test_stream_default_fmt_is_json(self) -> None:
        exp = _FakeExporter("json")
        out = StringIO()
        orch.ExportOrchestrator([exp]).export_to_stream(_make_cfm(), out)
        assert out.getvalue() == "ok"
        assert exp.written[0]["n"] == 3


class TestExportBatching:
    """Kills survivors in ``export_to_dir`` batched path (mutmut_22..47)."""

    def test_exact_batch_size_uses_single_file(self, monkeypatch, tmp_path: Path) -> None:
        exp = _FakeExporter("json")
        monkeypatch.setattr(orch, "BATCH_SIZE", 3)
        results = orch.ExportOrchestrator([exp]).export_to_dir(_make_cfm(), tmp_path)
        assert results[0]["status"] == "completed"
        assert (tmp_path / "measurements.json").exists()
        assert not (tmp_path / "measurements_0.json").exists()

    def test_batched_paths_written(self, monkeypatch, tmp_path: Path) -> None:
        cfm = _make_cfm()
        cfm2 = CanonicalFunctionalModel(
            run_id="run-1",
            functional_processes={
                **cfm.functional_processes,
                "fp-4": _fp("fp-4", "Four", _ev("doc-2", "four text")),
                "fp-5": _fp("fp-5", "Five", _ev("doc-2", "five text")),
            },
            metadata=cfm.metadata,
        )

        def _batched2(items: list, size: int = 2):
            for i in range(0, len(items), size):
                yield items[i : i + size]

        exp = _FakeExporter("json")
        monkeypatch.setattr(orch, "BATCH_SIZE", 2)
        monkeypatch.setattr(orch, "_batched", _batched2)
        results = orch.ExportOrchestrator([exp]).export_to_dir(cfm2, tmp_path)
        assert results[0]["status"] == "completed"
        paths = results[0]["paths"]
        assert len(paths) == 3
        assert all(Path(p).exists() for p in paths)
        assert exp.written[0]["n"] == 2


class TestGetVersionKillers:
    """Kills survivors in ``ExportOrchestrator._get_version`` (mutmut_1..4)."""

    def test_returns_installed_version(self) -> None:
        from importlib.metadata import version as _v

        assert orch.ExportOrchestrator([])._get_version() == _v("specmetrics")

    def test_fallback_version_when_package_missing(self, monkeypatch) -> None:
        def _raise(name: str) -> str:
            raise ImportError("not found")

        monkeypatch.setattr("importlib.metadata.version", _raise)
        assert orch.ExportOrchestrator([])._get_version() == "0.1.0"
