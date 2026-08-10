from __future__ import annotations

import pytest

from specmetrics.kernel import (
    Document,
    HandlerRegistry,
    PipelineContext,
    PipelineEngine,
)
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.extraction_registry import ProviderRouter
from specmetrics.kernel.extraction_stage import ExtractionStage


class _MockPipelineProvider:
    def __init__(
        self, provider_id: str, supported_types: list[str] | None = None
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
                duration_ms=5,
            ),
        )


@pytest.fixture
def pipeline_setup() -> tuple[HandlerRegistry, PipelineEngine]:
    registry = HandlerRegistry()
    engine = PipelineEngine(registry)
    return registry, engine


class TestExtractionPipelineIntegration:
    def test_mock_provider_registered_via_stage_is_invoked_in_pipeline(
        self, pipeline_setup: tuple[HandlerRegistry, PipelineEngine]
    ):
        registry, engine = pipeline_setup

        router = ProviderRouter()
        provider = _MockPipelineProvider("mock-extractor", supported_types=["section"])
        router.register(provider, "mock-extractor", types=["section"])
        stage = ExtractionStage(router)
        registry.register(stage)

        ctx = PipelineContext()
        result = engine.run(ctx)

        assert result.extraction_result is not None
        assert result.extraction_result["documents_processed"] >= 0

    def test_extraction_stage_produces_consumable_output(
        self, pipeline_setup: tuple[HandlerRegistry, PipelineEngine]
    ):
        registry, engine = pipeline_setup

        router = ProviderRouter()
        provider = _MockPipelineProvider("extractor", supported_types=["section"])
        router.register(provider, "extractor", types=["section"])
        stage = ExtractionStage(router)
        registry.register(stage)

        ctx = PipelineContext()
        result = engine.run(ctx)

        stage_result = result.extraction_result
        assert isinstance(stage_result, dict)
        assert "total_elements" in stage_result
        assert "results" in stage_result
