from specmetrics.kernel import (
    EventType,
    HandlerRegistry,
    PipelineContext,
    PipelineEngine,
    StageError,
)


class TestPipelineIntegration:
    def test_pipeline_with_two_stages_executes_in_order(self) -> None:
        registry = HandlerRegistry()
        order: list[str] = []

        class StageA:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.REPOSITORY_LOADED

            @property
            def handler_id(self) -> str:
                return "stage_a"

            @property
            def stage_name(self) -> str:
                return "StageA"

            def handle(self, event):
                order.append("A")
                return event.context

        class StageB:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.DOCUMENTS_DISCOVERED

            @property
            def handler_id(self) -> str:
                return "stage_b"

            @property
            def stage_name(self) -> str:
                return "StageB"

            def handle(self, event):
                order.append("B")
                return event.context

        registry.register(StageA())
        registry.register(StageB())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())

        assert order == ["A", "B"]
        assert any(
            e.event_type == EventType.PIPELINE_COMPLETED for e in ctx.published_events
        )

    def test_pipeline_with_failing_stage_halts_before_downstream(self) -> None:
        registry = HandlerRegistry()
        downstream_executed = False

        class FailingStage:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.REPOSITORY_LOADED

            @property
            def handler_id(self) -> str:
                return "failing"

            @property
            def stage_name(self) -> str:
                return "FailingStage"

            def handle(self, event):
                raise StageError("FailingStage", "intentional failure")

        class DownstreamStage:
            @property
            def handled_event_type(self) -> EventType:
                return EventType.DOCUMENTS_DISCOVERED

            @property
            def handler_id(self) -> str:
                return "downstream"

            @property
            def stage_name(self) -> str:
                return "Downstream"

            def handle(self, event):
                nonlocal downstream_executed
                downstream_executed = True
                return event.context

        registry.register(FailingStage())
        registry.register(DownstreamStage())
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())

        assert not downstream_executed
        assert any(
            e.event_type == EventType.PIPELINE_FAILED for e in ctx.published_events
        )
        failed = [
            e for e in ctx.published_events if e.event_type == EventType.PIPELINE_FAILED
        ][0]
        assert "FailingStage" in failed.payload["failed_stage"]

    def test_pipeline_context_contains_complete_event_log(self) -> None:
        registry = HandlerRegistry()

        class SimpleHandler:
            def __init__(self, et: EventType, hid: str, sn: str):
                self._et = et
                self._hid = hid
                self._sn = sn

            @property
            def handled_event_type(self):
                return self._et

            @property
            def handler_id(self):
                return self._hid

            @property
            def stage_name(self):
                return self._sn

            def handle(self, event):
                return event.context

        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "a", "S1"))
        engine = PipelineEngine(registry)
        ctx = engine.run(PipelineContext())

        published_types = [
            e.event_type for e in ctx.published_events if hasattr(e, "event_type")
        ]
        assert EventType.REPOSITORY_LOADED in published_types
        assert EventType.PIPELINE_COMPLETED in published_types
        assert ctx.diagnostics is not None
        assert ctx.diagnostics.total_duration_ms is not None

    def test_deterministic_pipeline_execution(self) -> None:
        registry = HandlerRegistry()

        class SimpleHandler:
            def __init__(self, et: EventType, hid: str, sn: str):
                self._et = et
                self._hid = hid
                self._sn = sn

            @property
            def handled_event_type(self):
                return self._et

            @property
            def handler_id(self):
                return self._hid

            @property
            def stage_name(self):
                return self._sn

            def handle(self, event):
                return event.context

        registry.register(SimpleHandler(EventType.REPOSITORY_LOADED, "a", "S1"))
        engine = PipelineEngine(registry)

        result1 = engine.run(PipelineContext())
        result2 = engine.run(PipelineContext())

        types1 = [
            e.event_type for e in result1.published_events if hasattr(e, "event_type")
        ]
        types2 = [
            e.event_type for e in result2.published_events if hasattr(e, "event_type")
        ]
        assert types1 == types2
