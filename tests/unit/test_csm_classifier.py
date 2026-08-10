from __future__ import annotations

from specmetrics.kernel.csm.activity_classifier import (
    classify_activity_type,
    classify_activity_type_with_context,
)
from specmetrics.kernel.csm.classifier import classify_node
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
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


class TestClassifyAllCategories:
    def test_extracted_element_returns_matches(self) -> None:
        from specmetrics.kernel.csm.classifier import classify_all_categories

        node = _make_node("n1", "We decided to use microservices")
        assert classify_all_categories(node) == ["decision"]

    def test_evidence_node_returns_empty(self) -> None:
        from specmetrics.kernel.csm.classifier import classify_all_categories

        node = _make_node("n2", "We decided to use microservices", node_type="evidence")
        assert classify_all_categories(node) == []

    def test_glossary_term_matched_by_match(self) -> None:
        from specmetrics.kernel.csm.classifier import classify_all_categories

        node = _make_node("n3", "Token Points: A metric measuring density")
        assert classify_all_categories(node) == ["glossary_term"]

    def test_non_glossary_uses_search(self) -> None:
        from specmetrics.kernel.csm.classifier import classify_all_categories

        node = _make_node("n4", "We decided to use microservices")
        assert "decision" in classify_all_categories(node)


class TestStripFrameworkLabels:
    def test_removes_framework_prefix(self) -> None:
        from specmetrics.kernel.csm.classifier import strip_framework_labels

        assert strip_framework_labels("OpenSpec Section: Requirements") == "Requirements"
        assert strip_framework_labels("Speckit Feature: Login") == "Login"
        assert strip_framework_labels("SpecMetrics Document: Overview") == "Overview"

    def test_untouched_text(self) -> None:
        from specmetrics.kernel.csm.classifier import strip_framework_labels

        assert strip_framework_labels("Plain text") == "Plain text"


def _graph_with(nodes: dict[str, GraphNode], edges: list[GraphEdge]) -> EvidenceGraph:
    return EvidenceGraph(
        run_id="run-1",
        nodes=nodes,
        edges=edges,
        metadata=GraphMetadata(run_id="run-1", node_count=len(nodes), edge_count=len(edges)),
    )


class TestGetEvidenceReferences:
    def _graph(self) -> EvidenceGraph:
        sa = _make_node("sa", "Explore requirements")
        ev = _make_node("ev", "evidence text", node_type="evidence")
        ev2 = _make_node("ev2", "second evidence", node_type="evidence")
        ev3 = _make_node("ev3", "composed target", node_type="evidence")
        return _graph_with(
            {"sa": sa, "ev": ev, "ev2": ev2, "ev3": ev3},
            [
                GraphEdge(source="sa", target="ev", edge_type="derived_from"),
                GraphEdge(source="sa", target="ev2", edge_type="references"),
                GraphEdge(source="sa", target="ev3", edge_type="composed_of"),
            ],
        )

    def test_includes_derived_from_and_references(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        refs = get_evidence_references("sa", self._graph())
        texts = {r.text for r in refs}
        assert "evidence text" in texts
        assert "second evidence" in texts

    def test_excludes_composed_of(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        refs = get_evidence_references("sa", self._graph())
        assert "composed target" not in {r.text for r in refs}

    def test_ignores_edges_from_other_sources(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        graph = self._graph()
        other = _make_node("other", "unrelated evidence", node_type="evidence")
        graph.nodes["other"] = other
        graph.edges.append(GraphEdge(source="other", target="other", edge_type="derived_from"))
        refs = get_evidence_references("sa", graph)
        assert "unrelated evidence" not in {r.text for r in refs}

    def test_self_reference_included(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        refs = get_evidence_references("sa", self._graph())
        assert "Explore requirements" in {r.text for r in refs}

    def test_dedupes_duplicate_edges_to_same_target(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        sa = _make_node("sa", "Explore requirements")
        ev = _make_node("ev", "evidence text", node_type="evidence")
        graph = _graph_with(
            {"sa": sa, "ev": ev},
            [
                GraphEdge(source="sa", target="ev", edge_type="derived_from"),
                GraphEdge(source="sa", target="ev", edge_type="references"),
            ],
        )
        refs = get_evidence_references("sa", graph)
        assert len(refs) == 2

    def test_missing_target_node_skipped(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        sa = _make_node("sa", "Explore requirements")
        graph = _graph_with(
            {"sa": sa},
            [GraphEdge(source="sa", target="missing", edge_type="derived_from")],
        )
        refs = get_evidence_references("sa", graph)
        assert len(refs) == 1

    def test_section_id_preserved_on_refs(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_evidence_references

        sa = _make_node("sa", "Explore requirements")
        sa.section_id = "sec-1"
        graph = _graph_with({"sa": sa}, [])
        refs = get_evidence_references("sa", graph)
        assert refs[0].section_id == "sec-1"


class TestGetNeighbors:
    def _graph(self) -> EvidenceGraph:
        n = _make_node("n", "center")
        a = _make_node("a", "out neighbor")
        b = _make_node("b", "in neighbor")
        c = _make_node("c", "unrelated")
        d = _make_node("d", "unrelated 2")
        return _graph_with(
            {"n": n, "a": a, "b": b, "c": c, "d": d},
            [
                GraphEdge(source="n", target="a", edge_type="derived_from"),
                GraphEdge(source="b", target="n", edge_type="derived_from"),
                GraphEdge(source="c", target="d", edge_type="derived_from"),
            ],
        )

    def test_returns_both_directions(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_neighbors

        neighbors = get_neighbors("n", self._graph())
        assert {nb.id for nb in neighbors} == {"a", "b"}

    def test_edge_type_filter(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_neighbors

        graph = self._graph()
        e = _make_node("e", "composed target")
        graph.nodes["e"] = e
        graph.edges.append(GraphEdge(source="n", target="e", edge_type="composed_of"))
        neighbors = get_neighbors("n", graph, edge_type="derived_from")
        assert {nb.id for nb in neighbors} == {"a", "b"}

    def test_all_neighbors_are_nodes(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_neighbors

        neighbors = get_neighbors("n", self._graph())
        assert all(nb is not None for nb in neighbors)

    def test_missing_neighbor_node_skipped(self) -> None:
        from specmetrics.kernel.csm.evidence_processing import get_neighbors

        n = _make_node("n", "center")
        graph = _graph_with(
            {"n": n},
            [GraphEdge(source="n", target="ghost", edge_type="derived_from")],
        )
        neighbors = get_neighbors("n", graph)
        assert neighbors == []
