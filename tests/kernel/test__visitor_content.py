"""Tests for specmetrics.kernel._visitor_content."""

from __future__ import annotations

from markdown_it.token import Token

from specmetrics.kernel._visitor_content import (
    CodeBlockVisitor,
    EmphasisVisitor,
    LinkVisitor,
    ParagraphVisitor,
    QuoteVisitor,
    _heading_path,
    _section_location,
)
from specmetrics.kernel._visitor_state import ExtractionState, Observation


def _tok(
    type_: str,
    content: str = "",
    info: str = "",
    tag: str = "",
    attrs: dict | None = None,
    children: list[Token] | None = None,
) -> Token:
    t = Token(type_, tag, 0)
    t.content = content
    t.info = info
    if attrs is not None:
        t.attrs = attrs
    if children is not None:
        t.children = children
    return t


def _state(heading_stack: list[str] | None = None) -> ExtractionState:
    st = ExtractionState()
    if heading_stack is not None:
        st.heading_stack = list(heading_stack)
    return st


def test_heading_path_joins_with_slash():
    """Kills _heading_path__mutmut_2 (separator '/' -> 'XX/XX')."""
    state = _state(["A", "B", "C"])
    assert _heading_path(state) == "A/B/C"


def test_section_location_returns_path_when_stack_non_empty():
    """Kills QuoteVisitor::visit__mutmut_30, CodeBlockVisitor::visit__mutmut_24,
    EmphasisVisitor::visit__mutmut_35, ParagraphVisitor::visit__mutmut_31
    (variants that would pass None to _section_location or drop the tuple)."""
    state = _state(["top"])
    assert _section_location(state) == "top"
    assert _section_location(_state([])) is None


def test_paragraph_recorded_at_top_level():
    """Kills ParagraphVisitor::visit__mutmut_24/32/33 (type 'paragraph'),
    __mutmut_31/37 (location tuple) and __mutmut_30/34/35 (context)."""
    state = _state(["h1"])
    tokens = [_tok("inline", "  hello world  ")]
    ParagraphVisitor().visit(tokens, state)
    assert len(state.observations) == 1
    ob = state.observations[0]
    assert ob.type == "paragraph"
    assert ob.content == "hello world"
    assert ob.context == {"heading_path": "h1"}
    assert ob.location == ("", "h1")


def test_paragraph_location_empty_heading():
    """Kills ParagraphVisitor::visit__mutmut_31 (location arg dropped)."""
    state = _state([])
    ParagraphVisitor().visit([_tok("inline", "text")], state)
    assert state.observations[0].location == ("", None)


def test_paragraph_skips_inside_single_container():
    """Kills ParagraphVisitor::visit__mutmut_16 (and -> or: inline at depth>0)."""
    state = _state([])
    tokens = [
        _tok("bullet_list_open"),
        _tok("inline", "nested"),
        _tok("bullet_list_close"),
    ]
    ParagraphVisitor().visit(tokens, state)
    assert state.observations == []


def test_paragraph_depth_after_two_containers_and_one_close():
    """Kills ParagraphVisitor::visit__mutmut_4 (depth += 1 -> = 1),
    __mutmut_5 (depth += 1 -> -= 1) and __mutmut_15 (depth - 1 -> depth - 2)."""
    state = _state([])
    tokens = [
        _tok("bullet_list_open"),
        _tok("bullet_list_open"),
        _tok("bullet_list_close"),
        _tok("inline", "still nested"),
    ]
    ParagraphVisitor().visit(tokens, state)
    assert state.observations == []


def test_paragraph_depth_recovers_after_full_close():
    """Kills ParagraphVisitor::visit__mutmut_5 (depth -= 1 would go negative)."""
    state = _state([])
    tokens = [
        _tok("bullet_list_open"),
        _tok("bullet_list_open"),
        _tok("bullet_list_close"),
        _tok("bullet_list_close"),
        _tok("inline", "top level"),
    ]
    ParagraphVisitor().visit(tokens, state)
    assert len(state.observations) == 1
    assert state.observations[0].content == "top level"


