from __future__ import annotations

from specmetrics.kernel.csm.builder import CsmBuilderStage
from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType


def create_csm_builder_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="csm_builder_stage",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,),
        handler_factory=lambda: CsmBuilderStage(),
        name="Canonical Specification Model Builder",
        description="Builds a canonical specification model from the evidence graph",
        version="0.1.0",
    )
