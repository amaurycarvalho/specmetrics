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
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType
from specmetrics.plugins.semantic.llm_provider import LLMExtractionProvider
from specmetrics.plugins.stage.extraction import create_extraction_metadata


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


class TestExtractionStageMetadata:
    def test_create_extraction_metadata_field_values(self):
        meta = create_extraction_metadata()
        assert isinstance(meta, PluginMetadata)
        assert meta.id == "extraction_stage"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.SEMANTIC
        assert meta.handled_event_types == (EventType.DOCUMENTS_DISCOVERED,)
        assert meta.name == "Semantic Extraction Stage"
        assert (
            meta.description
            == "Routes specification documents to extraction providers and consolidates results"
        )
        assert meta.version == "0.1.0"
        assert meta.handler_factory is not None

    def test_create_extraction_metadata_registers_llm_provider(self):
        meta = create_extraction_metadata()
        stage = meta.handler_factory()
        providers = stage._router.list_providers()
        assert len(providers) == 1
        assert isinstance(providers[0], LLMExtractionProvider)


class TestIsLikelyBinary:
    def test_empty_content_is_not_binary(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("") is False

    def test_plain_text_is_not_binary(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("# Requirements for the system") is False

    def test_control_heavy_content_is_binary(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("\x00\x01\x02\x03" + "aaaa") is True

    def test_low_control_ratio_is_not_binary(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("\x01" + "aaaaa") is False

    def test_space_is_not_counted_as_control(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary(" ") is False

    def test_whitespace_excluded_from_control_count(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("\n\t") is False

    def test_boundary_ratio_thirty_percent(self) -> None:
        from specmetrics.kernel.extraction_stage import _is_likely_binary

        assert _is_likely_binary("\x01\x02\x03" + "aaaaaaa") is False


class _FakeProvider:
    def __init__(self) -> None:
        self._gateway = None


class TestInjectGateway:
    def _make_stage(self, router, gateway=None) -> ExtractionStage:
        return ExtractionStage(router, gateway=gateway)

    def test_injects_gateway_from_context(self) -> None:
        from specmetrics.kernel.extraction_registry import ProviderRouter

        router = ProviderRouter()
        provider = _FakeProvider()
        router.register(provider, "fake", types=["section"])
        stage = self._make_stage(router)
        gw = object()
        context = PipelineContext(metadata={"llm_gateway": gw})
        stage._inject_gateway(context)
        assert stage._gateway is gw

    def test_injects_gateway_into_providers(self) -> None:
        from specmetrics.kernel.extraction_registry import ProviderRouter

        router = ProviderRouter()
        provider = _FakeProvider()
        router.register(provider, "fake", types=["section"])
        stage = self._make_stage(router)
        gw = object()
        context = PipelineContext(metadata={"llm_gateway": gw})
        stage._inject_gateway(context)
        assert provider._gateway is gw

    def test_keeps_existing_gateway_on_stage(self) -> None:
        from specmetrics.kernel.extraction_registry import ProviderRouter

        router = ProviderRouter()
        existing = object()
        stage = self._make_stage(router, gateway=existing)
        context = PipelineContext(metadata={"llm_gateway": object()})
        stage._inject_gateway(context)
        assert stage._gateway is existing

    def test_does_not_inject_when_context_metadata_missing(self) -> None:
        from specmetrics.kernel.extraction_registry import ProviderRouter

        router = ProviderRouter()
        provider = _FakeProvider()
        router.register(provider, "fake", types=["section"])
        stage = self._make_stage(router)
        context = PipelineContext(metadata={})
        stage._inject_gateway(context)
        assert stage._gateway is None
        assert provider._gateway is None

    def test_does_not_overwrite_provider_gateway(self) -> None:
        from specmetrics.kernel.extraction_registry import ProviderRouter

        router = ProviderRouter()
        provider = _FakeProvider()
        provider._gateway = object()
        router.register(provider, "fake", types=["section"])
        stage = self._make_stage(router)
        gw = object()
        context = PipelineContext(metadata={"llm_gateway": gw})
        stage._inject_gateway(context)
        assert provider._gateway is not gw
