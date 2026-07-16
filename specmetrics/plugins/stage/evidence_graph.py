from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.evidence_graph_stage import EvidenceGraphStage
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType


def create_evidence_graph_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="evidence_graph_stage",
        api_version="0.1.0",
        plugin_type=PluginType.SEMANTIC,
        handled_event_types=(EventType.SEMANTIC_EXTRACTION_COMPLETED,),
        handler_factory=lambda: EvidenceGraphStage(),
        name="Evidence Graph Stage",
        description="Builds a provenance graph from extracted elements and persists it",
        version="0.1.0",
    )
