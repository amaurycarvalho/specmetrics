from __future__ import annotations


from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.extraction_registry import ProviderRouter
from specmetrics.kernel.extraction_stage import ExtractionStage
from specmetrics.kernel.pipeline_context import PipelineContext


class _MockProvider:
    def __init__(
        self, provider_id: str = "mock", supported_types: list[str] | None = None
    ) -> None:
        self._provider_id = provider_id
        self._supported_types = supported_types or ["section"]

    def supports_type(self, document_type: str) -> bool:
        return document_type in self._supported_types

    def extract(self, document: Document) -> ExtractionResult:
        return ExtractionResult(
            provider_id=self._provider_id,
            elements=[
                ExtractedElement(
                    id=f"{document.id}/elem-1",
                    type="fact",
                    confidence=0.95,
                    evidence=EvidenceReference(
                        document_id=document.id,
                        text=document.content[:50],
                    ),
                    content=f"Extracted from {document.id}",
                )
            ],
            processing_stats=ProcessingStats(
                documents_processed=1,
                elements_extracted=1,
                errors=0,
                duration_ms=10,
            ),
        )


def _make_event(documents: list[Document]) -> PipelineEvent:
    from uuid import uuid4

    context = PipelineContext(execution_id=uuid4()).with_stage_output(
        field_name="adapter_result",
        value={"documents": documents},
    )
    return PipelineEvent(
        event_type=EventType.DOCUMENTS_DISCOVERED,
        publisher="test",
        payload={},
        context=context,
    )


class TestExtractionStage:
    def test_handles_documents_discovered_event_and_returns_result(self):
        router = ProviderRouter()
        provider = _MockProvider("mock-1")
        router.register(provider, "mock-1", types=["section"])
        stage = ExtractionStage(router)

        doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="section",
            content="# Test document",
        )
        event = _make_event([doc])
        context = stage.handle(event)

        output = context.extraction_result
        assert output["total_elements"] == 1
        assert output["documents_processed"] == 1

    def test_routes_documents_to_correct_provider_based_on_type(self):
        router = ProviderRouter()
        provider_a = _MockProvider("provider-a", supported_types=["use_case"])
        provider_b = _MockProvider("provider-b", supported_types=["business_rule"])
        router.register(provider_a, "provider-a", types=["use_case"])
        router.register(provider_b, "provider-b", types=["business_rule"])
        stage = ExtractionStage(router)

        docs = [
            Document(
                id="uc-1",
                path="use-cases/login.md",
                document_type="use_case",
                content="# Login",
            ),
            Document(
                id="br-1",
                path="business-rules/pw.md",
                document_type="business_rule",
                content="# Password",
            ),
        ]
        event = _make_event(docs)
        context = stage.handle(event)

        output = context.extraction_result
        assert output["total_elements"] == 2
        assert output["documents_processed"] == 2

    def test_processes_multiple_documents_and_consolidates_results(self):
        router = ProviderRouter()
        provider = _MockProvider("mock-1", supported_types=["section"])
        router.register(provider, "mock-1", types=["section"])
        stage = ExtractionStage(router)

        docs = [
            Document(
                id="doc-1",
                path="specs/a.md",
                document_type="section",
                content="# Doc A",
            ),
            Document(
                id="doc-2",
                path="specs/b.md",
                document_type="section",
                content="# Doc B",
            ),
            Document(
                id="doc-3",
                path="specs/c.md",
                document_type="section",
                content="# Doc C",
            ),
        ]
        event = _make_event(docs)
        context = stage.handle(event)

        output = context.extraction_result
        assert output["total_elements"] == 3
        assert output["documents_processed"] == 3
        assert output["documents_skipped"] == 0
