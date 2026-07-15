from __future__ import annotations

import pytest

from specmetrics.kernel.evidence_graph import (
    GraphNode,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopError,
    fingerprint_node,
)
from specmetrics.kernel.evidence_graph_stage import EvidenceGraphStage, NetworkXBackend
from specmetrics.kernel.extraction_provider import ExtractedElement, EvidenceReference


@pytest.fixture
def backend() -> NetworkXBackend:
    return NetworkXBackend()


class TestNetworkXBackend:
    def test_add_node_stores_attributes(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "document_id": "doc1", "text": "hello"})
        node = backend.get_node("n1")
        assert node is not None
        assert node["id"] == "n1"
        assert node["node_type"] == "evidence"
        assert node["document_id"] == "doc1"

    def test_add_node_raises_on_duplicate(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "text": "hello"})
        with pytest.raises(NodeAlreadyExistsError, match="n1"):
            backend.add_node("n1", {"node_type": "evidence", "text": "world"})

    def test_add_edge_raises_on_missing_source(self, backend: NetworkXBackend) -> None:
        backend.add_node("n2", {"node_type": "evidence", "text": "target"})
        with pytest.raises(NodeNotFoundError, match="n1"):
            backend.add_edge("n1", "n2", {"edge_type": "derived_from"})

    def test_add_edge_raises_on_missing_target(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "text": "source"})
        with pytest.raises(NodeNotFoundError, match="n2"):
            backend.add_edge("n1", "n2", {"edge_type": "derived_from"})

    def test_add_edge_raises_self_loop(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "text": "self"})
        with pytest.raises(SelfLoopError, match="n1"):
            backend.add_edge("n1", "n1", {"edge_type": "derived_from"})

    def test_get_node_returns_attributes(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "document_id": "doc1", "text": "hello"})
        node = backend.get_node("n1")
        assert node is not None
        assert node["node_type"] == "evidence"

    def test_get_node_returns_none_for_missing(self, backend: NetworkXBackend) -> None:
        assert backend.get_node("nonexistent") is None

    def test_serialization_round_trip(self, backend: NetworkXBackend) -> None:
        backend.add_node("n1", {"node_type": "evidence", "text": "a"})
        backend.add_node("n2", {"node_type": "extracted_element", "document_id": "doc1", "text": "b"})
        backend.add_edge("n1", "n2", {"edge_type": "references"})
        data = backend.to_serializable()
        restored = NetworkXBackend()
        restored.from_serializable(data)
        assert restored.get_node("n1") is not None
        assert restored.get_node("n2") is not None
        n1 = restored.get_node("n1")
        assert n1 is not None
        assert n1["text"] == "a"

    def test_build_from_extraction_result_produces_correct_counts(self) -> None:
        backend = NetworkXBackend()
        from specmetrics.kernel.extraction_provider import (
            ExtractionResult,
            ProcessingStats,
        )

        ref = EvidenceReference(document_id="doc1", section_id="s1", text="evidence text")
        elem1 = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref, content="fact 1")
        elem2 = ExtractedElement(id="e2", type="entity", confidence=0.8, evidence=ref, content="entity 1")
        result = ExtractionResult(
            elements=[elem1, elem2],
            provider_id="test_provider",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=2, errors=0, duration_ms=10),
        )

        node_count = 0
        edge_count = 0
        for elem in result.elements:
            nid = fingerprint_node(
                elem.evidence.document_id, elem.evidence.section_id,
                elem.evidence.text, elem.type,
            )
            try:
                backend.add_node(nid, {
                    "node_type": "extracted_element", "semantic_type": elem.type,
                    "document_id": elem.evidence.document_id, "text": elem.content,
                })
                node_count += 1
            except NodeAlreadyExistsError:
                pass
            eid = fingerprint_node(
                elem.evidence.document_id, elem.evidence.section_id,
                elem.evidence.text, None,
            )
            try:
                backend.add_node(eid, {
                    "node_type": "evidence", "document_id": elem.evidence.document_id,
                    "text": elem.evidence.text,
                })
                node_count += 1
            except NodeAlreadyExistsError:
                pass
            try:
                backend.add_edge(nid, eid, {"edge_type": "derived_from"})
                edge_count += 1
            except Exception:
                pass

        assert node_count == 3
        assert edge_count == 2


