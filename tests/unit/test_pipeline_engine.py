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
        handler = CapturingHandler(EventType.REPOSITORY_LOADED, "repo_handler", "Repository")
        registry.register(handler)
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(e.event_type == EventType.REPOSITORY_LOADED for e in ctx.published_events)

    def test_invokes_handlers_in_canonical_order(self) -> None:
        registry = HandlerRegistry()
        order: list[str] = []

        class OrderHandler:
            def __init__(self, et: EventType, hid: str, sn: str) -> None:
                self._et = et
                self._hid = hid
                self._sn = sn
            @property
            def handled_event_type(self) -> EventType: return self._et
            @property
            def handler_id(self) -> str: return self._hid
            @property
            def stage_name(self) -> str: return self._sn
            def handle(self, event): order.append(self._sn); return event.context

        registry.register(OrderHandler(EventType.REPOSITORY_LOADED, "a", "A"))
        registry.register(OrderHandler(EventType.DOCUMENTS_DISCOVERED, "b", "B"))
        registry.register(OrderHandler(EventType.SEMANTIC_EXTRACTION_COMPLETED, "c", "C"))
        engine = PipelineEngine(registry)
        engine.run(PipelineContext())
        assert order == ["A", "B", "C"]

    def test_returns_pipeline_completed_on_success(self) -> None:
        registry = HandlerRegistry()
        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "h1", "S1"))
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(e.event_type == EventType.PIPELINE_COMPLETED for e in ctx.published_events)

    def test_stage_error_halts_pipeline(self) -> None:
        registry = HandlerRegistry()

        class FailingHandler:
            @property
            def handled_event_type(self) -> EventType: return EventType.REPOSITORY_LOADED
            @property
            def handler_id(self) -> str: return "fail"
            @property
            def stage_name(self) -> str: return "FailStage"
            def handle(self, event): raise StageError("FailStage", "intentional")

        registry.register(FailingHandler())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        assert any(e.event_type == EventType.PIPELINE_FAILED for e in ctx.published_events)
        failed_events = [e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED]
        assert len(failed_events) == 1
        assert failed_events[0].payload["failed_stage"] == "FailStage"

    def test_pipeline_failed_contains_error_details(self) -> None:
        registry = HandlerRegistry()

        class FailingHandler:
            @property
            def handled_event_type(self) -> EventType: return EventType.REPOSITORY_LOADED
            @property
            def handler_id(self) -> str: return "fail"
            @property
            def stage_name(self) -> str: return "FailStage"
            def handle(self, event): raise StageError("FailStage", "something broke")

        registry.register(FailingHandler())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())
        failed = [e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED][0]
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
    def handled_event_type(self) -> EventType: return self._event_type
    @property
    def handler_id(self) -> str: return self._handler_id
    @property
    def stage_name(self) -> str: return self._stage_name

    def handle(self, event):
        self.captured_events.append(event)
        return event.context


class SimpleHandler:
    def __init__(self, event_type: EventType, handler_id: str, stage_name: str) -> None:
        self._event_type = event_type
        self._handler_id = handler_id
        self._stage_name = stage_name

    @property
    def handled_event_type(self) -> EventType: return self._event_type
    @property
    def handler_id(self) -> str: return self._handler_id
    @property
    def stage_name(self) -> str: return self._stage_name

    def handle(self, event):
        return event.context
