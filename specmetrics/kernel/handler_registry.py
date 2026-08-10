"""Registry for event handlers and the event handler protocol."""

from __future__ import annotations

from typing import Protocol, Self

from .events import EventType, PipelineEvent
from .exceptions import HandlerNotFoundError
from .pipeline_context import PipelineContext


class EventHandler(Protocol):
    """Protocol for handlers that process pipeline events."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type handled by this handler."""
        ...

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        ...

    @property
    def stage_name(self: Self) -> str:
        """Return the stage name this handler belongs to."""
        ...

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Handle the given event and return the resulting pipeline context."""
        ...


class HandlerRegistry:
    """Registry mapping event types to their registered handlers."""

    def __init__(self: Self) -> None:
        """Initialize an empty handler registry."""
        self._handlers: dict[EventType, list[EventHandler]] = {}

    def register(self: Self, handler: EventHandler) -> None:
        """Register a handler for the event type it declares."""
        et = handler.handled_event_type
        if et not in self._handlers:
            self._handlers[et] = []
        self._handlers[et].append(handler)

    def resolve(self: Self, event_type: EventType) -> EventHandler:
        """Return the first handler registered for the given event type."""
        handlers = self._handlers.get(event_type)
        if not handlers:
            raise HandlerNotFoundError(event_type.value)
        return handlers[0]

    def resolve_all(self: Self, event_type: EventType) -> list[EventHandler]:
        """Return all handlers registered for the given event type."""
        return self._handlers.get(event_type, [])

    @property
    def registered_types(self: Self) -> set[EventType]:
        """Return the set of event types with registered handlers."""
        return set(self._handlers.keys())
