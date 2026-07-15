import pytest

from specmetrics.kernel import EventType, HandlerNotFoundError, HandlerRegistry, PipelineContext, PipelineEvent


class TestHandlerRegistry:
    def test_raises_handler_not_found_for_unregistered_type(self) -> None:
        registry = HandlerRegistry()
        with pytest.raises(HandlerNotFoundError) as exc:
            registry.resolve(EventType.REPOSITORY_LOADED)
        assert "repository_loaded" in str(exc.value)

    def test_register_and_resolve_handler(self) -> None:
        registry = HandlerRegistry()
        handler = FakeHandler(EventType.REPOSITORY_LOADED, "test", "Stage")
        registry.register(handler)
        resolved = registry.resolve(EventType.REPOSITORY_LOADED)
        assert resolved is handler

    def test_registered_types_returns_correct_set(self) -> None:
        registry = HandlerRegistry()
        h1 = FakeHandler(EventType.REPOSITORY_LOADED, "h1", "S1")
        h2 = FakeHandler(EventType.DOCUMENTS_DISCOVERED, "h2", "S2")
        registry.register(h1)
        registry.register(h2)
        assert registry.registered_types == {EventType.REPOSITORY_LOADED, EventType.DOCUMENTS_DISCOVERED}


class FakeHandler:
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

    def handle(self, event: PipelineEvent) -> PipelineContext:
        return event.context
