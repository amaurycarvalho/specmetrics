from __future__ import annotations

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult,
    SemanticExtractionEngine,
)


def _make_doc(
    doc_id: str = "test-1",
    content: str = "# Test\nHello",
    doc_type: str = "specification",
) -> Document:
    return Document(
        id=doc_id, path=f"/tmp/{doc_id}.md", document_type=doc_type, content=content
    )


class TestProtocolConformance:
    def test_conforms_to_semantic_extraction_engine(self) -> None:
        engine: SemanticExtractionEngine = DeterministicSemanticEngine()
        assert engine is not None

    def test_extract_returns_extraction_result(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc()])
        assert isinstance(result, ExtractionResult)


class TestExtractStructure:
    def test_returns_elements_for_structural_content(self) -> None:
        content = "# Actors\n- User\n- Admin\n\n# Business Rules\nIf X Then Y"
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc(content=content)])
        assert len(result.elements) > 0

    def test_engine_id_is_deterministic(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc()])
        assert result.engine_id == "deterministic"

    def test_evidence_references_are_present(self) -> None:
        content = "# Actors\n- Admin"
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc(content=content)])
        for el in result.elements:
            assert el.evidence.document_id == "test-1"
            assert el.evidence.text

    def test_processing_stats_populated(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc()])
        assert result.processing_stats.documents_processed >= 0
        assert result.processing_stats.elements_extracted >= 0
        assert isinstance(result.processing_stats.elements_by_type, dict)
        assert result.processing_stats.duration_ms >= 0


class TestDeterminism:
    def test_same_document_produces_identical_elements(self) -> None:
        content = "# Constraints\n- Must be fast\n- Must be secure"
        engine = DeterministicSemanticEngine()
        doc = _make_doc(content=content)
        r1 = engine.extract([doc])
        r2 = engine.extract([doc])

        d1 = r1.model_dump(exclude={"processing_stats": {"duration_ms"}})
        d2 = r2.model_dump(exclude={"processing_stats": {"duration_ms"}})
        assert d1 == d2

    def test_content_hash_is_deterministic(self) -> None:
        content = "# Actors\n- Admin"
        engine = DeterministicSemanticEngine()
        doc = _make_doc(content=content)
        r1 = engine.extract([doc])
        r2 = engine.extract([doc])
        ids1 = [e.id for e in r1.elements]
        ids2 = [e.id for e in r2.elements]
        assert ids1 == ids2

    def test_content_hash_is_unique(self) -> None:
        content = "# Actors\n- Admin\n- User"
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc(content=content)])
        ids = [e.id for e in result.elements]
        assert len(ids) == len(set(ids))


class TestEdgeCases:
    def test_empty_document_returns_empty_result(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([_make_doc(content="")])
        assert len(result.elements) == 0

    def test_no_recognizable_patterns_returns_empty(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract(
            [_make_doc(content="Just some plain text with no patterns.")]
        )
        assert len(result.elements) == 0

    def test_empty_document_list(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([])
        assert len(result.elements) == 0
        assert result.processing_stats.documents_processed == 0

    def test_binary_content_skipped(self) -> None:
        engine = DeterministicSemanticEngine()
        null_bytes = "\x00\x01\x02\x03\x04" * 100
        result = engine.extract([_make_doc(content=null_bytes)])
        assert len(result.elements) == 0

    def test_deep_heading_flattened(self) -> None:
        content = "# A\n## B\n### C\n#### D\n##### E\n###### F\n####### G"
        engine = DeterministicSemanticEngine(max_heading_depth=6)
        result = engine.extract([_make_doc(content=content)])
        assert result is not None
