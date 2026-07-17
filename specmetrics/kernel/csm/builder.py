from __future__ import annotations

import time
from datetime import datetime, timezone

import structlog

from specmetrics.kernel.csm.classifier import (
    classify_all_categories,
    classify_node,
    strip_framework_labels,
)
from specmetrics.kernel.csm.activity_classifier import (
    classify_activity_type_with_context,
)
from specmetrics.kernel.csm.evidence_processing import (
    get_evidence_references,
    get_neighbors,
)
from specmetrics.kernel.csm.metadata import BuildMetadata, ClassificationConflict
from specmetrics.kernel.csm.model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Constraint,
    Decision,
    GlossaryTerm,
    OpenQuestion,
    Reference,
    Risk,
    SpecificationActivity,
)
from specmetrics.kernel.evidence_graph import EvidenceGraph
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


def build(graph: EvidenceGraph) -> CanonicalSpecificationModel:
    specification_activities: dict[str, SpecificationActivity] = {}
    decisions: dict[str, Decision] = {}
    assumptions: dict[str, Assumption] = {}
    constraints: dict[str, Constraint] = {}
    risks: dict[str, Risk] = {}
    open_questions: dict[str, OpenQuestion] = {}
    acceptance_criteria: dict[str, AcceptanceCriterion] = {}
    glossary_terms: dict[str, GlossaryTerm] = {}
    references: dict[str, Reference] = {}
    conflicts: list[ClassificationConflict] = []
    category_for_node: dict[str, str] = {}

    started_at = time.monotonic()

    # First pass: classify all nodes and create entities
    for node_id, node in graph.nodes.items():
        if node.node_type != "extracted_element":
            continue

        all_categories = classify_all_categories(node)
        if len(all_categories) > 1:
            conflicts.append(
                ClassificationConflict(
                    node_id=node_id,
                    competing_categories=list(all_categories),
                    resolved_category=all_categories[0],
                    reason=f"Multiple patterns matched: {', '.join(all_categories)}",
                )
            )

        category = classify_node(node)
        if category is None:
            references[node_id] = Reference(
                id=node_id,
                description=strip_framework_labels(node.text),
                evidence_references=get_evidence_references(node_id, graph),
                original_label=node.semantic_type or "",
            )
            continue

        category_for_node[node_id] = category
        clean_text = strip_framework_labels(node.text)
        evidence_refs = get_evidence_references(node_id, graph)

        if category == "decision":
            decisions[node_id] = Decision(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "assumption":
            assumptions[node_id] = Assumption(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "constraint":
            constraints[node_id] = Constraint(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
                constraint_type="technical",
            )
        elif category == "risk":
            risks[node_id] = Risk(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "open_question":
            open_questions[node_id] = OpenQuestion(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "acceptance_criterion":
            acceptance_criteria[node_id] = AcceptanceCriterion(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "glossary_term":
            glossary_terms[node_id] = GlossaryTerm(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
            )
        elif category == "specification_activity":
            specification_activities[node_id] = SpecificationActivity(
                id=node_id,
                description=clean_text,
                evidence_references=evidence_refs,
                activity_type="clarification",
            )

    # Second pass: link specification activities to discovered entities
    all_decisions = decisions
    all_assumptions = assumptions
    all_constraints = constraints
    all_risks = risks
    all_open_questions = open_questions
    all_acceptance_criteria = acceptance_criteria

    for sa_id, sa in specification_activities.items():
        activity_type = classify_activity_type_with_context(
            graph.nodes[sa_id], graph
        )
        linked = _find_linked(
            sa_id, graph,
            all_decisions, all_assumptions, all_constraints,
            all_risks, all_open_questions, all_acceptance_criteria,
        )
        specification_activities[sa_id] = SpecificationActivity(
            id=sa.id,
            description=sa.description,
            evidence_references=sa.evidence_references,
            activity_type=activity_type or "clarification",
            linked_decisions=linked.get("decisions", []),
            linked_assumptions=linked.get("assumptions", []),
            linked_questions=linked.get("open_questions", []),
            linked_constraints=linked.get("constraints", []),
            linked_risks=linked.get("risks", []),
            linked_acceptance_criteria=linked.get("acceptance_criteria", []),
        )

    build_duration_ms = int((time.monotonic() - started_at) * 1000)
    element_counts = {
        "specification_activities": len(specification_activities),
        "decisions": len(decisions),
        "assumptions": len(assumptions),
        "constraints": len(constraints),
        "risks": len(risks),
        "open_questions": len(open_questions),
        "acceptance_criteria": len(acceptance_criteria),
        "glossary_terms": len(glossary_terms),
        "references": len(references),
    }

    metadata = BuildMetadata(
        run_id=graph.run_id,
        build_duration_ms=build_duration_ms,
        element_counts=element_counts,
        total_input_nodes=len(
            [n for n in graph.nodes.values() if n.node_type == "extracted_element"]
        ),
        unclassified_count=len(references),
        classification_conflicts=conflicts,
    )

    return CanonicalSpecificationModel(
        run_id=graph.run_id,
        specification_activities=specification_activities,
        decisions=decisions,
        assumptions=assumptions,
        constraints=constraints,
        risks=risks,
        open_questions=open_questions,
        acceptance_criteria=acceptance_criteria,
        glossary_terms=glossary_terms,
        references=references,
        metadata=metadata,
        evidence_graph_ref=graph.run_id,
    )


def _find_linked(
    node_id: str,
    graph: EvidenceGraph,
    decisions: dict[str, Decision],
    assumptions: dict[str, Assumption],
    constraints: dict[str, Constraint],
    risks: dict[str, Risk],
    open_questions: dict[str, OpenQuestion],
    acceptance_criteria: dict[str, AcceptanceCriterion],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {
        "decisions": [],
        "assumptions": [],
        "open_questions": [],
        "constraints": [],
        "risks": [],
        "acceptance_criteria": [],
    }

    neighbors = get_neighbors(node_id, graph)
    for neighbor in neighbors:
        nid = neighbor.id
        if nid in decisions:
            result["decisions"].append(nid)
        if nid in assumptions:
            result["assumptions"].append(nid)
        if nid in constraints:
            result["constraints"].append(nid)
        if nid in risks:
            result["risks"].append(nid)
        if nid in open_questions:
            result["open_questions"].append(nid)
        if nid in acceptance_criteria:
            result["acceptance_criteria"].append(nid)

    return result


class CsmBuilderStage:
    def __init__(self) -> None:
        self._handled_event_type = EventType.EVIDENCE_GRAPH_BUILT
        self._handler_id = "csm_builder_stage"
        self._stage_name = "canonical_spec_model"

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
            logger.warning(
                "csm_builder_no_evidence_graph",
                execution_id=str(event.context.execution_id),
            )
            return context.with_stage_output(field_name="canonical_spec_model", value=None)

        run_id = graph_data.get("run_id", str(int(event.timestamp.timestamp())))

        try:
            from specmetrics.kernel.graph_persistence import GraphStore
            import os

            graphs_dir = os.path.join(os.getcwd(), ".specmetrics", "evidence_graphs")
            graph_path = os.path.join(graphs_dir, f"{run_id}.jsonl")
            evidence_graph = GraphStore.load(graph_path)
        except Exception:
            logger.warning(
                "csm_builder_load_failed",
                run_id=run_id,
                execution_id=str(event.context.execution_id),
            )
            return context.with_stage_output(field_name="canonical_spec_model", value=None)

        csm = build(evidence_graph)

        payload = {
            "run_id": csm.run_id,
            "element_counts": csm.metadata.element_counts,
            "build_duration_ms": csm.metadata.build_duration_ms,
            "total_input_nodes": csm.metadata.total_input_nodes,
            "unclassified_count": csm.metadata.unclassified_count,
            "conflict_count": len(csm.metadata.classification_conflicts),
        }

        logger.info(
            "canonical_spec_model_built",
            run_id=csm.run_id,
            element_counts=csm.metadata.element_counts,
            duration_ms=csm.metadata.build_duration_ms,
        )

        canonical_event = PipelineEvent(
            event_type=EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,
            publisher=self._handler_id,
            payload=payload,
            context=context,
            timestamp=datetime.now(timezone.utc),
        )
        context = context.with_stage_output(
            field_name="canonical_spec_model", value=csm, event=canonical_event
        )
        return context
