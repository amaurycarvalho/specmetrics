from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult,
    SemanticEngineFactory,
)


def _make_doc(doc_id: str, content: str, doc_type: str = "specification") -> Document:
    return Document(
        id=doc_id,
        path=f"/tmp/{doc_id}.md",
        document_type=doc_type,
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
        _make_doc(
            "doc-4",
            "```python\nprint('hello')\n```",
        ),
    ]


class TestDeterministicPipeline:
    def test_factory_resolves_none(self):
        engine = SemanticEngineFactory.create("none")
        assert engine is not None
        result = engine.extract(_sample_docs())
        assert isinstance(result, ExtractionResult)
        assert result.engine_id == "deterministic"

    def test_extraction_produces_elements(self):
        engine = DeterministicSemanticEngine()
        result = engine.extract(_sample_docs())
        assert len(result.elements) > 0

    def test_elements_have_evidence_with_rule_id(self):
        engine = DeterministicSemanticEngine()
        result = engine.extract(_sample_docs())
        for el in result.elements:
            assert el.evidence.document_id
            assert el.evidence.text
            assert el.evidence.rule_id

    def test_processing_stats_populated(self):
        engine = DeterministicSemanticEngine()
        result = engine.extract(_sample_docs())
        stats = result.processing_stats
        assert stats.documents_processed > 0
        assert stats.elements_extracted == len(result.elements)
        assert isinstance(stats.elements_by_type, dict)
        assert stats.duration_ms >= 0

    def test_deterministic_across_runs(self):
        engine = DeterministicSemanticEngine()
        r1 = engine.extract(_sample_docs())
        r2 = engine.extract(_sample_docs())
        d1 = r1.model_dump(exclude={"processing_stats": {"duration_ms"}})
        d2 = r2.model_dump(exclude={"processing_stats": {"duration_ms"}})
        assert d1 == d2

    def test_empty_document_list(self):
        engine = DeterministicSemanticEngine()
        result = engine.extract([])
        assert len(result.elements) == 0
        assert result.processing_stats.documents_processed == 0

    def test_framework_detection_openspec(self):
        doc = _make_doc("os-1", "# Use Case\nLogin", doc_type="openspec")
        engine = DeterministicSemanticEngine()
        result = engine.extract([doc])
        assert len(result.elements) >= 1

    def test_operation_extraction_from_gwt(self):
        doc = _make_doc(
            "gwt-1",
            "## User Story 1\n\n**GIVEN** a user is logged in\n**WHEN** they click submit\n**THEN** the form is saved\n",
            doc_type="speckit:specification",
        )
        engine = DeterministicSemanticEngine()
        result = engine.extract([doc])
        ops = [e for e in result.elements if e.type == "operation"]
        assert len(ops) >= 1
