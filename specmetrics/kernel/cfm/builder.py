"""Build a Canonical Functional Model from an evidence graph."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Self

import structlog

from specmetrics.kernel.cfm.classifier import classify_node, strip_framework_labels
from specmetrics.kernel.cfm.metadata import BuildMetadata, ClassificationConflict
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    FunctionalProcess,
    Operation,
    Relationship,
    UnclassifiedElement,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.evidence_graph import EvidenceGraph
from specmetrics.kernel.pipeline_context import PipelineContext

from ._entities import (
    _NODE_ENTITY_BUILDERS,
    DEFAULT_SEMANTIC_MARKER_FALLBACK,
    DEFAULT_SEMANTIC_MARKER_MAP,
    _build_functional_processes,
    _extract_relationship_endpoints,
    _to_evidence_ref,
)

logger = structlog.get_logger(__name__)

__all__ = [
    "DEFAULT_SEMANTIC_MARKER_FALLBACK",
    "DEFAULT_SEMANTIC_MARKER_MAP",
    "CfmBuilderStage",
    "build",
]


def build(
    graph: EvidenceGraph,
    semantic_marker_map: list[tuple[set[str], set[str], str]] | None = None,
    semantic_marker_fallback: dict[str, str] | None = None,
) -> CanonicalFunctionalModel:
    """Build a canonical functional model from the given evidence graph."""
    actors: dict[str, Actor] = {}
    functional_processes: dict[str, FunctionalProcess] = {}
    business_rules: dict[str, BusinessRule] = {}
    data_groups: dict[str, DataGroup] = {}
    relationships: list[Relationship] = []
    operations: dict[str, Operation] = {}
    unclassified: dict[str, UnclassifiedElement] = {}
    conflicts: list[ClassificationConflict] = []

    started_at = time.monotonic()

    node_containers: dict[str, dict[str, object]] = {
        "actor": actors,
        "business_rule": business_rules,
        "data_group": data_groups,
        "operation": operations,
    }

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

        section_id = node.section_id

        if category == "relationship":
            source_id, target_id = _extract_relationship_endpoints(node_id, graph)
            relationships.append(
                Relationship(
                    id=node_id,
                    source_id=source_id,
                    target_id=target_id,
                    evidence=evidence,
                )
            )
            continue

        builder = _NODE_ENTITY_BUILDERS.get(category)
        if builder is not None:
            node_containers[category][node_id] = builder(
                node_id,
                node,
                clean_name,
                evidence,
                section_id,
                semantic_marker_map,
                semantic_marker_fallback,
            )

    functional_processes = _build_functional_processes(operations, data_groups, actors)

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
        total_input_nodes=len(
            [n for n in graph.nodes.values() if n.node_type == "extracted_element"]
        ),
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


class CfmBuilderStage:
    """Pipeline stage that builds a canonical functional model from an evidence graph."""

    def __init__(
        self: Self,
        semantic_marker_map: list[tuple[set[str], set[str], str]] | None = None,
        semantic_marker_fallback: dict[str, str] | None = None,
    ) -> None:
        """Initialize the stage with optional semantic marker configuration."""
        self._handled_event_type = EventType.EVIDENCE_GRAPH_BUILT
        self._handler_id = "cfm_builder_stage"
        self._stage_name = "canonical_model"
        self._semantic_marker_map = semantic_marker_map
        self._semantic_marker_fallback = semantic_marker_fallback

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this stage handles."""
        return self._handled_event_type

    @property
    def handler_id(self: Self) -> str:
        """Return the unique handler identifier for this stage."""
        return self._handler_id

    @property
    def stage_name(self: Self) -> str:
        """Return the stage name."""
        return self._stage_name

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Handle a pipeline event and build the canonical functional model."""
        context = event.context

        graph_data = context.evidence_graph
        if graph_data is None:
            logger.warning(
                "cfm_builder_no_evidence_graph",
                execution_id=str(event.context.execution_id),
            )
            return context.with_stage_output(field_name="canonical_model", value=None)

        run_id = graph_data.get("run_id", str(int(event.timestamp.timestamp())))

        try:
            import os

            from specmetrics.kernel.graph_persistence import GraphStore

            graphs_dir = os.path.join(os.getcwd(), ".specmetrics", "evidence_graphs")
            graph_path = os.path.join(graphs_dir, f"{run_id}.jsonl")
            evidence_graph = GraphStore.load(graph_path)
        except Exception:
            logger.warning(
                "cfm_builder_load_failed",
                run_id=run_id,
                execution_id=str(event.context.execution_id),
            )
            return context.with_stage_output(field_name="canonical_model", value=None)

        cfm = build(
            evidence_graph, self._semantic_marker_map, self._semantic_marker_fallback
        )

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
            timestamp=datetime.now(UTC),
        )
        context = context.with_stage_output(
            field_name="canonical_model", value=cfm, event=canonical_event
        )
        return context
