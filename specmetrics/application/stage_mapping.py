"""Stage/event mapping and event-order resolution for the pipeline orchestrator.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). These helpers translate between
application ``StageName`` values and Kernel ``EventType`` values, and resolve the
ordered list of events to execute for a given request.
"""

from __future__ import annotations

from specmetrics.application.enums import StageName
from specmetrics.kernel.events import EventType
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import CANONICAL_EVENT_ORDER

_STAGE_NAME_TO_EVENT: dict[StageName, EventType] = {
    StageName.DISCOVER: EventType.REPOSITORY_LOADED,
    StageName.EXTRACT: EventType.SEMANTIC_EXTRACTION_COMPLETED,
    StageName.GRAPH: EventType.EVIDENCE_GRAPH_BUILT,
    StageName.CSM: EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,
    StageName.CFM: EventType.CANONICAL_MODEL_BUILT,
    StageName.RULE: EventType.RULE_PACK_APPLIED,
    StageName.MEASURE: EventType.MEASUREMENT_COMPLETED,
    StageName.EXPORT: EventType.EXPORT_COMPLETED,
}

_STAGE_NAME_TO_HANDLER_NAMES: dict[str, list[str]] = {
    "discover": ["discovery"],
    "extract": ["semantic_extraction"],
    "graph": ["evidence_graph"],
    "csm": ["canonical_spec_model"],
    "cfm": ["canonical_model"],
    "rule": ["Rule Pack Engine"],
    "measure": [
        "FPA Measurement",
        "SFP Measurement",
        "SNAP Measurement",
        "Story Points Measurement",
        "Token Points Measurement",
        "Cognitive Points Measurement",
        "BCP Measurement",
    ],
    "export": [],
}


def _stage_name_from_event(event_type: EventType) -> str:
    for stage_name, et in _STAGE_NAME_TO_EVENT.items():
        if et == event_type:
            return stage_name.value
    return event_type.value


def _resolve_event_order(
    stages: list[StageName] | None,
    from_stage: StageName | None,
) -> list[EventType]:
    if stages is not None:
        return [_STAGE_NAME_TO_EVENT[s] for s in stages]
    if from_stage is not None:
        start_event = _STAGE_NAME_TO_EVENT[from_stage]
        started = False
        result: list[EventType] = []
        for et in CANONICAL_EVENT_ORDER:
            if et == start_event:
                started = True
            if started:
                result.append(et)
        return result
    return list(CANONICAL_EVENT_ORDER)


def detect_framework(ctx: PipelineContext) -> str:
    """Return the detected SDD framework name, or an empty string when unknown."""
    adapter_data = getattr(ctx, "adapter_result", None) or {}
    adapters = adapter_data.get("adapters_used", [])
    if "speckit-adapter" in adapters:
        return "speckit"
    if "openspec-adapter" in adapters:
        return "openspec"
    return ""