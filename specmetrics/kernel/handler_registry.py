from __future__ import annotations

from typing import Protocol

from .events import EventType, PipelineEvent
from .exceptions import HandlerNotFoundError
from .pipeline_context import PipelineContext


class EventHandler(Protocol):
    @property
    def handled_event_type(self) -> EventType:
        ...

    @property
    def handler_id(self) -> str:
        ...

    @property
    def stage_name(self) -> str:
        ...

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ...


class HandlerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[EventType, EventHandler] = {}

    def register(self, handler: EventHandler) -> None:
        self._handlers[handler.handled_event_type] = handler

    def resolve(self, event_type: EventType) -> EventHandler:
        handler = self._handlers.get(event_type)
        if handler is None:
            raise HandlerNotFoundError(event_type.value)
        return handler

    @property
    def registered_types(self) -> set[EventType]:
        return set(self._handlers.keys())
