from __future__ import annotations


from specmetrics.kernel.csm.classifier import classify_node
from specmetrics.kernel.csm.activity_classifier import (
    classify_activity_type,
    classify_activity_type_with_context,
)
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphNode,
    GraphEdge,
    GraphMetadata,
)


def _make_node(
    node_id: str,
    text: str,
    node_type: str = "extracted_element",
    semantic_type: str | None = None,
) -> GraphNode:
    return GraphNode(
        id=node_id,
        node_type=node_type,  # type: ignore[arg-type]
        semantic_type=semantic_type,  # type: ignore[arg-type]
        document_id="doc1",
        text=text,
    )


class TestClassifier:
    def test_decision_pattern(self):
        node = _make_node("n1", "We decided to use microservices architecture")
        assert classify_node(node) == "decision"

    def test_assumption_pattern(self):
        node = _make_node(
            "n2", "We assume the system will handle 1000 concurrent users"
        )
        assert classify_node(node) == "assumption"

    def test_constraint_pattern(self):
        node = _make_node("n3", "The system must comply with GDPR regulations")
        assert classify_node(node) == "constraint"

    def test_constraint_shall(self):
        node = _make_node("n4", "All data shall be encrypted at rest")
        assert classify_node(node) == "constraint"

    def test_risk_pattern(self):
        node = _make_node("n5", "Risk of third-party API downtime during peak hours")
        assert classify_node(node) == "risk"

    def test_risk_concern(self):
        node = _make_node("n6", "A concern was raised about database scalability")
        assert classify_node(node) == "risk"

    def test_open_question_question_mark(self):
        node = _make_node("n7", "What is the expected response time?")
        assert classify_node(node) == "open_question"

    def test_open_question_tbd(self):
        node = _make_node("n8", "TBD on authentication mechanism")
        assert classify_node(node) == "open_question"

    def test_acceptance_criterion(self):
        node = _make_node(
            "n9",
            "Given the user is authenticated, when they request data, then the system returns 200",
        )
        assert classify_node(node) == "acceptance_criterion"

    def test_glossary_term(self):
        node = _make_node(
            "n10", "Token Points: A metric measuring specification token density"
        )
        assert classify_node(node) == "glossary_term"

    def test_specification_activity(self):
        node = _make_node("n11", "Explore the requirements for the payment module")
        assert classify_node(node) == "specification_activity"

    def test_unclassifiable_fallback(self):
        node = _make_node("n12", "Some random text that doesn't match any pattern")
        assert classify_node(node) is None

    def test_non_extracted_element_returns_none(self):
        node = _make_node("n13", "Some text", node_type="evidence")
        assert classify_node(node) is None

    def test_empty_text(self):
        node = _make_node("n14", "")
        assert classify_node(node) is None

    def test_decision_past_tense(self):
        node = _make_node(
            "n15", "It was agreed that Python would be the primary language"
        )
        assert classify_node(node) == "decision"

    def test_assumption_we_believe(self):
        node = _make_node(
            "n16", "We believe the migration can be completed in one sprint"
        )
        assert classify_node(node) == "assumption"

    def test_risk_potential_issue(self):
        node = _make_node("n17", "Potential issue with legacy system integration")
        assert classify_node(node) == "risk"

    def test_risk_if_when(self):
        node = _make_node("n18", "If the database migration fails when we deploy")
        assert classify_node(node) == "risk"


class TestActivityClassifier:
    def test_exploration(self):
        assert (
            classify_activity_type("Discover business requirements for the new module")
            == "exploration"
        )

    def test_research(self):
        assert (
            classify_activity_type("Research available authentication solutions")
            == "exploration"
        )

    def test_clarification(self):
        assert (
            classify_activity_type("Clarify the ambiguity around user permissions")
            == "clarification"
        )

    def test_refinement(self):
        assert (
            classify_activity_type("Refine the API specification for clarity")
            == "refinement"
        )

    def test_review(self):
        assert (
            classify_activity_type("Review the architecture document for consistency")
            == "review"
        )

    def test_validation(self):
        assert (
            classify_activity_type("Validate the requirements with stakeholders")
            == "validation"
        )

    def test_with_context_multiple_derived(self):
        graph = EvidenceGraph(
            run_id="run-1",
            nodes={
                "n1": _make_node("n1", "Improve specification structure"),
                "n2": _make_node("n2", "Detail for n1"),
                "n3": _make_node("n3", "More detail for n1"),
            },
            edges=[
                GraphEdge(source="n1", target="n2", edge_type="derived_from"),
                GraphEdge(source="n1", target="n3", edge_type="derived_from"),
            ],
            metadata=GraphMetadata(run_id="run-1", node_count=3, edge_count=2),
        )
        result = classify_activity_type_with_context(graph.nodes["n1"], graph)
        assert result == "refinement"

    def test_no_context_fallback(self):
        node = _make_node("n1", "Some activity text")
        graph = EvidenceGraph(
            run_id="run-1",
            nodes={"n1": node},
            edges=[],
            metadata=GraphMetadata(run_id="run-1", node_count=1, edge_count=0),
        )
        result = classify_activity_type_with_context(node, graph)
        assert result is None
