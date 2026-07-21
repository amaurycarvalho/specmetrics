from __future__ import annotations

from pydantic import BaseModel

import structlog

from .events import EventType, PipelineEvent
from .extraction_provider import ExtractionResult
from .extraction_registry import ProviderRouter
from .handler_registry import EventHandler
from .llm_gateway import LLMGateway
from .pipeline_context import PipelineContext

_NON_TEXT_THRESHOLD = 0.3


def _is_likely_binary(content: str) -> bool:
    """Heuristic check: if more than 30 % of characters are nulls or
    control chars (excluding common whitespace), treat as binary."""
    if not content:
        return False
    control = sum(1 for c in content if ord(c) < 32 and c not in "\n\r\t\f\v")
    return control / len(content) > _NON_TEXT_THRESHOLD


logger = structlog.get_logger(__name__)


class ExtractionStage(EventHandler):
    """Pipeline stage that extracts semantic elements from specification documents.

    Consumes DocumentsDiscovered events, routes documents to registered
    extraction providers, and consolidates results into the pipeline context.
    """

    def __init__(
        self, router: ProviderRouter, gateway: LLMGateway | None = None
    ) -> None:
        self._router = router
        self._gateway = gateway
        self._handled_event_type = EventType.DOCUMENTS_DISCOVERED
        self._handler_id = "extraction_stage"
        self._stage_name = "semantic_extraction"

    @property
    def handled_event_type(self) -> EventType:
        return self._handled_event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    @classmethod
    def config_schema(cls) -> type[BaseModel] | None:
        try:
            from specmetrics.plugins.semantic.llm_provider import LLMProviderConfig

            return LLMProviderConfig
        except ImportError:
            return None

    def handle(self, event: PipelineEvent) -> PipelineContext:
        context = event.context
        self._inject_gateway(context)
        docs_data = getattr(context, "adapter_result", None) or {}
        documents = docs_data.get("documents", [])
        results: dict[str, ExtractionResult] = {}
        total_elements = 0
        documents_processed = 0
        documents_skipped = 0

        for doc in documents:
            try:
                if _is_likely_binary(doc.content):
                    logger.warning(
                        "skipping_binary_content",
                        doc_id=getattr(doc, "id", "unknown"),
                    )
                    documents_skipped += 1
                    continue
                provider = self._router.resolve(doc.document_type)
                if provider is None:
                    logger.warning(
                        "no_provider_for_document",
                        doc_id=getattr(doc, "id", "unknown"),
                        doc_type=doc.document_type,
                    )
                    documents_skipped += 1
                    continue
                result = provider.extract(doc)
                pid = getattr(result, "provider_id", "unknown")
                if pid not in results:
                    results[pid] = result
                else:
                    results[pid].elements.extend(result.elements)
                    results[pid].processing_stats.elements_extracted += len(
                        result.elements
                    )
                total_elements += len(result.elements)
                documents_processed += 1
            except Exception as exc:
                logger.warning(
                    "document_extraction_failed",
                    doc_id=getattr(doc, "id", "unknown"),
                    error=str(exc),
                )
                documents_skipped += 1

        payload = {
            "results": {k: v.model_dump() for k, v in results.items()},
            "total_elements": total_elements,
            "documents_processed": documents_processed,
            "documents_skipped": documents_skipped,
        }

        return context.with_stage_output(
            field_name="extraction_result",
            value=payload,
        )

    def _inject_gateway(self, context: PipelineContext) -> None:
        if self._gateway is not None:
            return
        metadata = getattr(context, "metadata", None) or {}
        gw = metadata.get("llm_gateway") if isinstance(metadata, dict) else None
        if gw is not None:
            self._gateway = gw
            for provider in self._router.list_providers():
                if hasattr(provider, "_gateway") and provider._gateway is None:
                    provider._gateway = gw
