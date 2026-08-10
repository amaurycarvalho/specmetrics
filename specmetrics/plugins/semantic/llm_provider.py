"""LLM-backed semantic extraction provider with deterministic fallback."""

from __future__ import annotations

import logging
import time
from typing import Self

from pydantic import BaseModel, Field

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.llm_gateway import BatchRequest, LLMGateway

from ._config import (
    build_gateway,
    load_llm_config,
    resolve_api_key,
    resolve_api_url,
    resolve_model,
)
from ._content import (
    append_chunk_elements,
    build_doc_payloads,
    chunk_content,
    run_deterministic_fallback,
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


class LLMProviderConfig(BaseModel):
    """Configuration for the LLM extraction provider."""

    provider: str = Field(
        "none",
        description="Provider name (none for deterministic engine)",
    )
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
    """Extraction provider that uses an LLM gateway with deterministic fallback."""

    def __init__(
        self: Self,
        provider_id: str = "llm-provider",
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        provider: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        gateway: LLMGateway | None = None,
    ) -> None:
        """Initialize the provider with the given settings."""
        self._provider_id = provider_id
        self._chunk_size = chunk_size

        has_explicit = any(x is not None for x in (provider, api_url, model, api_key))
        cfg = load_llm_config() if not has_explicit else {}

        self._provider = provider if provider is not None else cfg.get("provider")
        self._api_url = resolve_api_url(api_url, cfg)
        self._model = resolve_model(model, cfg)
        self._api_key = resolve_api_key(api_key, cfg)
        self._gateway = gateway if gateway is not None else build_gateway(
            self._provider, self._model, self._api_key, self._api_url
        )

    @classmethod
    def config_schema(cls: type[Self]) -> type[BaseModel]:
        """Return the provider config model class."""
        return LLMProviderConfig

    def supports_type(self: Self, document_type: str) -> bool:
        """Return whether this provider supports the document type."""
        return True

    _config_warned: bool = False
    _no_key: bool = False

    def _check_config(self: Self) -> str | None:
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

    def extract(self: Self, document: Document) -> ExtractionResult:
        """Extract semantic elements from the given document."""
        started_at = time.monotonic()
        all_elements: list[ExtractedElement] = []
        errors = 0

        config_msg = self._check_config()
        if config_msg is not None:
            logger.warning(config_msg)

        if self.__class__._no_key:
            return self._fallback_extract(document, started_at)

        chunks = chunk_content(document.content, self._chunk_size)
        doc_payloads = build_doc_payloads(document, chunks)

        batch = BatchRequest(
            system_prompt=(
                "Extract semantic elements from the following specification document. "
                "Return a JSON object with an 'elements' array where each element has "
                "fields: type (fact/entity/relationship/operation), "
                "confidence (0.0-1.0), and content."
            ),
            documents=doc_payloads,
        )

        try:
            batch_results = self._gateway.complete_batch(batch, json_mode=True)
            total_elements_found = 0
            for chunk_doc_id, elements_list in batch_results.items():
                total_elements_found += append_chunk_elements(
                    chunk_doc_id, elements_list, document, all_elements
                )
            if total_elements_found == 0 and chunks:
                logger.warning(
                    "LLM batch returned no elements, falling back to deterministic engine"
                )
                fb_elements, fb_errors = run_deterministic_fallback(document)
                all_elements.extend(fb_elements)
                errors += fb_errors
        except Exception:
            logger.warning(
                "LLM batch extraction failed, falling back to deterministic engine"
            )
            fb_elements, fb_errors = run_deterministic_fallback(document)
            all_elements.extend(fb_elements)
            errors += fb_errors

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

    def _fallback_extract(
        self: Self, document: Document, started_at: float
    ) -> ExtractionResult:
        all_elements, errors = run_deterministic_fallback(document)
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