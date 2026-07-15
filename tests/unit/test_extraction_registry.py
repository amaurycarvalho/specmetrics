from __future__ import annotations

from typing import Optional

import pytest

from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.kernel.extraction_registry import ProviderRouter


class _MockProvider:
    def __init__(self, provider_id: str, supported_types: Optional[list[str]] = None) -> None:
        self._provider_id = provider_id
        self._supported_types = supported_types or []

    def supports_type(self, document_type: str) -> bool:
        return document_type in self._supported_types

    def extract(self, document) -> ExtractionResult:
        return ExtractionResult(
            provider_id=self._provider_id,
            elements=[],
            processing_stats=ProcessingStats(),
        )


class TestProviderRouter:
    def test_register_stores_provider_for_document_type(self):
        router = ProviderRouter()
        provider = _MockProvider("p1", supported_types=["use_case"])
        router.register(provider, "p1", types=["use_case"])
        resolved = router.resolve("use_case")
        assert resolved is not None

    def test_resolve_returns_correct_provider_for_matching_type(self):
        router = ProviderRouter()
        provider_a = _MockProvider("pa", supported_types=["use_case"])
        provider_b = _MockProvider("pb", supported_types=["business_rule"])
        router.register(provider_a, "pa", types=["use_case"])
        router.register(provider_b, "pb", types=["business_rule"])
        assert router.resolve("use_case") is provider_a
        assert router.resolve("business_rule") is provider_b

    def test_resolve_returns_none_when_no_provider_matches(self):
        router = ProviderRouter()
        provider = _MockProvider("p1", supported_types=["use_case"])
        router.register(provider, "p1", types=["use_case"])
        resolved = router.resolve("unknown_type")
        assert resolved is None
