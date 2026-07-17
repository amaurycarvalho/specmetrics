from __future__ import annotations

import logging
import os
import time
from typing import Any

import litellm
from pydantic import BaseModel, Field

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose error banners — we handle errors ourselves
litellm.suppress_debug_info = True
litellm.set_verbose = False
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
logging.getLogger("litellm").setLevel(logging.WARNING)

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


class LLMProviderConfig(BaseModel):
    api_url: str | None = Field(
        None,
        description="Base URL for the LLM API (e.g. https://api.openai.com/v1)",
    )
    model: str = Field(
        "gpt-4o-mini",
        description="Model identifier (e.g. gpt-4o-mini, claude-3-haiku)",
    )
    api_key: str | None = Field(
        None,
        description="API key or authentication token",
        json_schema_extra={"sensitive": True},
    )


class LLMExtractionProvider:
    def __init__(
        self,
        provider_id: str = "llm-provider",
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        api_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._provider_id = provider_id
        self._chunk_size = chunk_size

        self._api_url = (
            api_url
            or os.environ.get("SPECMETRICS_LLM_API_URL")
        )
        self._model = (
            model
            or os.environ.get("SPECMETRICS_LLM_MODEL")
            or "gpt-4o-mini"
        )
        self._api_key = (
            api_key
            or os.environ.get("SPECMETRICS_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return LLMProviderConfig

    def supports_type(self, document_type: str) -> bool:
        return True

    _config_warned: bool = False
    _no_key: bool = False

    def _check_config(self) -> str | None:
        if not self._api_key:
            self.__class__._no_key = True
            if not self.__class__._config_warned:
                self.__class__._config_warned = True
                return (
                    "LLM extraction disabled: no API key configured.\n"
                    "  Run:  specmetrics config llm set <provider> --api-key <key>\n"
                    "  Or set the SPECMETRICS_LLM_API_KEY environment variable.\n"
                    "  Falling back to structural extraction."
                )
            return None
        return None

    def _build_completion_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self._model,
        }
        if self._api_url:
            kwargs["api_base"] = self._api_url
        if self._api_key:
            kwargs["api_key"] = self._api_key
        return kwargs

    def _chunk_content(self, content: str) -> list[tuple[str, int]]:
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

        config_msg = self._check_config()
        if config_msg is not None:
            logger.warning(config_msg)

        if self.__class__._no_key:
            for chunk_text, chunk_idx in chunks:
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

        completion_kwargs = self._build_completion_kwargs()

        for chunk_text, chunk_idx in chunks:
            try:
                response = litellm.completion(
                    **completion_kwargs,
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
                logger.warning(
                    "LLM API call failed for chunk %d. "
                    "Run 'specmetrics config llm set <provider> --api-key <key>' to configure credentials, "
                    "or 'specmetrics config llm show' to review current settings. "
                    "Falling back to structural extraction for this chunk.",
                    chunk_idx,
                )
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
                    type="fact",
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
