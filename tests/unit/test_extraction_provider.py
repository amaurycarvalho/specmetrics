from __future__ import annotations

from typing import Protocol, runtime_checkable


from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.extraction_provider import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)


class TestExtractionProviderProtocol:
    def test_valid_provider_passes_structural_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def extract(self, document: Document) -> ExtractionResult:
                ...

            def supports_type(self, document_type: str) -> bool:
                ...

        class ValidProvider:
            def extract(self, document: Document) -> ExtractionResult:
                return ExtractionResult(
                    provider_id="test",
                    elements=[],
                    processing_stats=ProcessingStats(),
                )

            def supports_type(self, document_type: str) -> bool:
                return True

        provider = ValidProvider()
        assert isinstance(provider, CheckableProtocol)

    def test_provider_missing_extract_fails_structural_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def extract(self, document: Document) -> ExtractionResult:
                ...

            def supports_type(self, document_type: str) -> bool:
                ...

        class MissingExtract:
            def supports_type(self, document_type: str) -> bool:
                return True

        provider = MissingExtract()
        assert not isinstance(provider, CheckableProtocol)

    def test_provider_missing_supports_type_fails_structural_check(self):
        @runtime_checkable
        class CheckableProtocol(Protocol):
            def extract(self, document: Document) -> ExtractionResult:
                ...

            def supports_type(self, document_type: str) -> bool:
                ...

        class MissingSupportsType:
            def extract(self, document: Document) -> ExtractionResult:
                return ExtractionResult(
                    provider_id="test",
                    elements=[],
                    processing_stats=ProcessingStats(),
                )

        provider = MissingSupportsType()
        assert not isinstance(provider, CheckableProtocol)


class TestEvidenceReference:
    def test_accepts_valid_document_id_and_text(self):
        ref = EvidenceReference(document_id="doc-1", text="Some content")
        assert ref.document_id == "doc-1"
        assert ref.text == "Some content"
        assert ref.section_id is None

    def test_accepts_optional_section_id(self):
        ref = EvidenceReference(document_id="doc-1", section_id="sec-2", text="Content")
        assert ref.section_id == "sec-2"


class TestExtractedElement:
    def test_requires_valid_evidence_reference(self):
        evidence = EvidenceReference(document_id="doc-1", text="Source text")
        element = ExtractedElement(
            id="elem-1",
            type="fact",
            confidence=0.95,
            evidence=evidence,
            content="Extracted fact",
        )
        assert element.id == "elem-1"
        assert element.type == "fact"
        assert element.confidence == 0.95
        assert element.evidence.document_id == "doc-1"
