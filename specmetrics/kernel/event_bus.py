"""Event bus that dispatches pipeline events to registered handlers."""

from __future__ import annotations

from typing import Self

import structlog

from .events import PipelineEvent
from .exceptions import StageError
from .handler_registry import HandlerRegistry
from .pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


class EventBus:
    """Dispatches pipeline events to registered handlers in order."""

    def __init__(self: Self, registry: HandlerRegistry) -> None:
        """Initialize the event bus with the given handler registry."""
        self._registry = registry

    def publish(self: Self, event: PipelineEvent) -> PipelineContext:
        """Publish an event to all handlers and return the resulting context."""
        handlers = self._registry.resolve_all(event.event_type)
        if not handlers:
            handler = self._registry.resolve(event.event_type)
            handlers = [handler]

        ctx = event.context
        for i, handler in enumerate(handlers):
            logger.debug(
                "event_published",
                event_type=event.event_type.value,
                handler_id=handler.handler_id,
            )
            try:
                if i == 0:
                    ctx = handler.handle(event)
                else:
                    slot_event = PipelineEvent(
                        event_type=event.event_type,
                        publisher=handler.handler_id,
                        payload=event.payload,
                        context=ctx,
                    )
                    ctx = handler.handle(slot_event)
            except StageError:
                raise
            except Exception as exc:
                raise StageError(
                    stage_name=handler.stage_name,
                    message=str(exc),
                ) from exc
        return ctx
