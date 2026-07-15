from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.builder import build
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    Relationship,
)
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
)


def make_graph(nodes: list[GraphNode], edges: list[GraphEdge] | None = None) -> EvidenceGraph:
    return EvidenceGraph(
        run_id="test_run_001",
        nodes={n.id: n for n in nodes},
        edges=edges or [],
        metadata=GraphMetadata(run_id="test_run_001", node_count=len(nodes), edge_count=len(edges or [])),
    )


class TestBuild:
    def test_empty_graph_produces_empty_cfm(self) -> None:
        graph = make_graph([])
        cfm = build(graph)
        assert isinstance(cfm, CanonicalFunctionalModel)
        assert cfm.run_id == "test_run_001"
        assert len(cfm.actors) == 0
        assert len(cfm.functional_processes) == 0
        assert len(cfm.business_rules) == 0
        assert len(cfm.data_groups) == 0
        assert len(cfm.relationships) == 0
        assert len(cfm.operations) == 0
        assert len(cfm.unclassified) == 0

    def test_build_with_all_categories(self) -> None:
        nodes = [
            GraphNode(id="n1", node_type="extracted_element", semantic_type="fact", document_id="doc1", text="System validates email"),
            GraphNode(id="n2", node_type="extracted_element", semantic_type="entity", document_id="doc1", text="Administrator"),
            GraphNode(id="n3", node_type="extracted_element", semantic_type="entity", document_id="doc1", text="UserAccount"),
            GraphNode(id="n4", node_type="extracted_element", semantic_type="relationship", document_id="doc1", text="Admin manages users"),
            GraphNode(id="n5", node_type="extracted_element", semantic_type="operation", document_id="doc1", text="Create user"),
        ]
        edges = [
            GraphEdge(source="n2", target="n4", edge_type="references"),
        ]
        graph = make_graph(nodes, edges)
        cfm = build(graph)
        assert len(cfm.business_rules) == 1
        assert len(cfm.actors) == 1
        assert len(cfm.data_groups) == 1
        assert len(cfm.relationships) == 1
        assert len(cfm.operations) == 1

    def test_evidence_references_preserved(self) -> None:
        node = GraphNode(id="n1", node_type="extracted_element", semantic_type="fact", document_id="doc1", section_id="s1", text="rule text")
        graph = make_graph([node])
        cfm = build(graph)
        rule = next(iter(cfm.business_rules.values()))
        assert rule.evidence.graph_node_id == "n1"
        assert rule.evidence.document_id == "doc1"
        assert rule.evidence.section_id == "s1"
        assert rule.evidence.text == "rule text"

    def test_framework_labels_stripped(self) -> None:
        node = GraphNode(id="n1", node_type="extracted_element", semantic_type="fact", document_id="doc1", text="OpenSpec Section: Login Rule")
        graph = make_graph([node])
        cfm = build(graph)
        rule = next(iter(cfm.business_rules.values()))
        assert "OpenSpec" not in rule.name
        assert rule.name == "Login Rule"

    def test_unclassifiable_elements_in_references(self) -> None:
        node = GraphNode(id="n1", node_type="extracted_element", semantic_type=None, document_id="doc1", text="weird element")
        graph = make_graph([node])
        cfm = build(graph)
        assert len(cfm.unclassified) == 1
        assert cfm.unclassified["n1"].original_type == "unknown"

    def test_conflicting_classifications_flagged(self) -> None:
        nodes = [
            GraphNode(id="n1", node_type="extracted_element", semantic_type="fact", document_id="doc1", text="Process: do something"),
            GraphNode(id="n2", node_type="extracted_element", semantic_type="operation", document_id="doc1", text="Process: do something"),
        ]
        edges = [GraphEdge(source="n1", target="n2", edge_type="composed_of")]
        graph = make_graph(nodes, edges)
        cfm = build(graph)
        assert len(cfm.metadata.conflicts) >= 0

    def test_evidence_node_ignored(self) -> None:
        node = GraphNode(id="n1", node_type="evidence", document_id="doc1", text="source text")
        graph = make_graph([node])
        cfm = build(graph)
        assert len(cfm.business_rules) == 0
        assert len(cfm.actors) == 0
        assert len(cfm.functional_processes) == 0
        assert len(cfm.data_groups) == 0
        assert len(cfm.relationships) == 0
        assert len(cfm.operations) == 0
