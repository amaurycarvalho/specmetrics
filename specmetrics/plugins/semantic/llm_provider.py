from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.deterministic_engine import DeterministicSemanticEngine
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.llm_gateway import (
    BatchRequest,
    DocumentPayload,
    LLMGateway,
    LLMGatewayConfig,
)
from specmetrics.kernel.semantic_extraction_engine import (
    ExtractionResult as NewExtractionResult,
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


_CONFIG_SEARCH = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "specmetrics",
    Path("/etc/specmetrics"),
]


def _load_llm_config() -> dict[str, Any]:
    for base in _CONFIG_SEARCH:
        for fname in ("config.yml", "config.yaml", "config.json"):
            path = base / fname
            if path.exists():
                try:
                    import ruamel.yaml

                    yaml = ruamel.yaml.YAML(typ="safe")
                    data = yaml.load(path.read_text(encoding="utf-8"))
                    return (
                        (data or {})
                        .get("plugins", {})
                        .get("extraction_stage", {})
                        .get("llm", {})
                    )
                except Exception:
                    return {}
    return {}


class LLMExtractionProvider:
    def __init__(
        self,
        provider_id: str = "llm-provider",
        chunk_size: int = _DEFAULT_CHUNK_SIZE,
        provider: str | None = None,
        api_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        gateway: LLMGateway | None = None,
    ) -> None:
        self._provider_id = provider_id
        self._chunk_size = chunk_size

        has_explicit = any(x is not None for x in (provider, api_url, model, api_key))
        cfg = _load_llm_config() if not has_explicit else {}

        self._provider = provider if provider is not None else cfg.get("provider")

        self._api_url = (
            api_url or cfg.get("api_url") or os.environ.get("SPECMETRICS_LLM_API_URL")
        )
        self._model = (
            model
            or cfg.get("model")
            or os.environ.get("SPECMETRICS_LLM_MODEL")
            or "gpt-4o-mini"
        )
        self._api_key = (
            api_key
            or cfg.get("api_key")
            or os.environ.get("SPECMETRICS_LLM_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
        )

        if gateway is not None:
            self._gateway = gateway
        else:
            gw_config = LLMGatewayConfig(
                provider=self._provider or "openai",
                model=self._model,
                api_key=self._api_key,
                api_url=self._api_url,
            )
            self._gateway = LLMGateway(gw_config)

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
            kwargs["custom_llm_provider"] = "openai"
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

    def _run_deterministic_fallback(
        self, document: Document
    ) -> tuple[list[ExtractedElement], int]:
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

    def extract(self, document: Document) -> ExtractionResult:
        started_at = time.monotonic()
        all_elements: list[ExtractedElement] = []
        errors = 0

        config_msg = self._check_config()
        if config_msg is not None:
            logger.warning(config_msg)

        if self.__class__._no_key:
            return self._fallback_extract(document, started_at)

        chunks = self._chunk_content(document.content)
        doc_payloads = [
            DocumentPayload(
                document_id=f"{document.id}/chunk-{idx}",
                content=chunk_text,
                document_type=document.document_type,
            )
            for chunk_text, idx in chunks
        ]

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
                chunk_idx = 0
                if "/chunk-" in chunk_doc_id:
                    try:
                        chunk_idx = int(chunk_doc_id.split("/chunk-")[1])
                    except (ValueError, IndexError):
                        pass
                for i, item in enumerate(elements_list):
                    total_elements_found += 1
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
            if total_elements_found == 0 and chunks:
                logger.warning(
                    "LLM batch returned no elements, falling back to deterministic engine"
                )
                fb_elements, fb_errors = self._run_deterministic_fallback(document)
                all_elements.extend(fb_elements)
                errors += fb_errors
        except Exception:
            logger.warning(
                "LLM batch extraction failed, falling back to deterministic engine"
            )
            fb_elements, fb_errors = self._run_deterministic_fallback(document)
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
        self, document: Document, started_at: float
    ) -> ExtractionResult:
        all_elements, errors = self._run_deterministic_fallback(document)
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
        self, content: str, document: Document, chunk_idx: int = 0
    ) -> list[ExtractedElement]:
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
            fb_elements, _ = self._run_deterministic_fallback(document)
            elements.extend(fb_elements)
        return elements
