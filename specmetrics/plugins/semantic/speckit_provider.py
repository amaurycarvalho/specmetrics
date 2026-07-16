from __future__ import annotations

import logging
import time

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)

logger = logging.getLogger(__name__)

SPECKIT_TYPES = frozenset({"section", "term", "process", "data_group"})


class SpecKitProvider:
    """Built-in extraction provider for SpecKit framework documents.

    Handles section, term, process, and data_group document types
    using structural section-based parsing.
    """

    def __init__(self, provider_id: str = "speckit-provider") -> None:
        self._provider_id = provider_id

    def supports_type(self, document_type: str) -> bool:
        return document_type in SPECKIT_TYPES

    def extract(self, document: Document) -> ExtractionResult:
        started_at = time.monotonic()
        elements: list[ExtractedElement] = []

        for i, section in enumerate(document.sections or []):
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/speckit-{i}",
                    type="fact",
                    confidence=0.8,
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
                    id=f"{document.id}/speckit-0",
                    type="fact",
                    confidence=0.65,
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

    def __repr__(self) -> str:
        return f"SpecKitProvider({self._provider_id})"
