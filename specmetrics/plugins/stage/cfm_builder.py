from __future__ import annotations

from specmetrics.kernel.cfm.builder import CfmBuilderStage
from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType


def create_cfm_builder_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="cfm_builder_stage",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.EVIDENCE_GRAPH_BUILT,),
        handler_factory=lambda: CfmBuilderStage(),
        name="Canonical Functional Model Builder",
        description="Builds a canonical functional model from the evidence graph",
        version="0.1.0",
    )
