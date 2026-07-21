from __future__ import annotations

import json
import time
from typing import Any

import structlog

from .adapter_interface import Document
from .engine_patterns import _content_hash
from .llm_gateway import LLMGateway, LLMGatewayConfig
from .semantic_extraction_engine import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
    SemanticExtractionEngine,
)

logger = structlog.get_logger(__name__)


class ExtractionError(Exception): ...


_SYSTEM_PROMPT = """You are a semantic extraction engine. Extract semantic elements from the given specification document.

Return a JSON object with an "elements" array where each element has:
- "type": one of "fact", "entity", "relationship", "operation"
- "content": the extracted text content
- "confidence": a float between 0.0 and 1.0

Only extract elements that are explicitly present in the text. Do not infer or fabricate."""


class LiteLLMSemanticEngine(SemanticExtractionEngine):
    def __init__(
        self,
        model: str = "gpt-4",
        api_key: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        gateway: LLMGateway | None = None,
    ) -> None:
        self._model = model
        self._api_key = api_key
        self._temperature = temperature
        self._max_tokens = max_tokens

        if gateway is not None:
            self._gateway = gateway
        else:
            config = LLMGatewayConfig(
                provider="openai",
                model=model,
                api_key=api_key,
                max_tokens=max_tokens,
            )
            self._gateway = LLMGateway(config)

    def _call_llm(self, document: Document) -> list[dict[str, Any]]:
        user_content = (
            f"Document: {document.id}\n"
            f"Type: {document.document_type}\n\n"
            f"{document.content}"
        )

        try:
            response_text = self._gateway.complete(
                system_prompt=_SYSTEM_PROMPT,
                user_message=user_content,
                json_mode=True,
            )
            data = json.loads(response_text)
            return data.get("elements", [])
        except (json.JSONDecodeError, RuntimeError) as exc:
            raise ExtractionError(
                f"LLM provider failed: {type(exc).__name__}: {exc}"
            ) from exc

    def _parse_elements(
        self,
        raw_elements: list[dict[str, Any]],
        document: Document,
    ) -> list[ExtractedElement]:
        elements: list[ExtractedElement] = []
        for raw in raw_elements:
            elem_type = raw.get("type", "fact")
            if elem_type not in ("fact", "entity", "relationship", "operation"):
                elem_type = "fact"

            content = str(raw.get("content", ""))
            if not content:
                continue

            confidence = float(raw.get("confidence", 0.85))
            confidence = max(0.0, min(1.0, confidence))

            elem_id = _content_hash(document.id, None, content)
            evidence = EvidenceReference(
                document_id=document.id,
                section_id=None,
                text=content,
            )

            elements.append(
                ExtractedElement(
                    id=elem_id,
                    type=elem_type,
                    content=content,
                    confidence=confidence,
                    evidence=evidence,
                )
            )
        return elements

    def extract(self, documents: list[Document]) -> ExtractionResult:
        if not documents:
            return ExtractionResult(
                elements=[],
                engine_id="litellm",
                processing_stats=ProcessingStats(
                    documents_processed=0,
                    elements_extracted=0,
                    elements_by_type={},
                    duration_ms=0,
                    errors_count=0,
                ),
            )

        start = time.monotonic()
        all_elements: list[ExtractedElement] = []
        documents_processed = 0
        errors_count = 0

        for doc in documents:
            try:
                raw = self._call_llm(doc)
                elements = self._parse_elements(raw, doc)
                all_elements.extend(elements)
                documents_processed += 1
            except ExtractionError:
                logger.warning(
                    "llm_extraction_failed",
                    doc_id=doc.id,
                )
                errors_count += 1

        duration_ms = int((time.monotonic() - start) * 1000)

        elements_by_type: dict[str, int] = {}
        for el in all_elements:
            t = str(el.type)
            elements_by_type[t] = elements_by_type.get(t, 0) + 1

        return ExtractionResult(
            elements=all_elements,
            engine_id="litellm",
            processing_stats=ProcessingStats(
                documents_processed=documents_processed,
                elements_extracted=len(all_elements),
                elements_by_type=elements_by_type,
                duration_ms=duration_ms,
                errors_count=errors_count,
            ),
        )
