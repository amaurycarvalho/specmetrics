"""Bridges that acknowledge OpenSpec adapter pipeline events."""

from __future__ import annotations

from typing import Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

logger = structlog.get_logger(__name__)


class DocumentsValidatedHandler:
    """Handler that acknowledges and logs document validation results."""

    def __init__(self: Self) -> None:
        """Initialize the handler."""
        self._handled_event_type = EventType.DOCUMENTS_VALIDATED
        self._handler_id = "documents_validated_bridge"
        self._stage_name = "documents_validated"

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the handled event type."""
        return self._handled_event_type

    @property
    def handler_id(self: Self) -> str:
        """Return the handler identifier."""
        return self._handler_id

    @property
    def stage_name(self: Self) -> str:
        """Return the stage name."""
        return self._stage_name

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Handle the event and return the updated pipeline context."""
        context = event.context
        adapter_ctx = getattr(context, "adapter_result", None) or {}
        documents = adapter_ctx.get("documents", [])
        count = len(documents)
        logger.info(
            "documents_validated",
            count=count,
            execution_id=str(context.execution_id),
        )
        return context.with_stage_output(
            field_name="adapter_result",
            value={**adapter_ctx, "validated": True, "document_count": count},
        )


class CanonicalModelBuiltHandler:
    """Handler that acknowledges canonical model build events and logs results."""

    def __init__(self: Self) -> None:
        """Initialize the handler."""
        self._handled_event_type = EventType.CANONICAL_MODEL_BUILT
        self._handler_id = "canonical_model_built_bridge"
        self._stage_name = "canonical_model_built"

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the handled event type."""
        return self._handled_event_type

    @property
    def handler_id(self: Self) -> str:
        """Return the handler identifier."""
        return self._handler_id

    @property
    def stage_name(self: Self) -> str:
        """Return the stage name."""
        return self._stage_name

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Handle the event and return the pipeline context."""
        context = event.context
        cfm = getattr(context, "canonical_model", None)
        element_counts = {}
        if isinstance(cfm, CanonicalFunctionalModel):
            element_counts = cfm.metadata.element_counts
        elif isinstance(cfm, dict):
            element_counts = cfm.get("element_counts", {})
        logger.info(
            "canonical_model_built_received",
            element_counts=element_counts,
            execution_id=str(context.execution_id),
        )
        return context


def create_documents_validated_metadata() -> PluginMetadata:
    """Create metadata for the documents validated bridge."""
    return PluginMetadata(
        id="documents_validated_bridge",
        api_version="0.1.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=(EventType.DOCUMENTS_VALIDATED,),
        handler_factory=lambda: DocumentsValidatedHandler(),
        name="Documents Validated Bridge",
        description="Acknowledges and logs document validation results",
        version="0.1.0",
    )


def create_canonical_model_built_metadata() -> PluginMetadata:
    """Create metadata for the canonical model built bridge."""
    return PluginMetadata(
        id="canonical_model_built_bridge",
        api_version="0.1.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=(EventType.CANONICAL_MODEL_BUILT,),
        handler_factory=lambda: CanonicalModelBuiltHandler(),
        name="Canonical Model Built Bridge",
        description="Acknowledges canonical model built event and logs results",
        version="0.1.0",
    )
