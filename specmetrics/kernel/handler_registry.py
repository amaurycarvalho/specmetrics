from __future__ import annotations

from typing import Protocol

from .events import EventType, PipelineEvent
from .exceptions import HandlerNotFoundError
from .pipeline_context import PipelineContext


class EventHandler(Protocol):
    @property
    def handled_event_type(self) -> EventType: ...

    @property
    def handler_id(self) -> str: ...

    @property
    def stage_name(self) -> str: ...

    def handle(self, event: PipelineEvent) -> PipelineContext: ...


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def register(self, handler: EventHandler) -> None:
        et = handler.handled_event_type
        if et not in self._handlers:
            self._handlers[et] = []
        self._handlers[et].append(handler)

    def resolve(self, event_type: EventType) -> EventHandler:
        handlers = self._handlers.get(event_type)
        if not handlers:
            raise HandlerNotFoundError(event_type.value)
        return handlers[0]

    def resolve_all(self, event_type: EventType) -> list[EventHandler]:
        return self._handlers.get(event_type, [])

    @property
    def registered_types(self) -> set[EventType]:
        return set(self._handlers.keys())
