import pytest

from specmetrics.kernel import (
    EventType,
    HandlerNotFoundError,
    HandlerRegistry,
    PipelineContext,
    PipelineEvent,
    StageError,
)
from specmetrics.kernel.event_bus import EventBus


class TestEventBus:
    def test_delivers_event_to_registered_handler(self) -> None:
        registry = HandlerRegistry()
        handler = FakeHandler(EventType.REPOSITORY_LOADED, "test_handler", "Test Stage")
        registry.register(handler)
        bus = EventBus(registry)
        event = PipelineEvent(
            event_type=EventType.REPOSITORY_LOADED,
            publisher="test",
            payload={},
            context=PipelineContext(),
        )
        result = bus.publish(event)
        assert handler.called
        assert result is not None

    def test_raises_error_for_unregistered_type(self) -> None:
        registry = HandlerRegistry()
        bus = EventBus(registry)
        event = PipelineEvent(
            event_type=EventType.REPOSITORY_LOADED,
            publisher="test",
            payload={},
            context=PipelineContext(),
        )
        with pytest.raises(HandlerNotFoundError):
            bus.publish(event)

    def test_wraps_non_stage_error_into_stage_error(self) -> None:
        registry = HandlerRegistry()
        handler = ExceptionRaisingHandler(
            EventType.REPOSITORY_LOADED, "raise_handler", "RaiseStage"
        )
        registry.register(handler)
        bus = EventBus(registry)
        event = PipelineEvent(
            event_type=EventType.REPOSITORY_LOADED,
            publisher="test",
            payload={},
            context=PipelineContext(),
        )
        with pytest.raises(StageError) as exc:
            bus.publish(event)
        assert exc.value.stage_name == "RaiseStage"
        assert "something unexpected" in exc.value.message

    def test_preserves_event_order_across_multiple_publishes(self) -> None:
        registry = HandlerRegistry()
        h1 = FakeHandler(EventType.REPOSITORY_LOADED, "h1", "Stage 1")
        h2 = FakeHandler(EventType.DOCUMENTS_DISCOVERED, "h2", "Stage 2")
        registry.register(h1)
        registry.register(h2)
        bus = EventBus(registry)
        e1 = PipelineEvent(EventType.REPOSITORY_LOADED, "pub", {}, PipelineContext())
        e2 = PipelineEvent(EventType.DOCUMENTS_DISCOVERED, "pub", {}, PipelineContext())
        bus.publish(e1)
        bus.publish(e2)
        assert h1.call_count == 1
        assert h2.call_count == 1
        assert h1.last_event is e1
        assert h2.last_event is e2


class ExceptionRaisingHandler:
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

    def handle(self, event: PipelineEvent) -> PipelineContext:
        raise ValueError("something unexpected")


class FakeHandler:
    def __init__(self, event_type: EventType, handler_id: str, stage_name: str) -> None:
        self._event_type = event_type
        self._handler_id = handler_id
        self._stage_name = stage_name
        self.called = False
        self.call_count = 0
        self.last_event = None

    @property
    def handled_event_type(self) -> EventType:
        return self._event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event: PipelineEvent) -> PipelineContext:
        self.called = True
        self.call_count += 1
        self.last_event = event
        return event.context
