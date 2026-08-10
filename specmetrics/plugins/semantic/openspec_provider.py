"""Built-in extraction provider for OpenSpec framework documents."""

from __future__ import annotations

import logging
import time
from typing import Self

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)

logger = logging.getLogger(__name__)

OPENTSPEC_TYPES = frozenset({"use_case", "business_rule", "actor", "relationship"})


class OpenSpecProvider:
    """Built-in extraction provider for OpenSpec framework documents.

    Handles use_case, business_rule, actor, and relationship document types
    using structural section-based parsing.
    """

    def __init__(self: Self, provider_id: str = "openspec-provider") -> None:
        """Initialize the provider with the given provider id."""
        self._provider_id = provider_id

    def supports_type(self: Self, document_type: str) -> bool:
        """Return whether this provider supports the document type."""
        return document_type in OPENTSPEC_TYPES

    def extract(self: Self, document: Document) -> ExtractionResult:
        """Extract semantic elements from the given document."""
        started_at = time.monotonic()
        elements: list[ExtractedElement] = []

        for i, section in enumerate(document.sections or []):
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/openspec-{i}",
                    type="fact",
                    confidence=0.85,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        section_id=section.id,
                        text=section.content[:200],
                    ),
                    content=f"[{document.document_type}] {section.title}: {section.content}",
                )
            )

        if not elements:
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/openspec-0",
                    type="fact",
                    confidence=0.7,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        text=document.content[:200],
                    ),
                    content=f"[{document.document_type}] {document.content}",
                )
            )

        duration = int((time.monotonic() - started_at) * 1000)
        return ExtractionResult(
            provider_id=self._provider_id,
            elements=elements,
            processing_stats=ProcessingStats(
                documents_processed=1,
                elements_extracted=len(elements),
                errors=0,
                duration_ms=duration,
            ),
        )

    def __repr__(self: Self) -> str:
        """Return a string representation of the provider."""
        return f"OpenSpecProvider({self._provider_id})"
