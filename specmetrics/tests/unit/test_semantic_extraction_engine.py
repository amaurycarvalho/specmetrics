from __future__ import annotations

import pytest

from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult,
    SemanticEngineFactory,
)


class TestSemanticEngineFactory:
    def test_resolves_none_to_deterministic(self) -> None:
        engine = SemanticEngineFactory.create("none")
        assert engine is not None
        result = engine.extract([])
        assert isinstance(result, ExtractionResult)
        assert result.engine_id == "deterministic"

    def test_resolves_chatgpt_to_litellm(self) -> None:
        engine = SemanticEngineFactory.create("chatgpt")
        assert engine is not None
        result = engine.extract([])
        assert isinstance(result, ExtractionResult)
        assert result.engine_id == "litellm"

    def test_resolves_claude_to_litellm(self) -> None:
        engine = SemanticEngineFactory.create("claude")
        assert engine is not None
        result = engine.extract([])
        assert result.engine_id == "litellm"

    def test_resolves_gemini_to_litellm(self) -> None:
        engine = SemanticEngineFactory.create("gemini")
        assert engine is not None
        result = engine.extract([])
        assert result.engine_id == "litellm"

    def test_resolves_ollama_to_litellm(self) -> None:
        engine = SemanticEngineFactory.create("ollama")
        assert engine is not None
        result = engine.extract([])
        assert result.engine_id == "litellm"

    def test_raises_value_error_for_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider"):
            SemanticEngineFactory.create("unknown_provider")

    def test_create_returns_extraction_engine_protocol(self) -> None:
        engine = SemanticEngineFactory.create("none")
        assert hasattr(engine, "extract")
        result = engine.extract([])
        assert isinstance(result, ExtractionResult)
