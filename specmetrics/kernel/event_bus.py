from __future__ import annotations

import structlog

from .events import PipelineEvent
from .exceptions import StageError
from .handler_registry import HandlerRegistry
from .pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


class EventBus:
    def __init__(self, registry: HandlerRegistry) -> None:
        self._registry = registry

    def publish(self, event: PipelineEvent) -> PipelineContext:
        handler = self._registry.resolve(event.event_type)
        logger.debug(
            "event_published",
            event_type=event.event_type.value,
            handler_id=handler.handler_id,
        )
        try:
            next_context = handler.handle(event)
        except StageError:
            raise
        except Exception as exc:
            raise StageError(
                stage_name=handler.stage_name,
                message=str(exc),
            ) from exc
        return next_context
