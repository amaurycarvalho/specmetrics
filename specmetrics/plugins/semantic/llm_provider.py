from __future__ import annotations

import logging
import time
from typing import Any

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)

logger = logging.getLogger(__name__)

CANONICAL_TYPE_MAP: dict[str, str] = {
    "use-case": "use_case",
    "use_case": "use_case",
    "business-rule": "business_rule",
    "business_rule": "business_rule",
    "actor": "actor",
    "process": "process",
    "data": "data_group",
    "glossary": "term",
    "relationship": "relationship",
    "section": "section",
}


def _infer_type(document_type: str) -> str:
    return CANONICAL_TYPE_MAP.get(document_type, "unknown")


class LLMExtractionProvider:
    def __init__(self, provider_id: str = "llm-provider") -> None:
        self._provider_id = provider_id

    def supports_type(self, document_type: str) -> bool:
        return True

    def extract(self, document: Document) -> ExtractionResult:
        started_at = time.monotonic()
        elements: list[ExtractedElement] = []

        try:
            import litellm
            response = litellm.completion(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract semantic elements from the following specification document. "
                            "Return a JSON array of objects with fields: type (fact/entity/relationship/operation), "
                            "confidence (0.0-1.0), and content."
                        ),
                    },
                    {"role": "user", "content": document.content},
                ],
            )
            elements = self._parse_response(response, document)
        except Exception:
            logger.warning("LLM extraction failed, falling back to structural parsing")
            elements = self._structural_parse(document)

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

    def _parse_response(
        self, response: Any, document: Document
    ) -> list[ExtractedElement]:
        elements: list[ExtractedElement] = []
        try:
            content = response.choices[0].message.content
            import json
            data = json.loads(content)
            for i, item in enumerate(data):
                elem_type = item.get("type", "fact")
                confidence = float(item.get("confidence", 0.5))
                text = item.get("content", "")
                elements.append(
                    ExtractedElement(
                        id=f"{document.id}/llm-{i}",
                        type=elem_type,
                        confidence=max(0.0, min(1.0, confidence)),
                        evidence=EvidenceReference(
                            document_id=document.id,
                            text=text[:200],
                        ),
                        content=text,
                    )
                )
        except Exception:
            logger.warning("Failed to parse LLM response, falling back to structural")
            elements = self._structural_parse(document)
        return elements

    def _structural_parse(self, document: Document) -> list[ExtractedElement]:
        elements: list[ExtractedElement] = []
        for section in (document.sections or []):
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/sec-{section.id}",
                    type="fact",
                    confidence=0.6,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        section_id=section.id,
                        text=section.content[:200],
                    ),
                    content=f"{section.title}: {section.content}",
                )
            )
        if not elements:
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/full",
                    type="section",
                    confidence=0.5,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        text=document.content[:200],
                    ),
                    content=document.content,
                )
            )
        return elements
