import pytest

from specmetrics.kernel import (
    EventType,
    HandlerRegistry,
    PipelineContext,
    PipelineEngine,
    PipelineError,
    StageError,
)


class TestPipelineEngine:
    def test_publishes_repository_loaded_first(self) -> None:
        registry = HandlerRegistry()
        handler = CapturingHandler(
            EventType.REPOSITORY_LOADED, "repo_handler", "Repository"
        )
        registry.register(handler)
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(
            e.event_type == EventType.REPOSITORY_LOADED for e in ctx.published_events
        )

    def test_invokes_handlers_in_canonical_order(self) -> None:
        registry = HandlerRegistry()
        order: list[str] = []

        class OrderHandler:
            def __init__(self, et: EventType, hid: str, sn: str) -> None:
                self._et = et
                self._hid = hid
                self._sn = sn

            @property
            def handled_event_type(self) -> EventType:
                return self._et

            @property
            def handler_id(self) -> str:
                return self._hid

            @property
            def stage_name(self) -> str:
                return self._sn

            def handle(self, event):
                order.append(self._sn)
                return event.context

        registry.register(OrderHandler(EventType.REPOSITORY_LOADED, "a", "A"))
        registry.register(OrderHandler(EventType.DOCUMENTS_DISCOVERED, "b", "B"))
        registry.register(
            OrderHandler(EventType.SEMANTIC_EXTRACTION_COMPLETED, "c", "C")
        )
        engine = PipelineEngine(registry)
        engine.run(PipelineContext())
        assert order == ["A", "B", "C"]

    def test_returns_pipeline_completed_on_success(self) -> None:
        registry = HandlerRegistry()
        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "h1", "S1"))
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(
            e.event_type == EventType.PIPELINE_COMPLETED for e in ctx.published_events
        )

    def test_stage_error_halts_pipeline(self) -> None:
        registry = HandlerRegistry()

        class FailingHandler:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.REPOSITORY_LOADED

            @property
            def handler_id(self) -> str:
                return "fail"

            @property
            def stage_name(self) -> str:
                return "FailStage"

            def handle(self, event):
                raise StageError("FailStage", "intentional")

        registry.register(FailingHandler())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(
            e.event_type == EventType.PIPELINE_FAILED for e in ctx.published_events
        )
        failed_events = [
            e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED
        ]
        assert len(failed_events) == 1
        assert failed_events[0].payload["failed_stage"] == "FailStage"

    def test_pipeline_failed_contains_error_details(self) -> None:
        registry = HandlerRegistry()

        class FailingHandler:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.REPOSITORY_LOADED

            @property
            def handler_id(self) -> str:
                return "fail"

            @property
            def stage_name(self) -> str:
                return "FailStage"

            def handle(self, event):
                raise StageError("FailStage", "something broke")

        registry.register(FailingHandler())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        failed = next(
            e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED
        )
        assert failed.publisher == "pipeline_engine"
        assert "FailStage" in failed.payload["failed_stage"]

    def test_each_execution_has_unique_id(self) -> None:
        registry = HandlerRegistry()
        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "h1", "S1"))
        engine = PipelineEngine(registry)
        ctx1 = engine.run(PipelineContext())
        ctx2 = engine.run(PipelineContext())
        assert ctx1.execution_id != ctx2.execution_id

    def test_diagnostics_collected_per_stage(self) -> None:
        registry = HandlerRegistry()
        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "h1", "RepoStage"))
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert ctx.diagnostics is not None
        assert "RepoStage" in ctx.diagnostics.stage_timings
        timing = ctx.diagnostics.stage_timings["RepoStage"]
        assert timing.status.value == "completed"
        assert timing.duration_ms is not None

    def test_raises_pipeline_error_when_no_handlers_registered(self) -> None:
        registry = HandlerRegistry()
        engine = PipelineEngine(registry)
        with pytest.raises(PipelineError, match="No plugins installed"):
            engine.run(PipelineContext())


class CapturingHandler:
    def __init__(self, event_type: EventType, handler_id: str, stage_name: str) -> None:
        self._event_type = event_type
        self._handler_id = handler_id
        self._stage_name = stage_name
        self.captured_events: list = []

    @property
    def handled_event_type(self) -> EventType:
        return self._event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event):
        self.captured_events.append(event)
        return event.context


