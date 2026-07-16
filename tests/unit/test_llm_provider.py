from __future__ import annotations

from unittest.mock import patch, MagicMock

from specmetrics.kernel.adapter_interface import Document, DocumentSection
from specmetrics.kernel.extraction_provider import EvidenceReference
from specmetrics.plugins.semantic.llm_provider import LLMExtractionProvider


class _MockResponse:
    class Choice:
        class Message:
            def __init__(self, content: str) -> None:
                self.content = content

        def __init__(self, content: str) -> None:
            self.message = self.Message(content)

    def __init__(self, content: str) -> None:
        self.choices = [self.Choice(content)]


class TestLLMProviderValidResponse:
    def setup_method(self) -> None:
        self.provider = LLMExtractionProvider()
        self.doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="use_case",
            content="# Login Use Case\nUser enters credentials.",
        )

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_returns_extraction_result_with_elements(self, mock_litellm: MagicMock):
        mock_litellm.completion.return_value = _MockResponse(
            '[{"type": "fact", "confidence": 0.95, "content": "User can log in"}]'
        )
        result = self.provider.extract(self.doc)
        assert result.provider_id == "llm-provider"
        assert len(result.elements) == 1
        assert result.elements[0].type == "fact"

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_preserves_evidence_references(self, mock_litellm: MagicMock):
        mock_litellm.completion.return_value = _MockResponse(
            '[{"type": "fact", "confidence": 0.9, "content": "System authenticates user"}]'
        )
        result = self.provider.extract(self.doc)
        assert len(result.elements) == 1
        elem = result.elements[0]
        assert elem.evidence.document_id == "doc-1"
        assert len(elem.evidence.text) > 0

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_processes_multiple_elements(self, mock_litellm: MagicMock):
        mock_litellm.completion.return_value = _MockResponse(
            '[{"type": "fact", "confidence": 0.9, "content": "Login"}, {"type": "operation", "confidence": 0.8, "content": "Validate password"}]'
        )
        result = self.provider.extract(self.doc)
        assert len(result.elements) == 2


class TestLLMProviderGracefulDegradation:
    def setup_method(self) -> None:
        self.provider = LLMExtractionProvider()
        self.doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="section",
            content="# Test\nContent here.",
            sections=[DocumentSection(id="sec-1", title="Test", level=1, content="Content here.")],
        )

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_falls_back_to_structural_parse_on_llm_error(self, mock_litellm: MagicMock):
        mock_litellm.completion.side_effect = Exception("API key not configured")
        result = self.provider.extract(self.doc)
        assert len(result.elements) >= 1
        assert result.elements[0].type == "fact"

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_structural_parse_preserves_evidence(self, mock_litellm: MagicMock):
        mock_litellm.completion.side_effect = Exception("Network error")
        result = self.provider.extract(self.doc)
        for elem in result.elements:
            assert isinstance(elem.evidence, EvidenceReference)
            assert elem.evidence.document_id == "doc-1"

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_structural_parse_handles_empty_sections(self, mock_litellm: MagicMock):
        doc = Document(
            id="empty-doc",
            path="specs/empty.md",
            document_type="section",
            content="",
            sections=[],
        )
        mock_litellm.completion.side_effect = Exception("Unavailable")
        result = self.provider.extract(doc)
        assert len(result.elements) >= 1
        assert result.elements[0].type == "section"

    @patch("specmetrics.plugins.semantic.llm_provider.litellm")
    def test_returns_processing_stats(self, mock_litellm: MagicMock):
        mock_litellm.completion.side_effect = Exception("Timeout")
        result = self.provider.extract(self.doc)
        assert result.processing_stats.documents_processed == 1
        assert result.processing_stats.elements_extracted == len(result.elements)
