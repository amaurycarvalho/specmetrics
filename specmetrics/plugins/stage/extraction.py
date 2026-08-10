"""Stage metadata for the semantic extraction stage."""

from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.extraction_registry import ProviderRouter
from specmetrics.kernel.extraction_stage import ExtractionStage
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType
from specmetrics.plugins.semantic.llm_provider import LLMExtractionProvider


def create_extraction_metadata() -> PluginMetadata:
    """Create metadata for the extraction stage."""
    router = ProviderRouter()
    router.register(LLMExtractionProvider(), "llm-provider")
    return PluginMetadata(
        id="extraction_stage",
        api_version="0.1.0",
        plugin_type=PluginType.SEMANTIC,
        handled_event_types=(EventType.DOCUMENTS_DISCOVERED,),
        handler_factory=lambda: ExtractionStage(router=router),
        name="Semantic Extraction Stage",
        description="Routes specification documents to extraction providers and consolidates results",
        version="0.1.0",
    )