class SimpleHandler:
    def __init__(self, event_type: EventType, handler_id: str, stage_name: str) -> None:
        self._event_type = event_type
        self._handler_id = handler_id
        self._stage_name = stage_name

    @property
    def handled_event_type(self) -> EventType:
        return self._event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event):
        return event.context


from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from structlog.testing import capture_logs

from specmetrics.kernel.diagnostics import (
    Diagnostics,
    StageStatus,
    StageTiming,
)
from specmetrics.kernel.diagnostics import (
    StageError as StageErrorRecord,
)
from specmetrics.kernel.pipeline_engine import (
    _collect_spec_docs,
    _finish_diagnostics,
    _mark_timing,
)
from specmetrics.kernel.validation.models import BatchReport
from specmetrics.kernel.validation.pipeline import ValidationPipeline


def _make_engine(event_type: EventType, stage_name: str = "S1", handler_id: str = "h1"):
    registry = HandlerRegistry()
    registry.register(SimpleHandler(event_type, handler_id, stage_name))
    return PipelineEngine(registry)


class _ObservingHandler:
    def __init__(self, event_type: EventType, stage_name: str, sink: dict) -> None:
        self._event_type = event_type
        self._stage_name = stage_name
        self._sink = sink

    @property
    def handled_event_type(self) -> EventType:
        return self._event_type

    @property
    def handler_id(self) -> str:
        return "observer"

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event):
        self._sink.setdefault("publishers", []).append(event.publisher)
        timing = event.context.diagnostics.stage_timings[self._stage_name]
        self._sink["status_during_publish"] = timing.status
        return event.context


class _FailingHandler:
    def __init__(self, event_type: EventType, stage_name: str = "FailStage") -> None:
        self._event_type = event_type
        self._stage_name = stage_name

    @property
    def handled_event_type(self) -> EventType:
        return self._event_type

    @property
    def handler_id(self) -> str:
        return "fail"

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event):
        raise StageError(self._stage_name, "boom")


def test_mark_timing_scales_seconds_to_milliseconds() -> None:
    """Kills _mark_timing__mutmut_6 (``* 1000`` -> ``/ 1000``) and _mark_timing__mutmut_8 (``* 1000`` -> ``* 1001``)."""
    timing = StageTiming(
        stage_name="s", started_at=datetime.now(UTC) - timedelta(seconds=2)
    )
    _mark_timing(timing, StageStatus.COMPLETED)
    assert timing.duration_ms == 2000


def test_finish_diagnostics_computes_total_duration_ms() -> None:
    """Kills _finish_diagnostics__mutmut_5 (``total_seconds()`` -> ``total_seconds() / 1000``)."""
    diag = Diagnostics(started_at=datetime.now(UTC) - timedelta(seconds=2))
    _finish_diagnostics(diag)
    assert diag.total_duration_ms == 2000


def test_finalize_run_completed_event_metadata() -> None:
    """Kills _finalize_run__mutmut_3/10/11 (publisher), _finalize_run__mutmut_4 (payload), _finalize_run__mutmut_5 (context)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    ctx = engine.run(PipelineContext())
    completed = next(
        e for e in ctx.published_events if e.event_type == EventType.PIPELINE_COMPLETED
    )
    assert completed.publisher == "pipeline_engine"
    assert completed.payload == {}
    assert completed.context is not None
    assert completed.context.execution_id == ctx.execution_id


def test_run_publishes_events_with_empty_payload() -> None:
    """Kills PipelineEngine::run__mutmut_47 (``payload={}`` -> ``payload=None``) and _finalize_run__mutmut_4 (``payload={}`` -> ``payload=None``)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    ctx = engine.run(PipelineContext())
    assert ctx.published_events
    assert all(e.payload == {} for e in ctx.published_events)


