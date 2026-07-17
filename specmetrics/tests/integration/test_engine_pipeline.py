from __future__ import annotations

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult,
    SemanticEngineFactory,
    SemanticExtractionEngine,
)


def _make_doc(doc_id: str, content: str) -> Document:
    return Document(
        id=doc_id,
        path=f"/tmp/{doc_id}.md",
        document_type="specification",
        content=content,
    )


def _sample_docs() -> list[Document]:
    return [
        _make_doc("doc-1", "# Actors\n- Admin\n- User\n"),
        _make_doc("doc-2", "# Business Rules\nIf X Then Y\n"),
        _make_doc(
            "doc-3",
            "# User Story\nAs a user, I want to login So that I can access the system\n",
        ),
    ]


class TestPipelineWithDeterministicEngine:
    def test_factory_resolves_none_to_deterministic(self) -> None:
        engine = SemanticEngineFactory.create("none")
        assert engine is not None
        result = engine.extract(_sample_docs())
        assert isinstance(result, ExtractionResult)
        assert result.engine_id == "deterministic"

    def test_extraction_produces_elements_with_evidence(self) -> None:
        engine: SemanticExtractionEngine = DeterministicSemanticEngine()
        result = engine.extract(_sample_docs())
        assert len(result.elements) > 0
        for el in result.elements:
            assert el.evidence.document_id
            assert el.evidence.text

    def test_processing_stats_are_populated(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract(_sample_docs())
        stats = result.processing_stats
        assert stats.documents_processed > 0
        assert stats.elements_extracted == len(result.elements)
        assert isinstance(stats.elements_by_type, dict)
        assert stats.duration_ms >= 0

    def test_deterministic_output_across_runs(self) -> None:
        engine = DeterministicSemanticEngine()
        r1 = engine.extract(_sample_docs())
        r2 = engine.extract(_sample_docs())
        d1 = r1.model_dump(exclude={"processing_stats": {"duration_ms"}})
        d2 = r2.model_dump(exclude={"processing_stats": {"duration_ms"}})
        assert d1 == d2

    def test_empty_repository_returns_empty(self) -> None:
        engine = DeterministicSemanticEngine()
        result = engine.extract([])
        assert len(result.elements) == 0
        assert result.processing_stats.documents_processed == 0
