from __future__ import annotations

from unittest.mock import patch

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.semantic_extraction_engine import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
)
from specmetrics.plugins.semantic._content import (
    append_chunk_elements,
    build_doc_payloads,
    chunk_content,
    parse_response,
    run_deterministic_fallback,
)


def _doc(content: str = "Some content", document_type: str = "section") -> Document:
    return Document(
        id="doc-1",
        path="specs/test.md",
        document_type=document_type,
        content=content,
    )


class TestChunkContent:
    def test_single_chunk_when_within_size(self):
        chunks = chunk_content("short content", 100)
        assert chunks == [("short content", 0)]

    def test_breaks_at_paragraph_boundary(self):
        content = "para one\n\npara two\n\npara three"
        chunks = chunk_content(content, 12)
        assert len(chunks) > 1
        assert all(text and isinstance(idx, int) for text, idx in chunks)
        assert chunks[0][0] == "para one\n\n"

    def test_breaks_at_line_boundary_when_no_blank_line(self):
        content = "line one\nline two\nline three"
        chunks = chunk_content(content, 9)
        assert chunks[0][0] == "line one\n"

    def test_hard_cut_when_no_boundary(self):
        chunks = chunk_content("abcdef", 3)
        assert chunks[0][0] == "abc"
        assert chunks[1][0] == "def"

    def test_concatenation_is_lossless(self):
        content = ("abc\n\n" * 5) + "tail"
        chunks = chunk_content(content, 6)
        joined = "".join(text for text, _ in chunks)
        assert joined == content


class TestBuildDocPayloads:
    def test_builds_one_payload_per_chunk(self):
        doc = _doc()
        payloads = build_doc_payloads(doc, [("chunk A", 0), ("chunk B", 1)])
        assert len(payloads) == 2
        assert payloads[0].document_id == "doc-1/chunk-0"
        assert payloads[1].document_id == "doc-1/chunk-1"
        assert payloads[0].content == "chunk A"
        assert payloads[0].document_type == doc.document_type


class _FakeDetEngine:
    def __init__(self, extract_fn) -> None:
        self._extract_fn = extract_fn

    def extract(self, documents):
        return self._extract_fn(documents)


class TestRunDeterministicFallback:
    def _det_element(self, element_id: str) -> ExtractedElement:
        return ExtractedElement(
            id=element_id,
            type="fact",
            confidence=0.8,
            evidence=EvidenceReference(
                document_id="doc-1",
                section_id="sec-1",
                text="evidence text",
            ),
            content="element content",
        )

    def test_success_converts_elements(self):
        fake = _FakeDetEngine(
            lambda docs: ExtractionResult(
                elements=[self._det_element("e-1"), self._det_element("e-2")],
                engine_id="deterministic",
                processing_stats=ProcessingStats(documents_processed=1),
            )
        )
        with patch(
            "specmetrics.plugins.semantic._content.DeterministicSemanticEngine",
            return_value=fake,
        ):
            elements, error_flag = run_deterministic_fallback(_doc())
        assert error_flag == 0
        assert len(elements) == 2
        assert elements[0].id == "e-1"
        assert elements[0].evidence.document_id == "doc-1"

    def test_exception_returns_error_flag(self):
        def boom(docs):
            raise RuntimeError("boom")

        fake = _FakeDetEngine(boom)
        with patch(
            "specmetrics.plugins.semantic._content.DeterministicSemanticEngine",
            return_value=fake,
        ):
            elements, error_flag = run_deterministic_fallback(_doc())
        assert elements == []
        assert error_flag == 1


class TestAppendChunkElements:
    def test_with_chunk_index_sets_section(self):
        doc = _doc()
        out: list[ExtractedElement] = []
        count = append_chunk_elements(
            "doc-1/chunk-3",
            [{"type": "fact", "confidence": 0.9, "content": "text"}],
            doc,
            out,
        )
        assert count == 1
        assert out[0].evidence.section_id == "chunk-3"
        assert out[0].id == "doc-1/llm-3-0"

    def test_non_numeric_chunk_index_caught(self):
        doc = _doc()
        out: list[ExtractedElement] = []
        count = append_chunk_elements(
            "doc-1/chunk-abc",
            [{"type": "fact", "content": "text"}],
            doc,
            out,
        )
        assert count == 1
        assert out[0].evidence.section_id is None

    def test_plain_doc_id_no_chunk(self):
        doc = _doc()
        out: list[ExtractedElement] = []
        count = append_chunk_elements(
            "some-other-id",
            [{"type": "entity", "confidence": 0.5, "content": "x"}],
            doc,
            out,
        )
        assert count == 1
        assert out[0].evidence.section_id is None
        assert out[0].type == "entity"

    def test_clamps_confidence(self):
        doc = _doc()
        out: list[ExtractedElement] = []
        append_chunk_elements(
            "doc-1/chunk-0",
            [{"type": "fact", "confidence": 2.0, "content": "high"}],
            doc,
            out,
        )
        append_chunk_elements(
            "doc-1/chunk-0",
            [{"type": "fact", "confidence": -1.0, "content": "low"}],
            doc,
            out,
        )
        assert out[0].confidence == 1.0
        assert out[1].confidence == 0.0


class TestParseResponse:
    def test_parses_list(self):
        elements = parse_response(
            '[{"type": "entity", "confidence": 0.8, "content": "one"}]',
            _doc(),
            lambda doc: ([], 0),
        )
        assert len(elements) == 1
        assert elements[0].type == "entity"
        assert elements[0].content == "one"

    def test_parses_dict_elements_key(self):
        elements = parse_response(
            '{"elements": [{"type": "fact", "confidence": 0.7, "content": "two"}]}',
            _doc(),
            lambda doc: ([], 0),
            chunk_idx=4,
        )
        assert len(elements) == 1
        assert elements[0].id == "doc-1/llm-4-0"
        assert elements[0].evidence.section_id == "chunk-4"

    def test_invalid_json_falls_back(self):
        def fallback(doc: Document):
            return [ExtractedElement(
                id="fb",
                type="fact",
                confidence=0.5,
                evidence=EvidenceReference(
                    document_id=doc.id, section_id=None, text="fb"
                ),
                content="fb",
            )], 0

        elements = parse_response("not json", _doc(), fallback)
        assert len(elements) == 1
        assert elements[0].id == "fb"

    def test_non_list_dict_without_elements_returns_empty(self):
        elements = parse_response(
            '{"foo": "bar"}',
            _doc(),
            lambda doc: ([], 0),
        )
        assert elements == []

    def test_clamps_confidence_in_parse(self):
        elements = parse_response(
            '[{"type": "fact", "confidence": 5.0, "content": "c"}]',
            _doc(),
            lambda doc: ([], 0),
        )
        assert elements[0].confidence == 1.0