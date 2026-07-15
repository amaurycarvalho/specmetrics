from __future__ import annotations

import pytest

from specmetrics.kernel.evidence_graph_stage import NetworkXBackend
from specmetrics.kernel.graph_query_engine import GraphQueryEngine


@pytest.fixture
def populated_backend() -> NetworkXBackend:
    b = NetworkXBackend()
    b.add_node("e1", {
        "node_type": "extracted_element", "semantic_type": "fact",
        "document_id": "doc1", "text": "fact one",
    })
    b.add_node("e2", {
        "node_type": "extracted_element", "semantic_type": "entity",
        "document_id": "doc1", "text": "entity one",
    })
    b.add_node("e3", {
        "node_type": "extracted_element", "semantic_type": "fact",
        "document_id": "doc2", "text": "fact two",
    })
    b.add_node("ev1", {
        "node_type": "evidence", "document_id": "doc1", "text": "source text 1",
    })
    b.add_node("ev2", {
        "node_type": "evidence", "document_id": "doc2", "text": "source text 2",
    })
    b.add_edge("e1", "ev1", {"edge_type": "derived_from"})
    b.add_edge("e2", "ev1", {"edge_type": "derived_from"})
    b.add_edge("e3", "ev2", {"edge_type": "derived_from"})
    return b


@pytest.fixture
def engine(populated_backend: NetworkXBackend) -> GraphQueryEngine:
    return GraphQueryEngine(populated_backend)


class TestGraphQueryEngine:
    def test_get_node_existing(self, engine: GraphQueryEngine) -> None:
        node = engine.get_node("e1")
        assert node is not None
        assert node["id"] == "e1"

    def test_get_node_missing(self, engine: GraphQueryEngine) -> None:
        assert engine.get_node("nonexistent") is None

    def test_query_by_document(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_document("doc1")
        assert len(nodes) == 3
        assert all(n["document_id"] == "doc1" for n in nodes)

    def test_query_by_document_empty(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_document("nonexistent")
        assert nodes == []

    def test_query_by_type(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_type("fact")
        assert len(nodes) == 2
        assert all(n["semantic_type"] == "fact" for n in nodes)

    def test_query_by_type_empty(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_type("operation")
        assert nodes == []

    def test_query_by_evidence(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_evidence("fact")
        assert len(nodes) >= 2

    def test_query_by_evidence_no_match(self, engine: GraphQueryEngine) -> None:
        nodes = engine.query_by_evidence("zzzznotfound")
        assert nodes == []

    def test_traverse_provenance(self, engine: GraphQueryEngine) -> None:
        paths = engine.traverse_provenance("e1", max_depth=5)
        assert len(paths) >= 1
        first_path = paths[0]
        assert first_path[0]["id"] == "e1"
        assert first_path[-1]["id"] == "ev1"

    def test_traverse_provenance_max_depth(self, engine: GraphQueryEngine) -> None:
        paths = engine.traverse_provenance("e1", max_depth=0)
        assert len(paths) == 1
        assert paths[0][0]["id"] == "e1"
        assert len(paths[0]) == 1

    def test_traverse_provenance_nonexistent(self, engine: GraphQueryEngine) -> None:
        from specmetrics.kernel.evidence_graph import NodeNotFoundError
        with pytest.raises(NodeNotFoundError):
            engine.traverse_provenance("nonexistent")

    def test_find_references(self, engine: GraphQueryEngine) -> None:
        refs = engine.find_references("ev1")
        assert len(refs["incoming"]) == 2
        assert refs["outgoing"] == []

    def test_find_references_nonexistent(self, engine: GraphQueryEngine) -> None:
        refs = engine.find_references("nonexistent")
        assert refs["incoming"] == []
        assert refs["outgoing"] == []