def test_finalize_run_logs_execution_id_and_duration() -> None:
    """Kills _finalize_run__mutmut_22/25/29 (execution_id) and _finalize_run__mutmut_23/26 (duration_ms)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    with capture_logs() as logs:
        ctx = engine.run(PipelineContext())
    entry = next(l for l in logs if l["event"] == "pipeline_completed")
    assert entry["execution_id"] == str(ctx.execution_id)
    assert "duration_ms" in entry
    assert entry["duration_ms"] == ctx.diagnostics.total_duration_ms


def test_init_defaults_to_validation_pipeline() -> None:
    """Kills PipelineEngine::__init____mutmut_4 (``or ValidationPipeline()`` -> ``None``) and __init____mutmut_5 (``or`` -> ``and``)."""
    engine = PipelineEngine(HandlerRegistry())
    assert engine._validation_pipeline is not None


def test_init_uses_provided_validation_pipeline() -> None:
    """Kills PipelineEngine::__init____mutmut_5 (``validation_pipeline or`` -> ``validation_pipeline and``)."""
    vp = ValidationPipeline()
    engine = PipelineEngine(HandlerRegistry(), validation_pipeline=vp)
    assert engine._validation_pipeline is vp


def test_run_logs_pipeline_started() -> None:
    """Kills PipelineEngine::run__mutmut_18 (``logger.info("pipeline_started", ...)`` -> ``logger.info(None, ...)``)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    with capture_logs() as logs:
        engine.run(PipelineContext())
    assert any(l["event"] == "pipeline_started" for l in logs)


def test_run_logs_stage_skipped_for_unregistered_types() -> None:
    """Kills PipelineEngine::run__mutmut_26 (``logger.debug("stage_skipped", ...)`` -> ``logger.debug(None, ...)``)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    with capture_logs() as logs:
        engine.run(PipelineContext())
    skipped = [l for l in logs if l["event"] == "stage_skipped"]
    assert any(l["event_type"] == EventType.DOCUMENTS_DISCOVERED.value for l in skipped)


def test_stage_timing_records_stage_name() -> None:
    """Kills PipelineEngine::run__mutmut_36 (``stage_name=stage_name`` -> ``stage_name=None``)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED, stage_name="RepoStage")
    ctx = engine.run(PipelineContext())
    assert ctx.diagnostics.stage_timings["RepoStage"].stage_name == "RepoStage"


def test_stage_timing_is_running_during_publication() -> None:
    """Kills PipelineEngine::run__mutmut_37 (``status=StageStatus.RUNNING`` -> ``status=None``) and run__mutmut_40 (argument deletion)."""
    sink: dict = {}
    registry = HandlerRegistry()
    registry.register(_ObservingHandler(EventType.REPOSITORY_LOADED, "Obs", sink))
    engine = PipelineEngine(registry)
    engine.run(PipelineContext())
    assert sink["status_during_publish"] == StageStatus.RUNNING


def test_repository_loaded_publisher_is_pipeline_engine() -> None:
    """Kills PipelineEngine::run__mutmut_46/53/54 (publisher literal) and run__mutmut_55 (``if event_type`` -> ``if event_type not in (...``)."""
    sink: dict = {}
    registry = HandlerRegistry()
    registry.register(
        _ObservingHandler(EventType.REPOSITORY_LOADED, "CustomRepo", sink)
    )
    engine = PipelineEngine(registry)
    engine.run(PipelineContext())
    assert sink["publishers"] == ["pipeline_engine"]


def test_other_stage_publisher_is_stage_name() -> None:
    """Kills PipelineEngine::run__mutmut_55 (``if event_type`` -> ``if event_type not in (...``)."""
    sink: dict = {}
    registry = HandlerRegistry()
    registry.register(_ObservingHandler(EventType.DOCUMENTS_DISCOVERED, "Discover", sink))
    engine = PipelineEngine(registry)
    engine.run(PipelineContext())
    assert sink["publishers"] == ["Discover"]


def _spec_md_docs(tmpdir: str) -> list[Path]:
    spec_path = Path(tmpdir) / "spec.md"
    spec_path.write_text("# Spec", encoding="utf-8")
    other_path = Path(tmpdir) / "other.md"
    other_path.write_text("other", encoding="utf-8")
    return [spec_path, other_path]


def _engine_with_validated_handler_and_spy(tmpdir: str):
    engine = _make_engine(EventType.DOCUMENTS_VALIDATED, stage_name="Val")
    calls: list = []
    engine._validation_pipeline.run_batch = lambda paths, mode="all": (
        calls.append(list(paths)),
        BatchReport(
            reports=[],
            total_documents=0,
            passed_documents=0,
            failed_documents=0,
            duration_ms=0,
        ),
    )[1]
    return engine, calls


