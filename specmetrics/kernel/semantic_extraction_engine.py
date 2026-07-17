from __future__ import annotations

from typing import Literal, Optional, Protocol

from pydantic import BaseModel, Field

from .adapter_interface import Document


class EvidenceReference(BaseModel):
    """Pointer to source material that justifies an extracted element."""

    document_id: str = Field(min_length=1)
    section_id: Optional[str] = None
    text: str = Field(min_length=1)
    rule_id: str = ""


class ExtractedElement(BaseModel):
    """A semantic element produced by extraction."""

    id: str = Field(min_length=1)
    type: Literal["fact", "entity", "relationship", "operation"]
    content: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: EvidenceReference


class ProcessingStats(BaseModel):
    """Metadata about the extraction process for observability."""

    documents_processed: int = 0
    elements_extracted: int = 0
    elements_by_type: dict[str, int] = {}
    duration_ms: int = 0
    errors_count: int = 0


class ExtractionResult(BaseModel):
    """Canonical output model produced by extraction engines."""

    elements: list[ExtractedElement] = []
    engine_id: str
    processing_stats: ProcessingStats

    def deterministic_dump(self) -> dict:
        """Return model dict excluding non-deterministic timing fields.

        Use this for byte-identical comparison across runs (SC-002).
        """
        return self.model_dump(exclude={"processing_stats": {"duration_ms"}})


class SemanticExtractionEngine(Protocol):
    """Interface that all extraction engines must implement."""

    def extract(self, documents: list[Document]) -> ExtractionResult: ...


class SemanticEngineFactory:
    _ENGINE_MAP = {
        "none": "DeterministicSemanticEngine",
        "chatgpt": "LiteLLMSemanticEngine",
        "claude": "LiteLLMSemanticEngine",
        "gemini": "LiteLLMSemanticEngine",
        "ollama": "LiteLLMSemanticEngine",
    }

    _MODEL_MAP = {
        "chatgpt": "gpt-4",
        "claude": "claude-3-opus",
        "gemini": "gemini-pro",
        "ollama": "ollama/llama3",
    }

    @classmethod
    def create(
        cls, provider: str, config: dict | None = None
    ) -> SemanticExtractionEngine:
        engine_name = cls._ENGINE_MAP.get(provider)
        if engine_name is None:
            raise ValueError(f"Unknown provider: {provider}")

        if engine_name == "DeterministicSemanticEngine":
            from .deterministic_engine import DeterministicSemanticEngine

            return DeterministicSemanticEngine(**(config or {}))

        from .litellm_engine import LiteLLMSemanticEngine

        resolved_config = dict(config or {})
        if "model" not in resolved_config:
            resolved_config["model"] = cls._MODEL_MAP.get(provider, "gpt-4")
        return LiteLLMSemanticEngine(**resolved_config)
