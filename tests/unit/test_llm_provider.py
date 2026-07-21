from __future__ import annotations

import json
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


_GATEWAY_MODULE = "specmetrics.kernel.llm_gateway"


class TestLLMProviderValidResponse:
    def setup_method(self) -> None:
        self.provider = LLMExtractionProvider(api_key="test-key")
        self.doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="use_case",
            content="# Login Use Case\nUser enters credentials.",
        )

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    def test_returns_extraction_result_with_elements(self, mock_litellm: MagicMock):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            f"{self.doc.id}/chunk-0": {"elements": [{"type": "fact", "confidence": 0.95, "content": "User can log in"}]}
        })
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_litellm.completion.return_value = mock_response
        result = self.provider.extract(self.doc)
        assert result.provider_id == "llm-provider"
        assert len(result.elements) == 1
        assert result.elements[0].type == "fact"

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    def test_preserves_evidence_references(self, mock_litellm: MagicMock):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            f"{self.doc.id}/chunk-0": {"elements": [{"type": "fact", "confidence": 0.9, "content": "System authenticates user"}]}
        })
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_litellm.completion.return_value = mock_response
        result = self.provider.extract(self.doc)
        assert len(result.elements) == 1
        elem = result.elements[0]
        assert elem.evidence.document_id == "doc-1"
        assert len(elem.evidence.text) > 0

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    def test_processes_multiple_elements(self, mock_litellm: MagicMock):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            f"{self.doc.id}/chunk-0": {"elements": [
                {"type": "fact", "confidence": 0.9, "content": "Login"},
                {"type": "operation", "confidence": 0.8, "content": "Validate password"},
            ]}
        })
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_litellm.completion.return_value = mock_response
        result = self.provider.extract(self.doc)
        assert len(result.elements) == 2


class TestLLMProviderGracefulDegradation:
    def setup_method(self) -> None:
        self.provider = LLMExtractionProvider(api_key="test-key")
        self.doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="section",
            content="# Test\nContent here.",
            sections=[
                DocumentSection(
                    id="sec-1", title="Test", level=1, content="Content here."
                )
            ],
        )

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    @patch("time.sleep", return_value=None)
    def test_falls_back_to_deterministic_engine_on_llm_error(
        self, mock_sleep: MagicMock, mock_litellm: MagicMock
    ):
        doc = Document(
            id="doc-story",
            path="specs/story.md",
            document_type="section",
            content="# Test\nAs a User, I want to login, So that I can access my account",
        )
        mock_litellm.completion.side_effect = Exception("API key not configured")
        result = self.provider.extract(doc)
        assert len(result.elements) >= 1
        assert result.elements[0].type == "entity"

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    @patch("time.sleep", return_value=None)
    def test_structural_parse_preserves_evidence(self, mock_sleep: MagicMock, mock_litellm: MagicMock):
        mock_litellm.completion.side_effect = Exception("Network error")
        result = self.provider.extract(self.doc)
        for elem in result.elements:
            assert isinstance(elem.evidence, EvidenceReference)
            assert elem.evidence.document_id == "doc-1"

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    @patch("time.sleep", return_value=None)
    def test_structural_parse_handles_empty_sections(self, mock_sleep: MagicMock, mock_litellm: MagicMock):
        doc = Document(
            id="empty-doc",
            path="specs/empty.md",
            document_type="section",
            content="",
            sections=[],
        )
        mock_litellm.completion.side_effect = Exception("Unavailable")
        result = self.provider.extract(doc)
        assert len(result.elements) == 0
        assert result.processing_stats.errors == 0

    @patch(f"{_GATEWAY_MODULE}.HAS_LITELLM", True)
    @patch(f"{_GATEWAY_MODULE}.litellm")
    @patch("time.sleep", return_value=None)
    def test_returns_processing_stats(self, mock_sleep: MagicMock, mock_litellm: MagicMock):
        mock_litellm.completion.side_effect = Exception("Timeout")
        result = self.provider.extract(self.doc)
        assert result.processing_stats.documents_processed == 1
        assert result.processing_stats.elements_extracted == len(result.elements)


class TestLLMProviderConfigCheck:
    def setup_method(self) -> None:
        LLMExtractionProvider._no_key = False
        LLMExtractionProvider._config_warned = False
        self.provider = LLMExtractionProvider()
        self.doc = Document(
            id="doc-1",
            path="specs/test.md",
            document_type="section",
            content="# Test\nContent here.",
        )

    def test_skips_llm_and_uses_structural_when_no_key(self):
        result = self.provider.extract(self.doc)
        assert result.processing_stats.documents_processed == 1
        assert result.provider_id == "llm-provider"

    def test_config_schema_returns_llm_provider_config(self):
        schema = LLMExtractionProvider.config_schema()
        from specmetrics.plugins.semantic.llm_provider import LLMProviderConfig

        assert schema is LLMProviderConfig