class TestFingerprintNode:
    def test_fingerprint_is_deterministic(self) -> None:
        fp1 = fingerprint_node("doc1", "s1", "text", "fact")
        fp2 = fingerprint_node("doc1", "s1", "text", "fact")
        assert fp1 == fp2

    def test_fingerprint_differs_for_different_inputs(self) -> None:
        fp1 = fingerprint_node("doc1", "s1", "text", "fact")
        fp2 = fingerprint_node("doc1", "s1", "other", "fact")
        assert fp1 != fp2

    def test_fingerprint_handles_none_section(self) -> None:
        fp = fingerprint_node("doc1", None, "text", "fact")
        assert isinstance(fp, str)
        assert len(fp) == 64


class TestGraphNodeModel:
    def test_valid_extracted_element(self) -> None:
        node = GraphNode(
            id="n1", node_type="extracted_element", semantic_type="fact",
            document_id="doc1", text="content",
        )
        assert node.node_type == "extracted_element"
        assert node.semantic_type == "fact"

    def test_valid_evidence_node(self) -> None:
        node = GraphNode(
            id="n1", node_type="evidence",
            document_id="doc1", text="source text",
        )
        assert node.node_type == "evidence"
        assert node.semantic_type is None

    def test_confidence_validation(self) -> None:
        GraphNode(
            id="n1", node_type="extracted_element", semantic_type="fact",
            document_id="doc1", text="x", confidence=0.5,
        )
        with pytest.raises(Exception):
            GraphNode(
                id="n1", node_type="extracted_element", semantic_type="fact",
                document_id="doc1", text="x", confidence=1.5,
            )


class TestIncrementalUpdate:
    def test_update_replaces_nodes_from_document(self) -> None:
        backend = NetworkXBackend()
        backend.add_node("n1", {"node_type": "evidence", "document_id": "doc1", "text": "old"})
        backend.add_node("n2", {"node_type": "evidence", "document_id": "doc2", "text": "keep"})
        stage = EvidenceGraphStage(backend=backend)
        from specmetrics.kernel.extraction_provider import EvidenceReference, ExtractedElement, ExtractionResult, ProcessingStats
        ref = EvidenceReference(document_id="doc1", section_id="s1", text="new evidence")
        elem = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref, content="new fact")
        result = ExtractionResult(
            elements=[elem], provider_id="t",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        stage.update_for_document("doc1", result.model_dump(mode="json"))
        doc1_nodes = backend.query_nodes({"document_id": "doc1"})
        assert len(doc1_nodes) == 2

    def test_update_preserves_other_documents(self) -> None:
        backend = NetworkXBackend()
        backend.add_node("n1", {"node_type": "evidence", "document_id": "doc1", "text": "remove"})
        backend.add_node("n2", {"node_type": "evidence", "document_id": "doc2", "text": "keep"})
        stage = EvidenceGraphStage(backend=backend)
        ref = EvidenceReference(document_id="doc1", section_id="s1", text="new")
        elem = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref, content="new")
        from specmetrics.kernel.extraction_provider import ExtractionResult, ProcessingStats
        result = ExtractionResult(
            elements=[elem], provider_id="t",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        stage.update_for_document("doc1", result.model_dump(mode="json"))
        doc2_nodes = backend.query_nodes({"document_id": "doc2"})
        assert len(doc2_nodes) == 1
        assert doc2_nodes[0]["text"] == "keep"

    def test_update_empty_removes_all_document_nodes(self) -> None:
        backend = NetworkXBackend()
        backend.add_node("n1", {"node_type": "evidence", "document_id": "doc1", "text": "gone"})
        backend.add_node("n2", {"node_type": "evidence", "document_id": "doc2", "text": "stay"})
        stage = EvidenceGraphStage(backend=backend)
        stage.update_for_document("doc1", {"elements": []})
        doc1_nodes = backend.query_nodes({"document_id": "doc1"})
        assert doc1_nodes == []
