"""Tests for specmetrics.kernel.engine_visitors."""

from __future__ import annotations

from markdown_it.token import Token

from specmetrics.kernel._visitor_state import ExtractionState, Observation
from specmetrics.kernel.engine_visitors import HeadingVisitor, ListVisitor


def _tok(type_: str, content: str = "", tag: str = "") -> Token:
    t = Token(type_, tag, 0)
    t.content = content
    return t


def _state(heading_stack: list[str] | None = None) -> ExtractionState:
    st = ExtractionState()
    if heading_stack is not None:
        st.heading_stack = list(heading_stack)
    return st


def _head(*tokens) -> ExtractionState:
    st = _state()
    HeadingVisitor().visit(list(tokens), st)
    return st


def _head_with_stack(tokens, stack) -> ExtractionState:
    st = _state(stack)
    HeadingVisitor().visit(list(tokens), st)
    return st


def test_heading_records_basic_observation():
    """Kills HeadingVisitor::visit__mutmut_1 (enumerate(None)) and
    __mutmut_2/3/4 (heading_open check)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "Title"))
    assert len(st.observations) == 1
    ob = st.observations[0]
    assert isinstance(ob, Observation)
    assert ob.type == "heading"
    assert ob.content == "Title"


def test_heading_level_from_tag():
    """Kills HeadingVisitor::visit__mutmut_5/6/7 (level from tag) and
    __mutmut_8/9 (level condition)."""
    st = _head(_tok("heading_open", "", "h2"), _tok("inline", "x"))
    assert st.observations[0].context["level"] == 2


def test_heading_level_default_for_non_standard_tag():
    """Kills HeadingVisitor::visit__mutmut_10 (else default 1 -> 2)."""
    st = _head(_tok("heading_open", "", "heading"), _tok("inline", "x"))
    assert st.observations[0].context["level"] == 1


def test_heading_level_capped_at_six():
    """Kills HeadingVisitor::visit__mutmut_16 (min(level, 6) -> 7)."""
    st = _head(_tok("heading_open", "", "h7"), _tok("inline", "x"))
    assert st.observations[0].context["level"] == 6


def test_heading_level_min_call():
    """Kills HeadingVisitor::visit__mutmut_11/12/13/14/15 (min() call variants)."""
    st = _head(_tok("heading_open", "", "h3"), _tok("inline", "x"))
    assert st.observations[0].context["level"] == 3


def test_heading_stack_pop_uses_level():
    """Kills HeadingVisitor::visit__mutmut_17 (>= -> > on stack pop)."""
    st = _head_with_stack(
        [_tok("heading_open", "", "h2"), _tok("inline", "new")], ["a", "b"]
    )
    assert st.observations[0].context["heading_path"] == "a/new"


def test_heading_without_following_inline():
    """Kills HeadingVisitor::visit__mutmut_18/19/21 (bounds on next token)."""
    st = _head(_tok("heading_open", "", "h1"))
    assert st.observations == []


def test_heading_followed_by_inline_last_two_tokens():
    """Kills HeadingVisitor::visit__mutmut_20 (i + 1 -> i + 2) and
    __mutmut_23 (tokens[i + 2].type)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "Title"))
    assert len(st.observations) == 1
    assert st.observations[0].content == "Title"


def test_heading_next_token_must_be_inline():
    """Kills HeadingVisitor::visit__mutmut_22 (tokens[i - 1].type),
    __mutmut_24/25/26 (inline type check)."""
    st = _head(
        _tok("heading_open", "", "h1"),
        _tok("inline", "Title"),
        _tok("paragraph_close"),
    )
    assert len(st.observations) == 1
    assert st.observations[0].content == "Title"


def test_heading_text_from_next_inline_token():
    """Kills HeadingVisitor::visit__mutmut_28/29 (tokens[i +/- 1/2].content)."""
    st = _head(
        _tok("heading_open", "", "h1"),
        _tok("inline", "real title"),
        _tok("paragraph_close", "junk"),
    )
    assert st.observations[0].content == "real title"


def test_heading_known_section_type():
    """Kills HeadingVisitor::visit__mutmut_31/32/33/34 (section_type lookup)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "Actors"))
    assert st.observations[0].context["section_type"] == "Actors"


def test_heading_unknown_section_type():
    """Verifies unknown headings get 'unknown' section_type."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "Random"))
    assert st.observations[0].context["section_type"] == "unknown"


def test_heading_location_doc_id_empty():
    """Kills HeadingVisitor::visit__mutmut_35/36 (doc_id '' -> None/'XXXX') and
    __mutmut_45 (location dropped)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "x"))
    assert st.observations[0].location == ("", "x")


def test_heading_observation_type():
    """Kills HeadingVisitor::visit__mutmut_38/42/46/47 (type 'heading')."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "x"))
    assert st.observations[0].type == "heading"


