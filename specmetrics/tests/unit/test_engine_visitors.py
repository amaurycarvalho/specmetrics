from __future__ import annotations

from specmetrics.kernel.engine_visitors import (
    CodeBlockVisitor,
    EmphasisVisitor,
    ExtractionState,
    HeadingVisitor,
    LinkVisitor,
    ListVisitor,
    ParagraphVisitor,
    QuoteVisitor,
    TableVisitor,
)


def _make_token(
    type_: str, tag: str = "", content: str = "", nesting: int = 0, **kwargs: object
):
    from types import SimpleNamespace

    tok = SimpleNamespace(
        type=type_,
        tag=tag,
        content=content,
        nesting=nesting,
        level=kwargs.get("level", 0),
        info=kwargs.get("info", ""),
        children=kwargs.get("children", None),
        attrs=kwargs.get("attrs", {}),
        hidden=kwargs.get("hidden", False),
        map=kwargs.get("map", [0, 0]),
    )
    return tok


def _inline_token(content: str, children: list | None = None) -> object:
    return _make_token("inline", content=content, children=children)


class TestHeadingVisitor:
    def test_collects_heading_hierarchy(self) -> None:
        tokens = [
            _make_token("heading_open", tag="h1", nesting=1),
            _inline_token("Actors"),
            _make_token("heading_close", tag="h1", nesting=-1),
        ]
        state = ExtractionState()
        HeadingVisitor().visit(tokens, state)
        assert len(state.observations) == 1
        assert state.observations[0].type == "heading"
        assert "Actors" in state.observations[0].content

    def test_heading_stack_maintained(self) -> None:
        tokens = [
            _make_token("heading_open", tag="h1", nesting=1),
            _inline_token("Section 1"),
            _make_token("heading_close", tag="h1", nesting=-1),
            _make_token("heading_open", tag="h2", nesting=1),
            _inline_token("Subsection"),
            _make_token("heading_close", tag="h2", nesting=-1),
        ]
        state = ExtractionState()
        HeadingVisitor().visit(tokens, state)
        assert len(state.observations) == 2
        assert len(state.heading_stack) == 2

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        HeadingVisitor().visit([], state)
        assert len(state.observations) == 0


class TestListVisitor:
    def test_collects_unordered_list_items(self) -> None:
        tokens = [
            _make_token("bullet_list_open"),
            _make_token("list_item_open"),
            _inline_token("Item 1"),
            _make_token("list_item_close"),
            _make_token("list_item_open"),
            _inline_token("Item 2"),
            _make_token("list_item_close"),
            _make_token("bullet_list_close"),
        ]
        state = ExtractionState()
        ListVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        ListVisitor().visit([], state)
        assert len(state.observations) == 0


class TestTableVisitor:
    def test_collects_table_headers_and_rows(self) -> None:
        tokens = [
            _make_token("table_open"),
            _make_token("thead_open"),
            _make_token("tr_open"),
            _inline_token("Name"),
            _make_token("tr_close"),
            _make_token("thead_close"),
            _make_token("tbody_open"),
            _make_token("tr_open"),
            _inline_token("Alice"),
            _make_token("tr_close"),
            _make_token("tbody_close"),
            _make_token("table_close"),
        ]
        state = ExtractionState()
        TableVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        TableVisitor().visit([], state)
        assert len(state.observations) == 0


class TestCodeBlockVisitor:
    def test_collects_fenced_code_with_language(self) -> None:
        tokens = [_make_token("fence", content="print('hello')", info="python")]
        state = ExtractionState()
        CodeBlockVisitor().visit(tokens, state)
        assert len(state.observations) >= 1
        assert state.observations[0].context.get("language") == "python"

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        CodeBlockVisitor().visit([], state)
        assert len(state.observations) == 0


class TestQuoteVisitor:
    def test_collects_blockquote_content(self) -> None:
        tokens = [
            _make_token("blockquote_open"),
            _inline_token("Quoted text"),
            _make_token("blockquote_close"),
        ]
        state = ExtractionState()
        QuoteVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        QuoteVisitor().visit([], state)
        assert len(state.observations) == 0


class TestEmphasisVisitor:
    def test_collects_strong_text(self) -> None:
        child = _make_token("strong", tag="strong", content="important")
        tokens = [_inline_token("text with emphasis", children=[child])]
        state = ExtractionState()
        EmphasisVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        EmphasisVisitor().visit([], state)
        assert len(state.observations) == 0


class TestLinkVisitor:
    def test_collects_links(self) -> None:
        child = _make_token("link_open", attrs={"href": "https://example.com"})
        tokens = [_inline_token("click here", children=[child])]
        state = ExtractionState()
        LinkVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        LinkVisitor().visit([], state)
        assert len(state.observations) == 0


class TestParagraphVisitor:
    def test_collects_standalone_paragraph(self) -> None:
        tokens = [_inline_token("This is a standalone paragraph.")]
        state = ExtractionState()
        ParagraphVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_skips_inline_inside_heading(self) -> None:
        tokens = [
            _make_token("heading_open", tag="h1", nesting=1),
            _inline_token("Title"),
            _make_token("heading_close", tag="h1", nesting=-1),
            _inline_token("Paragraph text"),
        ]
        state = ExtractionState()
        ParagraphVisitor().visit(tokens, state)
        assert len(state.observations) >= 1

    def test_empty_tokens_no_error(self) -> None:
        state = ExtractionState()
        ParagraphVisitor().visit([], state)
        assert len(state.observations) == 0