def test_document_validation_collects_spec_docs_from_adapter_result() -> None:
    """Kills _run_document_validation__mutmut_4..12 (doc_paths computation) and mutmut_14/15 (run_batch result)."""
    with TemporaryDirectory() as tmpdir:
        spec_path, other_path = _spec_md_docs(tmpdir)
        engine, calls = _engine_with_validated_handler_and_spy(tmpdir)
        ctx = PipelineContext(
            adapter_result={
                "documents": [{"path": str(spec_path)}, {"path": str(other_path)}]
            }
        )
        engine.run(ctx)
        assert calls == [[spec_path]]


def test_document_validation_runs_for_validated_event() -> None:
    """Kills _run_document_validation__mutmut_2 (``!=`` -> ``==``) and mutmut_56/57 (None substituted call args)."""
    with TemporaryDirectory() as tmpdir:
        spec_path, _ = _spec_md_docs(tmpdir)
        engine, calls = _engine_with_validated_handler_and_spy(tmpdir)
        ctx = PipelineContext(adapter_result={"documents": [{"path": str(spec_path)}]})
        engine.run(ctx)
        assert len(calls) == 1


def test_document_validation_skipped_for_other_event_types() -> None:
    """Kills _run_document_validation__mutmut_1 (added ``and self._validation_pipeline is None``)."""
    with TemporaryDirectory() as tmpdir:
        spec_path, _ = _spec_md_docs(tmpdir)
        engine = _make_engine(EventType.REPOSITORY_LOADED)
        calls: list = []
        engine._validation_pipeline.run_batch = lambda paths, mode="all": (
            calls.append(list(paths)),
            BatchReport(
                reports=[],
                total_documents=0,
                passed_documents=0,
                failed_documents=0,
                duration_ms=0,
            ),
        )[1]
        ctx = PipelineContext(adapter_result={"documents": [{"path": str(spec_path)}]})
        engine.run(ctx)
        assert calls == []


def test_document_validation_skipped_without_documents() -> None:
    """Kills _run_document_validation__mutmut_13 (``if not doc_paths`` -> ``if doc_paths``)."""
    engine = _make_engine(EventType.DOCUMENTS_VALIDATED)
    calls: list = []
    engine._validation_pipeline.run_batch = lambda paths, mode="all": (
        calls.append(list(paths)),
        BatchReport(
            reports=[],
            total_documents=0,
            passed_documents=0,
            failed_documents=0,
            duration_ms=0,
        ),
    )[1]
    engine.run(PipelineContext())
    assert calls == []


def test_document_validation_logs_failures() -> None:
    """Kills _run_document_validation__mutmut_17 (``> 0`` -> ``> 1``), mutmut_19/28 (execution_id), mutmut_22 (event name), mutmut_20/24 (failed_documents), mutmut_21/25 (total)."""
    with TemporaryDirectory() as tmpdir:
        spec_path, _ = _spec_md_docs(tmpdir)
        engine = _make_engine(EventType.DOCUMENTS_VALIDATED)
        engine._validation_pipeline.run_batch = lambda paths, mode="all": BatchReport(
            reports=[],
            total_documents=2,
            passed_documents=1,
            failed_documents=1,
            duration_ms=0,
        )
        ctx = PipelineContext(adapter_result={"documents": [{"path": str(spec_path)}]})
        with capture_logs() as logs:
            engine.run(ctx)
        entry = next(l for l in logs if l["event"] == "document_validation_failed")
        assert entry["execution_id"] == str(ctx.execution_id)
        assert entry["failed_documents"] == 1
        assert entry["total"] == 2


def test_document_validation_does_not_log_when_all_pass() -> None:
    """Kills _run_document_validation__mutmut_16 (``> 0`` -> ``>= 0``)."""
    with TemporaryDirectory() as tmpdir:
        spec_path, _ = _spec_md_docs(tmpdir)
        engine = _make_engine(EventType.DOCUMENTS_VALIDATED)
        engine._validation_pipeline.run_batch = lambda paths, mode="all": BatchReport(
            reports=[],
            total_documents=1,
            passed_documents=1,
            failed_documents=0,
            duration_ms=0,
        )
        ctx = PipelineContext(adapter_result={"documents": [{"path": str(spec_path)}]})
        with capture_logs() as logs:
            engine.run(ctx)
        assert not any(l["event"] == "document_validation_failed" for l in logs)


