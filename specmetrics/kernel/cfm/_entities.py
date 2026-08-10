"""Private entity-building helpers for the CFM builder."""

from __future__ import annotations

import re
from collections.abc import Iterable

from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
)
from specmetrics.kernel.evidence_graph import EvidenceGraph, GraphNode

_OPERATION_DIRECTION_PATTERNS = [
    (re.compile(r"\*\*WHEN\*\*"), "input"),
    (re.compile(r"\*\*GIVEN\*\*"), "input"),
    (re.compile(r"#### Scenario:"), "query"),
    (re.compile(r"\*\*THEN\*\*"), "output"),
]


def _infer_operation_direction(text: str) -> str:
    for pattern, direction in _OPERATION_DIRECTION_PATTERNS:
        if pattern.search(text):
            return direction
    return "input"


DEFAULT_SEMANTIC_MARKER_MAP: list[tuple[set[str], set[str], str]] = [
    (
        {"business_rule"},
        {"User Scenarios", "User Story", "Scenario", "Acceptance", "UI"},
        "presentation_interface",
    ),
    (
        {"data_group"},
        {"Data Model", "Key Entities", "Entities", "Schema"},
        "data_operation",
    ),
    (
        {"business_rule", "operation"},
        {"Functional Requirements", "Features", "Requirements", "Specification"},
        "operational_feature",
    ),
    (
        {"business_rule"},
        {"Integration", "API", "Contracts", "Technical", "Architecture"},
        "technical_interface",
    ),
]

DEFAULT_SEMANTIC_MARKER_FALLBACK: dict[str, str] = {
    "data_group": "data_operation",
    "operation": "operational_feature",
    "business_rule": "operational_feature",
    "actor": "operational_feature",
}


def _build_actor(
    node_id: str,
    node: GraphNode,
    clean_name: str,
    evidence: EvidenceRef,
    section_id: str | None,
    marker_map: list[tuple[set[str], set[str], str]] | None,
    fallback_map: dict[str, str] | None,
) -> Actor:
    """Build an Actor entity."""
    return Actor(
        id=node_id,
        name=clean_name,
        evidence=evidence,
        metadata={
            "semantic_marker": _infer_semantic_marker(
                "actor", section_id, marker_map, fallback_map
            )
        },
    )


def _build_business_rule(
    node_id: str,
    node: GraphNode,
    clean_name: str,
    evidence: EvidenceRef,
    section_id: str | None,
    marker_map: list[tuple[set[str], set[str], str]] | None,
    fallback_map: dict[str, str] | None,
) -> BusinessRule:
    """Build a BusinessRule entity."""
    return BusinessRule(
        id=node_id,
        name=clean_name,
        description=node.text,
        evidence=evidence,
        metadata={
            "semantic_marker": _infer_semantic_marker(
                "business_rule", section_id, marker_map, fallback_map
            )
        },
    )


def _build_data_group(
    node_id: str,
    node: GraphNode,
    clean_name: str,
    evidence: EvidenceRef,
    section_id: str | None,
    marker_map: list[tuple[set[str], set[str], str]] | None,
    fallback_map: dict[str, str] | None,
) -> DataGroup:
    """Build a DataGroup entity."""
    return DataGroup(
        id=node_id,
        name=clean_name,
        evidence=evidence,
        metadata={
            "semantic_marker": _infer_semantic_marker(
                "data_group", section_id, marker_map, fallback_map
            )
        },
    )


def _build_operation(
    node_id: str,
    node: GraphNode,
    clean_name: str,
    evidence: EvidenceRef,
    section_id: str | None,
    marker_map: list[tuple[set[str], set[str], str]] | None,
    fallback_map: dict[str, str] | None,
) -> Operation:
    """Build an Operation entity with an inferred direction."""
    return Operation(
        id=node_id,
        name=clean_name,
        parent_process_id="",
        description=node.text,
        evidence=evidence,
        metadata={
            "direction": _infer_operation_direction(node.text),
            "semantic_marker": _infer_semantic_marker(
                "operation", section_id, marker_map, fallback_map
            ),
        },
    )


_NODE_ENTITY_BUILDERS = {
    "actor": _build_actor,
    "business_rule": _build_business_rule,
    "data_group": _build_data_group,
    "operation": _build_operation,
}


def _infer_semantic_marker(
    category: str,
    section_id: str | None,
    marker_map: list[tuple[set[str], set[str], str]] | None = None,
    fallback_map: dict[str, str] | None = None,
) -> str:
    map_ = marker_map if marker_map is not None else DEFAULT_SEMANTIC_MARKER_MAP
    fallback = (
        fallback_map if fallback_map is not None else DEFAULT_SEMANTIC_MARKER_FALLBACK
    )
    if section_id:
        section_lower = section_id.lower()
        for categories, section_patterns, marker in map_:
            if category in categories:
                for sp in section_patterns:
                    if sp.lower() in section_lower:
                        return marker
    return fallback.get(category, "operational_feature")


def _group_by_document(
    items: Iterable[tuple[str, object]],
) -> dict[str, list[tuple[str, object]]]:
    """Group (id, element) pairs by the document id of their evidence."""
    grouped: dict[str, list[tuple[str, object]]] = {}
    for key, item in items:
        doc_id = item.evidence.document_id if item.evidence else "unknown"
        if doc_id not in grouped:
            grouped[doc_id] = []
        grouped[doc_id].append((key, item))
    return grouped


def _fp_evidence(
    fp_id: str, doc_id: str, ops: list[tuple[str, Operation]]
) -> EvidenceRef:
    """Resolve the evidence reference for a functional process."""
    if ops[0][1].evidence:
        return ops[0][1].evidence
    return EvidenceRef(
        graph_node_id=fp_id,
        document_id=doc_id,
        text="",
    )


def _build_functional_processes(
    operations: dict[str, Operation],
    data_groups: dict[str, DataGroup],
    actors: dict[str, Actor],
) -> dict[str, FunctionalProcess]:
    if not operations:
        return {}

    ops_by_doc = _group_by_document(operations.items())
    data_groups_by_doc = _group_by_document(data_groups.items())
    actors_by_doc = _group_by_document(actors.items())

    functional_processes: dict[str, FunctionalProcess] = {}
    for doc_id, ops in ops_by_doc.items():
        fp_id = f"fp_{doc_id}"
        fp_ops = [op_id for op_id, _ in ops]
        fp_evidence = _fp_evidence(fp_id, doc_id, ops)

        fp_dgs = [dg_id for dg_id, _ in data_groups_by_doc.get(doc_id, [])]
        fp_actors = [act_id for act_id, _ in actors_by_doc.get(doc_id, [])]

        functional_processes[fp_id] = FunctionalProcess(
            id=fp_id,
            name=f"Functional Process — {doc_id}",
            operation_ids=fp_ops,
            data_group_ids=fp_dgs,
            actor_ids=fp_actors,
            evidence=fp_evidence,
        )

    return functional_processes


def _extract_relationship_endpoints(
    node_id: str, graph: EvidenceGraph
) -> tuple[str, str]:
    for edge in graph.edges:
        if edge.source == node_id and edge.target != node_id:
            return node_id, edge.target
        if edge.target == node_id and edge.source != node_id:
            return edge.source, node_id
    return "", ""


def _to_evidence_ref(node_id: str, node: GraphNode) -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=node_id,
        document_id=node.document_id,
        section_id=node.section_id,
        text=node.text,
    )