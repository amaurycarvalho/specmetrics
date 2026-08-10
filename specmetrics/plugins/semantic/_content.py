"""Internal chunking, payload, and response helpers for LLM extraction."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
)
from specmetrics.kernel.llm_gateway import DocumentPayload
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult as NewExtractionResult,
)

logger = logging.getLogger(__name__)


def chunk_content(content: str, chunk_size: int) -> list[tuple[str, int]]:
    """Split content into chunks, breaking at paragraph boundaries when possible."""
    if len(content) <= chunk_size:
        return [(content, 0)]

    chunks: list[tuple[str, int]] = []
    start = 0
    chunk_idx = 0
    while start < len(content):
        end = min(start + chunk_size, len(content))
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


def build_doc_payloads(
    document: Document, chunks: list[tuple[str, int]]
) -> list[DocumentPayload]:
    """Build per-chunk document payloads for the document."""
    return [
        DocumentPayload(
            document_id=f"{document.id}/chunk-{idx}",
            content=chunk_text,
            document_type=document.document_type,
        )
        for chunk_text, idx in chunks
    ]


def run_deterministic_fallback(
    document: Document,
) -> tuple[list[ExtractedElement], int]:
    """Run the deterministic engine and return extracted elements with a flag."""
    try:
        det_engine = DeterministicSemanticEngine()
        det_result: NewExtractionResult = det_engine.extract([document])
        elements: list[ExtractedElement] = []
        for el in det_result.elements:
            elements.append(
                ExtractedElement(
                    id=el.id,
                    type=el.type,
                    confidence=el.confidence,
                    evidence=EvidenceReference(
                        document_id=el.evidence.document_id,
                        section_id=el.evidence.section_id,
                        text=el.evidence.text,
                    ),
                    content=el.content,
                )
            )
        return elements, 0
    except Exception:
        return [], 1


def append_chunk_elements(
    chunk_doc_id: str,
    elements_list: list[dict[str, Any]],
    document: Document,
    all_elements: list[ExtractedElement],
) -> int:
    """Convert chunk element dicts into extracted elements and return the count."""
    chunk_idx = 0
    if "/chunk-" in chunk_doc_id:
        try:
            chunk_idx = int(chunk_doc_id.split("/chunk-")[1])
        except (ValueError, IndexError):
            pass
    for i, item in enumerate(elements_list):
        elem_type = item.get("type", "fact")
        confidence = float(item.get("confidence", 0.5))
        text = item.get("content", "")
        section_id = f"chunk-{chunk_idx}" if chunk_idx > 0 else None
        all_elements.append(
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
    return len(elements_list)


def parse_response(
    content: str,
    document: Document,
    fallback_fn: Callable[[Document], tuple[list[ExtractedElement], int]],
    chunk_idx: int = 0,
) -> list[ExtractedElement]:
    """Parse an LLM response, falling back to the deterministic engine on failure."""
    elements: list[ExtractedElement] = []
    try:
        data = json.loads(content)
        items = data if isinstance(data, list) else data.get("elements", data)
        for i, item in enumerate(items if isinstance(items, list) else []):
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
        logger.warning(
            "Failed to parse LLM response, falling back to deterministic engine"
        )
        fb_elements, _ = fallback_fn(document)
        elements.extend(fb_elements)
    return elements