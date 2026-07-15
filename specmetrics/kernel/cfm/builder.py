from __future__ import annotations

import time
from typing import Any

import structlog

from specmetrics.kernel.cfm.classifier import classify_node, strip_framework_labels
from specmetrics.kernel.cfm.metadata import BuildMetadata, ClassificationConflict
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    UnclassifiedElement,
)
from datetime import datetime, timezone

from specmetrics.kernel.evidence_graph import EvidenceGraph, GraphNode
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


def build(graph: EvidenceGraph) -> CanonicalFunctionalModel:
    actors: dict[str, Actor] = {}
    functional_processes: dict[str, FunctionalProcess] = {}
    business_rules: dict[str, BusinessRule] = {}
    data_groups: dict[str, DataGroup] = {}
    relationships: list[Relationship] = []
    operations: dict[str, Operation] = {}
    unclassified: dict[str, UnclassifiedElement] = {}
    conflicts: list[ClassificationConflict] = []

    started_at = time.monotonic()

    for node_id, node in graph.nodes.items():
        if node.node_type != "extracted_element":
            continue

        category = classify_node(node)
        if category is None:
            unclassified[node_id] = UnclassifiedElement(
                id=node_id,
                original_type=node.semantic_type or "unknown",
                content=node.text,
                evidence=_to_evidence_ref(node_id, node),
            )
            continue

        clean_name = strip_framework_labels(node.text)
        evidence = _to_evidence_ref(node_id, node)

        if category == "actor":
            actors[node_id] = Actor(id=node_id, name=clean_name, evidence=evidence)
        elif category == "business_rule":
            business_rules[node_id] = BusinessRule(
                id=node_id, name=clean_name, description=node.text, evidence=evidence,
            )
        elif category == "data_group":
            data_groups[node_id] = DataGroup(id=node_id, name=clean_name, evidence=evidence)
        elif category == "relationship":
            source_id, target_id = _extract_relationship_endpoints(node_id, graph)
            relationships.append(Relationship(
                id=node_id, source_id=source_id, target_id=target_id,
                evidence=evidence,
            ))
        elif category == "operation":
            operations[node_id] = Operation(
                id=node_id, name=clean_name, parent_process_id="",
                description=node.text, evidence=evidence,
            )

    build_duration_ms = int((time.monotonic() - started_at) * 1000)
    element_counts = {
        "actors": len(actors),
        "functional_processes": len(functional_processes),
        "business_rules": len(business_rules),
        "data_groups": len(data_groups),
        "relationships": len(relationships),
        "operations": len(operations),
        "unclassified": len(unclassified),
    }

    metadata = BuildMetadata(
        run_id=graph.run_id,
        build_duration_ms=build_duration_ms,
        element_counts=element_counts,
        total_input_nodes=len([n for n in graph.nodes.values() if n.node_type == "extracted_element"]),
        unclassified_count=len(unclassified),
        conflicts=conflicts,
    )

    return CanonicalFunctionalModel(
        run_id=graph.run_id,
        actors=actors,
        functional_processes=functional_processes,
        business_rules=business_rules,
        data_groups=data_groups,
        relationships=relationships,
        operations=operations,
        unclassified=unclassified,
        metadata=metadata,
        evidence_graph_ref=graph.run_id,
    )


def _extract_relationship_endpoints(node_id: str, graph: EvidenceGraph) -> tuple[str, str]:
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


class CfmBuilderStage:
    def __init__(self) -> None:
        self._handled_event_type = EventType.EVIDENCE_GRAPH_BUILT
        self._handler_id = "cfm_builder_stage"
        self._stage_name = "canonical_model"

    @property
    def handled_event_type(self) -> EventType:
        return self._handled_event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event: PipelineEvent) -> PipelineContext:
        context = event.context

        graph_data = context.evidence_graph
        if graph_data is None:
            logger.warning("cfm_builder_no_evidence_graph", execution_id=str(event.context.execution_id))
            payload = _empty_payload(event)
            return context.with_stage_output(field_name="canonical_model", value=payload)

        run_id = graph_data.get("run_id", str(int(event.timestamp.timestamp())))

        try:
            from specmetrics.kernel.graph_persistence import GraphStore
            import os
            graphs_dir = os.path.join(os.getcwd(), ".evidence_graphs")
            graph_path = os.path.join(graphs_dir, f"{run_id}.jsonl")
            evidence_graph = GraphStore.load(graph_path)
        except Exception:
            logger.warning(
                "cfm_builder_load_failed",
                run_id=run_id,
                execution_id=str(event.context.execution_id),
            )
            payload = _empty_payload(event)
            return context.with_stage_output(field_name="canonical_model", value=payload)

        cfm = build(evidence_graph)

        payload = {
            "run_id": cfm.run_id,
            "element_counts": cfm.metadata.element_counts,
            "build_duration_ms": cfm.metadata.build_duration_ms,
            "total_input_nodes": cfm.metadata.total_input_nodes,
            "unclassified_count": cfm.metadata.unclassified_count,
            "conflict_count": len(cfm.metadata.conflicts),
        }

        logger.info(
            "canonical_model_built",
            run_id=cfm.run_id,
            element_counts=cfm.metadata.element_counts,
            duration_ms=cfm.metadata.build_duration_ms,
        )

        canonical_event = PipelineEvent(
            event_type=EventType.CANONICAL_MODEL_BUILT,
            publisher=self._handler_id,
            payload=payload,
            context=context,
            timestamp=datetime.now(timezone.utc),
        )
        context = context.with_stage_output(field_name="canonical_model", value=payload, event=canonical_event)
        return context


def _empty_payload(event: PipelineEvent) -> dict[str, Any]:
    return {
        "run_id": str(int(event.timestamp.timestamp())),
        "element_counts": {},
        "build_duration_ms": 0,
        "total_input_nodes": 0,
        "unclassified_count": 0,
        "conflict_count": 0,
    }
