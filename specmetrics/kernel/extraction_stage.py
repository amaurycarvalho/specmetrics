from __future__ import annotations


import structlog

from .events import EventType, PipelineEvent
from .extraction_provider import ExtractionResult
from .extraction_registry import ProviderRouter
from .handler_registry import EventHandler
from .pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


class ExtractionStage(EventHandler):
    """Pipeline stage that extracts semantic elements from specification documents.

    Consumes DocumentsDiscovered events, routes documents to registered
    extraction providers, and consolidates results into the pipeline context.
    """

    def __init__(self, router: ProviderRouter) -> None:
        self._router = router
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

    def handle(self, event: PipelineEvent) -> PipelineContext:
        context = event.context
        docs_data = getattr(context, "adapter_result", None) or {}
        documents = docs_data.get("documents", [])
        results: dict[str, ExtractionResult] = {}
        total_elements = 0
        documents_processed = 0
        documents_skipped = 0

        for doc in documents:
            try:
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
                    results[pid].processing_stats.elements_extracted += len(result.elements)
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
