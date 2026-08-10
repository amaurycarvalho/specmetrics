"""Per-stage entity payload builders for pipeline results.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). Builds the truncated entity
payloads attached to each stage of a ``PipelineResult``.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from specmetrics.application.enums import StageName
from specmetrics.application.models import METRIC_NAME_MAP
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.events import EventType
from specmetrics.kernel.pipeline_context import PipelineContext

from .stage_mapping import _stage_name_from_event
from .truncation import _truncate_text


def _build_stage_entities(
    ctx: PipelineContext,
    event_order: list[EventType],
    export_path: Path | None,
) -> dict[str, list[dict]]:
    builders: dict[str, Callable[[PipelineContext], list[dict]]] = {
        "discover": _entities_for_discover,
        "extract": _entities_for_extract,
        "graph": _entities_for_graph,
        "csm": _entities_for_csm,
        "cfm": _entities_for_cfm,
        "rule": _entities_for_rule,
        "measure": _entities_for_measure,
        "export": lambda ctx: _entities_for_export(ctx, export_path),
    }

    entities: dict[str, list[dict]] = {}
    valid_stage_names = {s.value for s in StageName}

    for event_type in event_order:
        stage_name = _stage_name_from_event(event_type)
        if stage_name not in valid_stage_names:
            continue
        builder = builders.get(stage_name)
        if builder:
            entities[stage_name] = builder(ctx)

    return entities


def _entities_for_discover(ctx: PipelineContext) -> list[dict]:
    adapter_data = getattr(ctx, "adapter_result", None) or {}
    return [
        {
            "id": str(getattr(doc, "id", "")),
            "document_type": str(getattr(doc, "document_type", "")),
            "path": str(getattr(doc, "path", "")),
        }
        for doc in adapter_data.get("documents", [])
    ]


def _entities_for_extract(ctx: PipelineContext) -> list[dict]:
    extract_data = getattr(ctx, "extraction_result", None) or {}
    results_dict = extract_data.get("results", {})
    stage_entities: list[dict] = []

    for provider_result in results_dict.values():
        for elem in provider_result.get("elements", []):
            if isinstance(elem, dict):
                entry = _coerce_element_dict(elem)
            else:
                entry = _coerce_element_obj(elem)
            if not any(entry.get(k) for k in ("id", "type", "content")):
                continue
            stage_entities.append(entry)

    stage_entities.append(
        {
            "type": "documents_processed",
            "count": extract_data.get("documents_processed", 0),
        }
    )
    stage_entities.append(
        {
            "type": "documents_skipped",
            "count": extract_data.get("documents_skipped", 0),
        }
    )
    return stage_entities


def _coerce_element_dict(elem: dict) -> dict:
    evidence = elem.get("evidence")
    return {
        "id": str(elem.get("id", "")),
        "type": str(elem.get("type", "")),
        "content": _truncate_text(elem.get("content")),
        "confidence": float(elem.get("confidence", 0.0)),
        "evidence": _coerce_element_evidence(evidence) if evidence else {},
    }


def _coerce_element_obj(elem: object) -> dict:
    evidence = getattr(elem, "evidence", None)
    return {
        "id": str(getattr(elem, "id", "")),
        "type": str(getattr(elem, "type", "")),
        "content": _truncate_text(getattr(elem, "content", None)),
        "confidence": float(getattr(elem, "confidence", 0.0)),
        "evidence": _coerce_element_evidence(evidence) if evidence else {},
    }


def _coerce_element_evidence(evidence: object) -> dict:
    if isinstance(evidence, dict):
        return {
            "document_id": str(evidence.get("document_id", "")),
            "section_id": str(evidence.get("section_id", None)),
            "text": _truncate_text(evidence.get("text")),
        }
    return {
        "document_id": str(getattr(evidence, "document_id", "")),
        "section_id": str(getattr(evidence, "section_id", None)),
        "text": _truncate_text(getattr(evidence, "text", None)),
    }


def _entities_for_graph(ctx: PipelineContext) -> list[dict]:
    graph_data = getattr(ctx, "evidence_graph", None) or {}
    stage_entities: list[dict] = []
    if not isinstance(graph_data, dict):
        return stage_entities
    for node in graph_data.get("nodes", []):
        if isinstance(node, dict):
            stage_entities.append(
                {
                    "id": node.get("id", ""),
                    "node_type": node.get("node_type", ""),
                    "semantic_type": node.get("semantic_type"),
                    "document_id": node.get("document_id"),
                    "section_id": node.get("section_id"),
                    "text": _truncate_text(node.get("text")),
                }
            )
    stage_entities.append(
        {
            "node_type": "graph_summary",
            "edge_count": graph_data.get("edge_count", 0),
            "run_id": graph_data.get("run_id", ""),
        }
    )
    return stage_entities


def _entities_for_csm(ctx: PipelineContext) -> list[dict]:
    csm = getattr(ctx, "canonical_spec_model", None)
    stage_entities: list[dict] = []
    if not isinstance(csm, CanonicalSpecificationModel):
        return stage_entities
    category_map = {
        "specification_activity": csm.specification_activities,
        "decision": csm.decisions,
        "assumption": csm.assumptions,
        "constraint": csm.constraints,
        "risk": csm.risks,
        "open_question": csm.open_questions,
        "acceptance_criterion": csm.acceptance_criteria,
        "glossary_term": csm.glossary_terms,
        "reference": csm.references,
    }
    for cat_name, cat_dict in category_map.items():
        for element in cat_dict.values():
            dumped = element.model_dump(mode="json")
            dumped["type"] = cat_name
            if "description" in dumped:
                dumped["description"] = _truncate_text(dumped["description"])
            stage_entities.append(dumped)
    return stage_entities


def _entities_for_cfm(ctx: PipelineContext) -> list[dict]:
    cfm = getattr(ctx, "canonical_model", None)
    stage_entities: list[dict] = []
    if not isinstance(cfm, CanonicalFunctionalModel):
        return stage_entities
    category_map = {
        "actor": cfm.actors,
        "functional_process": cfm.functional_processes,
        "business_rule": cfm.business_rules,
        "data_group": cfm.data_groups,
        "operation": cfm.operations,
        "unclassified": cfm.unclassified,
    }
    for cat_name, cat_dict in category_map.items():
        for element in cat_dict.values():
            dumped = element.model_dump(mode="json")
            dumped["type"] = cat_name
            stage_entities.append(dumped)
    for rel in cfm.relationships:
        dumped = rel.model_dump(mode="json")
        dumped["type"] = "relationship"
        stage_entities.append(dumped)
    return stage_entities


def _entities_for_rule(ctx: PipelineContext) -> list[dict]:
    cfm = getattr(ctx, "canonical_model", None)
    stage_entities: list[dict] = []
    if not isinstance(cfm, CanonicalFunctionalModel):
        return stage_entities
    for rule_pack in getattr(cfm.metadata, "applied_rules", []):
        if isinstance(rule_pack, dict):
            stage_entities.append(
                {
                    "type": "applied_rule_pack",
                    "rule_pack_id": rule_pack.get("rule_pack_id", ""),
                    "rule_id": rule_pack.get("rule_id", ""),
                    "rule_type": rule_pack.get("rule_type", ""),
                    "methodology": rule_pack.get("methodology", ""),
                    "description": rule_pack.get("description", ""),
                }
            )
    stage_entities.append(
        {
            "type": "modification_summary",
            "entities_modified": sum(cfm.metadata.element_counts.values())
            if hasattr(cfm.metadata, "element_counts")
            else 0,
            "vaf_applied": getattr(cfm.metadata, "vaf", None),
        }
    )
    return stage_entities


def _entities_for_measure(ctx: PipelineContext) -> list[dict]:
    mr = getattr(ctx, "measurement_result", None) or {}
    stage_entities: list[dict] = []
    if not isinstance(mr, dict):
        return stage_entities
    key_map = {
        "function_points": ("fpa_total_function_points", "fpa_breakdown"),
        "simplified_function_points": ("sfp_total_sfp", None),
        "business_complexity_points": ("bcp_measured_items", None),
        "token_points": ("token_total_score", None),
        "cognitive_points": ("cognitive_raw_score", "cognitive_bloom_breakdown"),
        "story_points": ("storypoints_total_story_points", None),
        "snap": ("snap_total_snap", None),
        "tshirt": ("tshirt", "tshirt_breakdown"),
    }
    metric_name_to_cli = {v: k for k, v in METRIC_NAME_MAP.items()}
    for metric_name in list(METRIC_NAME_MAP.values()):
        stage_entities.append(
            _build_metric_entry(mr, metric_name, key_map, metric_name_to_cli)
        )
    return stage_entities


def _build_metric_entry(
    mr: dict[str, Any],
    metric_name: str,
    key_map: dict[str, tuple[str | None, str | None]],
    metric_name_to_cli: dict[str, str],
) -> dict:
    total_key, breakdown_key = key_map.get(metric_name, (None, None))
    total = mr.get(total_key, 0) if total_key else 0
    if metric_name in ("token_points", "cognitive_points"):
        total = round(total, 1)
    entry: dict = {
        "metric": metric_name,
        "total": total,
        "status": "completed",
        "duration_ms": 0,
    }
    if breakdown_key and breakdown_key in mr:
        entry["breakdown"] = _metric_breakdown(mr, metric_name, breakdown_key)
    cli_id = metric_name_to_cli.get(metric_name)
    if cli_id:
        warnings = _metric_warnings(mr, cli_id)
        if warnings:
            entry["warnings"] = warnings
    return entry


def _metric_breakdown(
    mr: dict[str, Any], metric_name: str, breakdown_key: str
) -> object:
    bd: object = mr[breakdown_key]
    if metric_name == "cognitive_points" and isinstance(bd, dict):
        bd = {
            k: {"total": round(v["total"], 1)} if isinstance(v, dict) else round(v, 1)
            for k, v in bd.items()
        }
    return bd


def _metric_warnings(mr: dict[str, Any], cli_id: str) -> list[str]:
    raw = mr.get(f"{cli_id}_warnings", [])
    if not isinstance(raw, list):
        return []
    return [
        w.get("message", str(w)) if isinstance(w, dict) else str(w) for w in raw
    ]


def _entities_for_export(
    ctx: PipelineContext, export_path: Path | None
) -> list[dict]:
    stage_entities: list[dict] = []
    if not export_path:
        return stage_entities
    try:
        rel = export_path.relative_to(ctx.repository)
    except (ValueError, AttributeError):
        rel = export_path
    stage_entities.append({"format": "json", "path": str(rel)})
    return stage_entities