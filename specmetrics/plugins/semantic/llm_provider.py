from __future__ import annotations

import logging
import time
from typing import Any

import litellm

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)

logger = logging.getLogger(__name__)

_DEFAULT_CHUNK_SIZE = 8_000

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
    def __init__(self, provider_id: str = "llm-provider", chunk_size: int = _DEFAULT_CHUNK_SIZE) -> None:
        self._provider_id = provider_id
        self._chunk_size = chunk_size

    def supports_type(self, document_type: str) -> bool:
        return True

    def _chunk_content(self, content: str) -> list[tuple[str, int]]:
        """Split content into chunks of at most ``chunk_size`` characters.

        Returns a list of ``(chunk_text, chunk_index)`` tuples.
        Splits on paragraph boundaries when possible.
        """
        if len(content) <= self._chunk_size:
            return [(content, 0)]

        chunks: list[tuple[str, int]] = []
        start = 0
        chunk_idx = 0
        while start < len(content):
            end = min(start + self._chunk_size, len(content))
            if end < len(content):
                boundary = content.rfind("\n\n", start, end)
                if boundary > start:
                    end = boundary + 2
                else:
                    boundary = content.rfind("\n", start, end)
                    if boundary > start:
                        end = boundary + 1
            chunks.append((content[start:end], chunk_idx))
            chunk_idx += 1
            start = end
        return chunks

    def extract(self, document: Document) -> ExtractionResult:
        started_at = time.monotonic()
        all_elements: list[ExtractedElement] = []
        chunks = self._chunk_content(document.content)
        errors = 0

        for chunk_text, chunk_idx in chunks:
            try:
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
                        {"role": "user", "content": chunk_text},
                    ],
                )
                chunk_elements = self._parse_response(response, document, chunk_idx)
                all_elements.extend(chunk_elements)
            except Exception:
                logger.warning("LLM extraction failed for chunk %d, falling back to structural", chunk_idx)
                try:
                    chunk_elements = self._structural_parse(document, chunk_text, chunk_idx)
                    all_elements.extend(chunk_elements)
                except Exception:
                    errors += 1

        duration = int((time.monotonic() - started_at) * 1000)
        return ExtractionResult(
            provider_id=self._provider_id,
            elements=all_elements,
            processing_stats=ProcessingStats(
                documents_processed=1,
                elements_extracted=len(all_elements),
                errors=errors,
                duration_ms=duration,
            ),
        )

    def _parse_response(
        self, response: Any, document: Document, chunk_idx: int = 0
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
                section_id = f"chunk-{chunk_idx}" if chunk_idx > 0 else None
                elements.append(
                    ExtractedElement(
                        id=f"{document.id}/llm-{chunk_idx}-{i}",
                        type=elem_type,
                        confidence=max(0.0, min(1.0, confidence)),
                        evidence=EvidenceReference(
                            document_id=document.id,
                            section_id=section_id,
                            text=text[:200],
                        ),
                        content=text,
                    )
                )
        except Exception:
            logger.warning("Failed to parse LLM response, falling back to structural")
            elements = self._structural_parse(document, document.content)
        return elements

    def _structural_parse(
        self, document: Document, chunk_text: str | None = None, chunk_idx: int = 0
    ) -> list[ExtractedElement]:
        elements: list[ExtractedElement] = []
        content = chunk_text or document.content
        section_id = f"chunk-{chunk_idx}" if chunk_idx > 0 else None
        for section in (document.sections or []):
            if chunk_text and section.content not in chunk_text:
                continue
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/sec-{chunk_idx}-{section.id}",
                    type="fact",
                    confidence=0.6,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        section_id=section_id or section.id,
                        text=section.content[:200],
                    ),
                    content=f"{section.title}: {section.content}",
                )
            )
        if not elements:
            fallback_text = content[:200] if content else "(empty document)"
            elements.append(
                ExtractedElement(
                    id=f"{document.id}/full-{chunk_idx}",
                    type="section",
                    confidence=0.5,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        section_id=section_id,
                        text=fallback_text,
                    ),
                    content=content or "",
                )
            )
        return elements