def test_heading_content_field():
    """Kills HeadingVisitor::visit__mutmut_39/43 (content=text)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "   spaced   "))
    assert st.observations[0].content == "spaced"


def test_heading_context_field():
    """Kills HeadingVisitor::visit__mutmut_44 (context dropped) and
    __mutmut_55/56 (heading_path key)."""
    st = _head(_tok("heading_open", "", "h1"), _tok("inline", "x"))
    assert st.observations[0].context == {
        "level": 1,
        "section_type": "unknown",
        "heading_path": "x",
    }


def test_heading_path_joined_with_slash():
    """Kills HeadingVisitor::visit__mutmut_57/58 (heading_path join) and
    __mutmut_59/60 (location join)."""
    st = _head_with_stack(
        [
            _tok("heading_open", "", "h1"),
            _tok("inline", "a"),
            _tok("heading_open", "", "h2"),
            _tok("inline", "b"),
        ],
        [],
    )
    assert st.observations[1].context["heading_path"] == "a/b"
    assert st.observations[1].location == ("", "a/b")


def test_list_records_single_item():
    """Kills ListVisitor::visit__mutmut_1 (list_depth=None), __mutmut_3
    (current_items=None), __mutmut_4/5/6/7/8 (open check) and
    __mutmut_23/24/25/26 (_append_list call variants)."""
    st = _state()
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert len(st.observations) == 1
    ob = st.observations[0]
    assert isinstance(ob, Observation)
    assert ob.type == "list"
    assert ob.content == "a"
    assert ob.context == {"item_count": 1, "heading_path": ""}
    assert ob.location == ("", None)


def test_list_joins_items():
    """Kills ListVisitor::visit__mutmut_34 (append(None))."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("bullet_list_open"),
            _tok("inline", "a"),
            _tok("inline", "b"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert st.observations[0].content == "a\nb"
    assert st.observations[0].context["item_count"] == 2


def test_list_nested_items_accumulate():
    """Kills ListVisitor::visit__mutmut_9 (depth += 1 -> = 1)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("bullet_list_open"),
            _tok("bullet_list_open"),
            _tok("inline", "inner"),
            _tok("bullet_list_close"),
            _tok("inline", "outer"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert st.observations[0].content == "inner\nouter"


def test_list_two_opens_two_closes():
    """Kills ListVisitor::visit__mutmut_11 (depth += 1 -> += 2)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("bullet_list_open"),
            _tok("bullet_list_open"),
            _tok("inline", "a"),
            _tok("bullet_list_close"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert len(st.observations) == 1
    assert st.observations[0].content == "a"


def test_list_balanced_close():
    """Kills ListVisitor::visit__mutmut_10 (depth += 1 -> -= 1),
    __mutmut_17 (depth -= 1 -> = 1), __mutmut_18 (depth -= 1 -> += 1) and
    __mutmut_19 (depth -= 1 -> -= 2)."""
    st = _state()
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert len(st.observations) == 1
    assert st.observations[0].content == "a"


def test_list_close_requires_zero_depth():
    """Kills ListVisitor::visit__mutmut_20 (and -> or on flush condition)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("bullet_list_open"),
            _tok("bullet_list_open"),
            _tok("inline", "inner"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert st.observations == []


def test_list_flush_condition_equality():
    """Kills ListVisitor::visit__mutmut_21 (== 0 -> != 0) and
    __mutmut_22 (== 0 -> == 1)."""
    st = _state()
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert len(st.observations) == 1


def test_list_initial_depth_zero():
    """Kills ListVisitor::visit__mutmut_2 (initial list_depth 0 -> 1)."""
    st = _state()
    ListVisitor().visit([_tok("inline", "stray"), _tok("bullet_list_close")], st)
    assert st.observations == []


def test_list_close_token_types():
    """Kills ListVisitor::visit__mutmut_12/13/14/15/16 (close check)."""
    st = _state()
    ListVisitor().visit(
        [_tok("ordered_list_open"), _tok("inline", "a"), _tok("ordered_list_close")], st
    )
    assert len(st.observations) == 1
    assert st.observations[0].content == "a"


def test_list_inline_requires_depth():
    """Kills ListVisitor::visit__mutmut_28 (and -> or on inline append)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("inline", "stray"),
            _tok("bullet_list_open"),
            _tok("inline", "real"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert st.observations[0].content == "real"


def test_list_inline_type_check():
    """Kills ListVisitor::visit__mutmut_29/30/31 (inline type variants)."""
    st = _state()
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert len(st.observations) == 1
    assert st.observations[0].content == "a"


def test_list_inline_depth_strictly_positive():
    """Kills ListVisitor::visit__mutmut_32 (> 0 -> >= 0)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("inline", "stray"),
            _tok("bullet_list_open"),
            _tok("inline", "real"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert st.observations[0].content == "real"


def test_list_inline_single_depth():
    """Kills ListVisitor::visit__mutmut_33 (> 0 -> > 1)."""
    st = _state()
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert len(st.observations) == 1


def test_list_multiple_blocks_reset_items():
    """Kills ListVisitor::visit__mutmut_27 (current_items = None after flush)."""
    st = _state()
    ListVisitor().visit(
        [
            _tok("bullet_list_open"),
            _tok("inline", "a"),
            _tok("bullet_list_close"),
            _tok("bullet_list_open"),
            _tok("inline", "b"),
            _tok("bullet_list_close"),
        ],
        st,
    )
    assert [o.content for o in st.observations] == ["a", "b"]


def test_list_location_with_heading_path():
    """Verifies list location uses heading path when present."""
    st = _state(["docs", "section"])
    ListVisitor().visit(
        [_tok("bullet_list_open"), _tok("inline", "a"), _tok("bullet_list_close")], st
    )
    assert st.observations[0].location == ("", "docs/section")
    assert st.observations[0].context["heading_path"] == "docs/section"
