"""Stage that discovers specification documents via registered adapters."""

from __future__ import annotations

from typing import Self

import structlog

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

logger = structlog.get_logger(__name__)


class AdapterDiscoveryHandler:
    """Handler that discovers documents through the adapter registry."""

    def __init__(self: Self) -> None:
        """Initialize the handler."""
        self._handled_event_type = EventType.REPOSITORY_LOADED
        self._handler_id = "adapter_discovery"
        self._stage_name = "discovery"

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
        repo_path = getattr(context, "repository", None)
        if repo_path is None:
            logger.warning("no_repository_path")
            return context.with_stage_output("adapter_result", {"documents": []})

        metadata = context.metadata or {}
        adapter_registry = metadata.get("adapter_registry")
        if adapter_registry is None:
            logger.warning("no_adapter_registry")
            return context.with_stage_output("adapter_result", {"documents": []})

        scanned = adapter_registry.scan_all(repo_path)
        all_documents = []
        for docs in scanned.values():
            all_documents.extend(docs)

        logger.info(
            "adapter_discovery_complete",
            adapters=len(scanned),
            documents=len(all_documents),
        )

        return context.with_stage_output(
            "adapter_result",
            {"documents": all_documents, "adapters_used": list(scanned.keys())},
        )


def create_adapter_discovery_metadata() -> PluginMetadata:
    """Create metadata for the adapter discovery stage."""
    return PluginMetadata(
        id="adapter_discovery",
        api_version="0.1.0",
        plugin_type=PluginType.SEMANTIC,
        handled_event_types=(EventType.REPOSITORY_LOADED,),
        handler_factory=lambda: AdapterDiscoveryHandler(),
        name="Adapter Discovery Stage",
        description="Discovers specification documents via registered adapters",
        version="0.1.0",
    )