def test_codeblock_records_fence():
    """Kills CodeBlockVisitor::visit__mutmut_1/2/3 (fence check) and
    __mutmut_8/12/16/17 (type 'code_block')."""
    state = _state(["h"])
    tok = _tok("fence", "code line", info="python")
    CodeBlockVisitor().visit([tok], state)
    assert len(state.observations) == 1
    ob = state.observations[0]
    assert ob.type == "code_block"
    assert ob.content == "code line"


def test_codeblock_language_default_empty():
    """Kills CodeBlockVisitor::visit__mutmut_4 (language -> None) and
    __mutmut_6 (default '' -> 'XXXX')."""
    state = _state([])
    CodeBlockVisitor().visit([_tok("fence", "x", info="")], state)
    assert state.observations[0].context["language"] == ""


def test_codeblock_language_from_info():
    """Kills CodeBlockVisitor::visit__mutmut_5 (or -> and)."""
    state = _state([])
    CodeBlockVisitor().visit([_tok("fence", "x", info=" python ")], state)
    assert state.observations[0].context["language"] == "python"


def test_codeblock_observation_fields():
    """Kills CodeBlockVisitor::visit__mutmut_7 (ob=None), __mutmut_9/13
    (content), __mutmut_10/14 (context), __mutmut_11/15/23/24 (location)
    and __mutmut_25 (append(None))."""
    state = _state(["s1"])
    CodeBlockVisitor().visit([_tok("fence", "body", info="")], state)
    ob = state.observations[-1]
    assert isinstance(ob, Observation)
    assert ob.content == "body"
    assert ob.context == {"language": "", "heading_path": "s1"}
    assert ob.location == ("", "s1")


def test_codeblock_location_empty_heading():
    """Kills CodeBlockVisitor::visit__mutmut_11 (location -> None)."""
    state = _state([])
    CodeBlockVisitor().visit([_tok("fence", "x")], state)
    assert state.observations[0].location == ("", None)


def test_quote_records_single_line():
    """Kills QuoteVisitor::visit__mutmut_4/5/6 (blockquote_open check),
    __mutmut_7/8 (in_quote=True), __mutmut_10/11/12 (blockquote_close check),
    __mutmut_15 (ob=None) and __mutmut_16/20/24/25 (type 'blockquote')."""
    state = _state(["q"])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "  quoted  "),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert len(state.observations) == 1
    ob = state.observations[0]
    assert isinstance(ob, Observation)
    assert ob.type == "blockquote"
    assert ob.content == "quoted"
    assert ob.context == {"heading_path": "q"}
    assert ob.location == ("", "q")


