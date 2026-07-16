from __future__ import annotations

from typing import Optional, Protocol

from pydantic import BaseModel, Field

from .adapter_interface import Document


class EvidenceReference(BaseModel):
    """Pointer back to the source material that justifies an extracted element."""

    document_id: str = Field(min_length=1)
    section_id: Optional[str] = None
    text: str = Field(min_length=1)


class ExtractedElement(BaseModel):
    """Semantic element produced by extraction.

    Represents a fact, entity, relationship, or operation identified in a
    specification document.
    """

    id: str
    type: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: EvidenceReference
    content: str


class ProcessingStats(BaseModel):
    """Metadata about the extraction process for observability."""

    documents_processed: int = 0
    elements_extracted: int = 0
    errors: int = 0
    duration_ms: int = 0


class ExtractionResult(BaseModel):
    """Output of a single provider's extraction for one or more documents."""

    elements: list[ExtractedElement] = []
    provider_id: str
    processing_stats: ProcessingStats


class ExtractionProvider(Protocol):
    """Structural interface that every extraction provider must implement."""

    def extract(self, document: Document) -> ExtractionResult:
        """Extract semantic elements from a single document.

        Must be idempotent and must not modify the input document.
        """

    def supports_type(self, document_type: str) -> bool:
        """Return True if this provider can handle the given document type.

        Must be fast (no full document scan or external calls).
        """
