from __future__ import annotations

import pytest

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphMetadata,
    NodeAlreadyExistsError,
    fingerprint_node,
)
from specmetrics.kernel.evidence_graph_stage import EvidenceGraphStage, NetworkXBackend
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.pipeline_context import PipelineContext


def _make_event(payload: dict) -> PipelineEvent:
    context = PipelineContext()
    return PipelineEvent(
        event_type=EventType.SEMANTIC_EXTRACTION_COMPLETED,
        publisher="extraction_stage",
        payload=payload,
        context=context,
    )


class TestEvidenceGraphPipeline:
    def test_stage_builds_graph_from_extraction_result(self) -> None:
        ref = EvidenceReference(document_id="doc1", section_id="s1", text="evidence text")
        elem = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref, content="a fact")
        result = ExtractionResult(
            elements=[elem],
            provider_id="test",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        event = _make_event({"results": {"test": result.model_dump(mode="json")}})
        stage = EvidenceGraphStage()
        ctx = stage.handle(event)
        assert ctx.evidence_graph is not None
        assert ctx.evidence_graph["node_count"] >= 1
        assert ctx.evidence_graph["run_id"] is not None

    def test_stage_handles_empty_extraction(self) -> None:
        event = _make_event({"results": {}})
        stage = EvidenceGraphStage()
        ctx = stage.handle(event)
        assert ctx.evidence_graph is not None
        assert ctx.evidence_graph["node_count"] == 0
        assert ctx.evidence_graph["edge_count"] == 0

    def test_stage_handles_multiple_providers(self) -> None:
        ref1 = EvidenceReference(document_id="doc1", section_id="s1", text="text1")
        ref2 = EvidenceReference(document_id="doc2", section_id="s2", text="text2")
        elem1 = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref1, content="fact 1")
        elem2 = ExtractedElement(id="e2", type="entity", confidence=0.8, evidence=ref2, content="entity 1")
        r1 = ExtractionResult(
            elements=[elem1], provider_id="p1",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        r2 = ExtractionResult(
            elements=[elem2], provider_id="p2",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        event = _make_event({
            "results": {
                "p1": r1.model_dump(mode="json"),
                "p2": r2.model_dump(mode="json"),
            },
        })
        stage = EvidenceGraphStage()
        ctx = stage.handle(event)
        assert ctx.evidence_graph["node_count"] >= 2

    def test_update_for_document_replaces_nodes(self) -> None:
        backend = NetworkXBackend()
        ref = EvidenceReference(document_id="doc1", section_id="s1", text="evidence")
        elem = ExtractedElement(id="e1", type="fact", confidence=0.9, evidence=ref, content="old fact")
        nid = fingerprint_node(ref.document_id, ref.section_id, ref.text, elem.type)
        eid = fingerprint_node(ref.document_id, ref.section_id, ref.text, None)
        backend.add_node(nid, {"node_type": "extracted_element", "semantic_type": "fact", "document_id": "doc1", "text": "old fact"})
        backend.add_node(eid, {"node_type": "evidence", "document_id": "doc1", "text": "evidence"})
        backend.add_edge(nid, eid, {"edge_type": "derived_from"})
        backend.add_node("other", {"node_type": "evidence", "document_id": "doc2", "text": "other"})

        stage = EvidenceGraphStage(backend=backend)
        new_elem = ExtractedElement(id="e2", type="entity", confidence=0.7, evidence=ref, content="new entity")
        new_result = ExtractionResult(
            elements=[new_elem], provider_id="test",
            processing_stats=ProcessingStats(documents_processed=1, elements_extracted=1, errors=0, duration_ms=5),
        )
        stage.update_for_document("doc1", new_result.model_dump(mode="json"))

        doc1_nodes = backend.query_nodes({"document_id": "doc1"})
        assert len(doc1_nodes) == 2
        doc2_nodes = backend.query_nodes({"document_id": "doc2"})
        assert len(doc2_nodes) == 1