def test_quote_joins_multiple_lines_with_newline():
    """Kills QuoteVisitor::visit__mutmut_17/21 (content=None) and
    __mutmut_27 ('\\n' -> 'XX\\nXX')."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "line one"),
        _tok("inline", "line two"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert state.observations[0].content == "line one\nline two"


def test_quote_skips_inline_before_any_open():
    """Kills QuoteVisitor::visit__mutmut_2 (initial in_quote False -> True)."""
    state = _state([])
    tokens = [
        _tok("inline", "stray"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert state.observations == []


def test_quote_resets_flag_after_close():
    """Kills QuoteVisitor::visit__mutmut_14 (in_quote False -> True after close)."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "a"),
        _tok("blockquote_close"),
        _tok("inline", "b"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert len(state.observations) == 1
    assert state.observations[0].content == "a"


def test_quote_multiple_blocks():
    """Kills QuoteVisitor::visit__mutmut_34 (parts=None after close) and
    __mutmut_9 (parts=[] -> None on open)."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "first"),
        _tok("blockquote_close"),
        _tok("blockquote_open"),
        _tok("inline", "second"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert [o.content for o in state.observations] == ["first", "second"]


def test_quote_only_inline_inside_quote_append():
    """Kills QuoteVisitor::visit__mutmut_39 (parts.append(None))."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "quoted"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert state.observations[0].content == "quoted"


def test_quote_inline_requires_open_flag():
    """Kills QuoteVisitor::visit__mutmut_35 (and -> or)."""
    state = _state([])
    tokens = [
        _tok("blockquote_close"),
        _tok("inline", "stray"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert state.observations == []


def test_quote_inline_within_open():
    """Kills QuoteVisitor::visit__mutmut_36 (== -> != on 'inline'),
    __mutmut_37/38 (string literal)."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "quoted"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert len(state.observations) == 1
    assert state.observations[0].content == "quoted"


def test_quote_context_and_location():
    """Kills QuoteVisitor::visit__mutmut_18/22/28/29 (context variants) and
    __mutmut_19/23/31/32 (location variants)."""
    state = _state(["sec"])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "x"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    ob = state.observations[0]
    assert ob.context == {"heading_path": "sec"}
    assert ob.location == ("", "sec")


def test_quote_appends_observation_object():
    """Kills QuoteVisitor::visit__mutmut_33 (append(None))."""
    state = _state([])
    tokens = [
        _tok("blockquote_open"),
        _tok("inline", "x"),
        _tok("blockquote_close"),
    ]
    QuoteVisitor().visit(tokens, state)
    assert state.observations[-1].type == "blockquote"


def test_emphasis_records_strong():
    """Kills EmphasisVisitor::visit__mutmut_2/3/4 (inline check),
    __mutmut_5/6/7/8/9 (strong/em membership), __mutmut_11/12/13/14/15/16
    (hasattr variants) and __mutmut_18 (ob=None)."""
    state = _state(["h"])
    child = _tok("strong", "bold", tag="strong")
    tok = _tok("inline", "**bold**", children=[child])
    EmphasisVisitor().visit([tok], state)
    assert len(state.observations) == 1
    ob = state.observations[0]
    assert isinstance(ob, Observation)
    assert ob.content == "bold"
    assert ob.context == {"emphasis_type": "strong", "heading_path": "h"}
    assert ob.location == ("", "h")


def test_emphasis_records_em():
    """Kills EmphasisVisitor::visit__mutmut_8/9 (em string literals)."""
    state = _state([])
    child = _tok("em", "ital", tag="em")
    tok = _tok("inline", "*ital*", children=[child])
    EmphasisVisitor().visit([tok], state)
    assert len(state.observations) == 1
    assert state.observations[0].context["emphasis_type"] == "em"


def test_emphasis_type_string():
    """Kills EmphasisVisitor::visit__mutmut_19/23/27/28 (type 'emphasis')."""
    state = _state([])
    child = _tok("strong", "x", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "**x**", children=[child])], state)
    assert state.observations[0].type == "emphasis"


def test_emphasis_content_field():
    """Kills EmphasisVisitor::visit__mutmut_20/24 (content=text -> None/deleted)."""
    state = _state([])
    child = _tok("strong", "value", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "**value**", children=[child])], state)
    assert state.observations[0].content == "value"


def test_emphasis_context_field():
    """Kills EmphasisVisitor::visit__mutmut_21/25 (context -> None/deleted)."""
    state = _state(["p"])
    child = _tok("em", "v", tag="em")
    EmphasisVisitor().visit([_tok("inline", "*v*", children=[child])], state)
    assert state.observations[0].context == {"emphasis_type": "em", "heading_path": "p"}


def test_emphasis_location_field():
    """Kills EmphasisVisitor::visit__mutmut_22/26/34/35 (location variants)."""
    state = _state(["p"])
    child = _tok("strong", "v", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "**v**", children=[child])], state)
    assert state.observations[0].location == ("", "p")


def test_emphasis_ignores_child_without_content():
    """Kills EmphasisVisitor::visit__mutmut_10 (text=None) and __mutmut_15/16
    (hasattr attribute name change)."""
    state = _state([])
    child = _tok("strong", "", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "** **", children=[child])], state)
    assert state.observations == []
    child2 = _tok("strong", "x", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "**x**", children=[child2])], state)
    assert len(state.observations) == 1
    assert state.observations[0].content == "x"


def test_emphasis_requires_inline_type():
    """Kills EmphasisVisitor::visit__mutmut_1 (and -> or on inline check)."""
    state = _state([])
    child = _tok("strong", "bold", tag="strong")
    non_inline = _tok("paragraph_open", "", children=[child])
    EmphasisVisitor().visit([non_inline], state)
    assert state.observations == []


def test_emphasis_appends_observation():
    """Kills EmphasisVisitor::visit__mutmut_36 (append(None))."""
    state = _state([])
    child = _tok("strong", "x", tag="strong")
    EmphasisVisitor().visit([_tok("inline", "**x**", children=[child])], state)
    assert state.observations[-1].content == "x"


def test_link_records_href_and_text():
    """Kills LinkVisitor::visit__mutmut_2/3/4 (inline check),
    __mutmut_5/6/7 (link_open check) and __mutmut_8 (tuple -> None)."""
    state = _state(["h"])
    child = _tok("link_open", "", tag="a", attrs={"href": "http://x.com"})
    text = _tok("text", "site", tag="")
    tok = _tok("inline", "[site](http://x.com)", children=[child, text])
    LinkVisitor().visit([tok], state)
    assert len(state.observations) == 1
    ob = state.observations[0]
    assert ob.type == "link"
    assert ob.content == "site (http://x.com)"
    assert ob.context == {"url": "http://x.com", "link_text": "site", "heading_path": "h"}
    assert ob.location == ("", "h")


def test_link_target_child_and_tok():
    """Kills LinkVisitor::visit__mutmut_9/10/11/12 (link_target call variants)."""
    child = _tok("link_open", "", tag="a", attrs={"href": "http://y.com"})
    text = _tok("text", "label", tag="")
    tok = _tok("inline", "[label](http://y.com)", children=[child, text])
    visitor = LinkVisitor()
    assert visitor._link_target(child, tok) == ("http://y.com", "label")


def test_link_target_requires_inline_type():
    """Kills LinkVisitor::visit__mutmut_1 (and -> or)."""
    state = _state([])
    child = _tok("link_open", "", tag="a", attrs={"href": "http://z.com"})
    text = _tok("text", "label", tag="")
    non_inline = _tok("paragraph_open", "", children=[child, text])
    LinkVisitor().visit([non_inline], state)
    assert state.observations == []


def test_link_append_uses_url_truthiness():
    """Kills LinkVisitor::visit__mutmut_14 (url -> None)."""
    state = _state([])
    visitor = LinkVisitor()
    visitor._append_link(state, "http://u.com", "t")
    assert state.observations[0].content == "t (http://u.com)"
    state2 = _state([])
    visitor._append_link(state2, "", "t")
    assert state2.observations[0].content == "t"


def test_link_append_keeps_link_text():
    """Kills LinkVisitor::visit__mutmut_15 (link_text -> None)."""
    state = _state([])
    LinkVisitor()._append_link(state, "http://u.com", "title")
    assert state.observations[0].content == "title (http://u.com)"
    assert state.observations[0].context["link_text"] == "title"


def test_link_append_arguments_position():
    """Kills LinkVisitor::visit__mutmut_13/16/17/18 (_append_link call variants)."""
    state = _state([])
    LinkVisitor().visit(
        [
            _tok(
                "inline",
                "[t](http://a.com)",
                children=[
                    _tok("link_open", "", tag="a", attrs={"href": "http://a.com"}),
                    _tok("text", "t", tag=""),
                ],
            )
        ],
        state,
    )
    assert len(state.observations) == 1
    assert state.observations[0].content == "t (http://a.com)"


def test_link_target_href_default_empty():
    """Verifies _link_target uses '' default for missing href."""
    child = _tok("link_open", "", tag="a")
    text = _tok("text", "no target", tag="")
    tok = _tok("inline", "[no target]", children=[child, text])
    assert LinkVisitor()._link_target(child, tok) == ("", "no target")