def test_fail_stage_marks_timing_failed_and_records_error() -> None:
    """Kills _fail_stage__mutmut_2 (status), mutmut_5 (StageErrorRecord -> None), mutmut_7/14/18/19/20 (message), mutmut_8/21 (exception_type), mutmut_9/22 (timestamp)."""
    registry = HandlerRegistry()
    registry.register(_FailingHandler(EventType.REPOSITORY_LOADED))
    engine = PipelineEngine(registry)
    ctx = engine.run(PipelineContext())
    timing = ctx.diagnostics.stage_timings["FailStage"]
    assert timing.status == StageStatus.FAILED
    assert len(ctx.diagnostics.errors) == 1
    err = ctx.diagnostics.errors[0]
    assert isinstance(err, StageErrorRecord)
    assert err.stage_name == "FailStage"
    assert err.message == "boom"
    assert err.exception_type == "StageError"
    assert err.timestamp is not None
    assert err.timestamp.tzinfo == UTC


def test_fail_stage_event_payload_and_context() -> None:
    """Kills _fail_stage__mutmut_28 (``context=ctx`` -> ``context=None``), mutmut_37/38 (payload key), mutmut_39 (``str(exc)`` -> ``str(None)``), and run__mutmut_77 (``exc`` -> ``None``)."""
    registry = HandlerRegistry()
    registry.register(_FailingHandler(EventType.REPOSITORY_LOADED))
    engine = PipelineEngine(registry)
    ctx = engine.run(PipelineContext())
    failed = next(
        e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED
    )
    assert failed.context is not None
    assert failed.publisher == "pipeline_engine"
    assert failed.payload == {
        "failed_stage": "FailStage",
        "error_message": "('FailStage', 'boom')",
    }


def test_fail_stage_logs_failure_details() -> None:
    """Kills _fail_stage__mutmut_49/53/58 (execution_id), mutmut_50/54 (failed_stage), mutmut_51/55/59 (error)."""
    registry = HandlerRegistry()
    registry.register(_FailingHandler(EventType.REPOSITORY_LOADED))
    engine = PipelineEngine(registry)
    with capture_logs() as logs:
        ctx = engine.run(PipelineContext())
    entry = next(l for l in logs if l["event"] == "pipeline_failed")
    assert entry["execution_id"] == str(ctx.execution_id)
    assert entry["failed_stage"] == "FailStage"
    assert entry["error"] == "('FailStage', 'boom')"


def test_fail_stage_uses_str_for_exception_without_message() -> None:
    """Kills _fail_stage__mutmut_20 (``str(exc)`` -> ``str(None)``) and mutmut_7 (``message=None``)."""
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    timing = StageTiming(stage_name="S", started_at=datetime.now(UTC))
    diag = Diagnostics(started_at=datetime.now(UTC))
    engine._fail_stage(
        PipelineContext(), "S", timing, ValueError("plain error"), diag
    )
    assert diag.errors[0].message == "plain error"
    assert diag.errors[0].exception_type == "ValueError"


def test_build_context_preserves_source_fields() -> None:
    """Kills PipelineEngine::_build_context__mutmut_3..20 (per-field None / deletion substitutions)."""
    exec_id = uuid4()
    source = PipelineContext(
        execution_id=exec_id,
        metadata={"k": "v"},
        repository="repo",
        adapter_result={"a": 1},
        extraction_result={"e": 1},
        evidence_graph={"g": 1},
        canonical_model={"c": 1},
        measurement_result={"m": 1},
        exported_files=["f"],
    )
    engine = _make_engine(EventType.REPOSITORY_LOADED)
    ctx = engine.run(source)
    assert ctx.execution_id == exec_id
    assert ctx.metadata == {"k": "v"}
    assert ctx.repository == "repo"
    assert ctx.adapter_result == {"a": 1}
    assert ctx.extraction_result == {"e": 1}
    assert ctx.evidence_graph == {"g": 1}
    assert ctx.canonical_model == {"c": 1}
    assert ctx.measurement_result == {"m": 1}
    assert ctx.exported_files == ["f"]


def test_collect_spec_docs_filters_only_spec_md() -> None:
    """Kills PipelineEngine::_run_document_validation__mutmut_11/12 (attribute name ``adapter_result`` changed)."""
    docs = [{"path": "/x/spec.md"}, {"path": "/x/notes.md"}]
    paths = _collect_spec_docs({"documents": docs})
    assert paths == [Path("/x/spec.md")]
