from __future__ import annotations

import pytest

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.litellm_engine import (
    ExtractionError,
    LiteLLMSemanticEngine,
)
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult,
    SemanticExtractionEngine,
)


def _make_doc(doc_id: str = "test-1", content: str = "# Test") -> Document:
    return Document(
        id=doc_id,
        path=f"/tmp/{doc_id}.md",
        document_type="specification",
        content=content,
    )


class TestProtocolConformance:
    def test_conforms_to_semantic_extraction_engine(self) -> None:
        engine: SemanticExtractionEngine = LiteLLMSemanticEngine(model="gpt-4")
        assert engine is not None

    def test_extract_returns_extraction_result(self) -> None:
        engine = LiteLLMSemanticEngine(model="gpt-4")
        result = engine.extract([_make_doc()])
        assert isinstance(result, ExtractionResult)


class TestEmptyInput:
    def test_empty_document_list(self) -> None:
        engine = LiteLLMSemanticEngine(model="gpt-4")
        result = engine.extract([])
        assert len(result.elements) == 0
        assert result.processing_stats.documents_processed == 0
        assert result.engine_id == "litellm"


class TestErrorHandling:
    def test_raises_error_when_litellm_not_installed(self) -> None:
        import specmetrics.kernel.litellm_engine as le

        original = le.HAS_LITELLM
        le.HAS_LITELLM = False
        try:
            engine = LiteLLMSemanticEngine(model="gpt-4")
            with pytest.raises(ExtractionError, match="LiteLLM is not installed"):
                engine._call_llm(_make_doc())
        finally:
            le.HAS_LITELLM = original

    def test_engine_id_is_litellm(self) -> None:
        engine = LiteLLMSemanticEngine(model="gpt-4")
        result = engine.extract([_make_doc()])
        assert result.engine_id == "litellm"
