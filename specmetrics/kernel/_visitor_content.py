"""Content visitors that record paragraphs, code blocks, quotes, and links."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from ._visitor_state import ExtractionState, Observation

if TYPE_CHECKING:
    from markdown_it.token import Token

_CONTAINER_OPEN = {
    "heading_open",
    "bullet_list_open",
    "ordered_list_open",
    "list_item_open",
    "blockquote_open",
    "table_open",
}
_CONTAINER_CLOSE = {
    "heading_close",
    "bullet_list_close",
    "ordered_list_close",
    "list_item_close",
    "blockquote_close",
    "table_close",
}


def _heading_path(state: ExtractionState) -> str:
    return "/".join(state.heading_stack)


def _section_location(state: ExtractionState) -> str | None:
    return _heading_path(state) if state.heading_stack else None


class ParagraphVisitor:
    """Visitor that records paragraph observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record paragraph observations from the token stream."""
        depth = 0
        for tok in tokens:
            if tok.type in _CONTAINER_OPEN:
                depth += 1
            elif tok.type in _CONTAINER_CLOSE:
                depth = max(0, depth - 1)
            elif tok.type == "inline" and depth == 0:
                text = tok.content.strip()
                if text:
                    ob = Observation(
                        type="paragraph",
                        content=text,
                        context={"heading_path": _heading_path(state)},
                        location=("", _section_location(state)),
                    )
                    state.observations.append(ob)


class CodeBlockVisitor:
    """Visitor that records code block observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record code block observations from the token stream."""
        for tok in tokens:
            if tok.type == "fence":
                language = (tok.info or "").strip()
                ob = Observation(
                    type="code_block",
                    content=tok.content,
                    context={
                        "language": language,
                        "heading_path": _heading_path(state),
                    },
                    location=("", _section_location(state)),
                )
                state.observations.append(ob)


class QuoteVisitor:
    """Visitor that records blockquote observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record blockquote observations from the token stream."""
        in_quote = False
        parts: list[str] = []
        for tok in tokens:
            if tok.type == "blockquote_open":
                in_quote = True
                parts = []
            elif tok.type == "blockquote_close":
                in_quote = False
                if parts:
                    ob = Observation(
                        type="blockquote",
                        content="\n".join(parts),
                        context={"heading_path": _heading_path(state)},
                        location=("", _section_location(state)),
                    )
                    state.observations.append(ob)
                    parts = []
            elif tok.type == "inline" and in_quote:
                parts.append(tok.content.strip())


class EmphasisVisitor:
    """Visitor that records emphasis observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record emphasis observations from the token stream."""
        for tok in tokens:
            if tok.type == "inline" and tok.children:
                for child in tok.children:
                    if child.type in ("strong", "em"):
                        text = (
                            child.content.strip()
                            if hasattr(child, "content")
                            else ""
                        )
                        if text:
                            ob = Observation(
                                type="emphasis",
                                content=text,
                                context={
                                    "emphasis_type": child.tag,
                                    "heading_path": _heading_path(state),
                                },
                                location=("", _section_location(state)),
                            )
                            state.observations.append(ob)


class LinkVisitor:
    """Visitor that records link observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record link observations from the token stream."""
        for tok in tokens:
            if tok.type == "inline" and tok.children:
                for child in tok.children:
                    if child.type == "link_open":
                        url, link_text = self._link_target(child, tok)
                        self._append_link(state, url, link_text)

    def _link_target(self: Self, child: Token, tok: Token) -> tuple[str, str]:
        """Return the URL and link text for the given link token."""
        url = child.attrs.get("href", "") if hasattr(child, "attrs") else ""
        link_text = ""
        for j, c in enumerate(tok.children):
            if c.type == "link_open" and id(c) == id(child):
                if j + 1 < len(tok.children):
                    sibling = tok.children[j + 1]
                    if hasattr(sibling, "content"):
                        link_text = sibling.content
                break
        return url, link_text

    def _append_link(
        self: Self, state: ExtractionState, url: str, link_text: str
    ) -> None:
        ob = Observation(
            type="link",
            content=f"{link_text} ({url})" if url else link_text,
            context={
                "url": url,
                "link_text": link_text,
                "heading_path": _heading_path(state),
            },
            location=("", _section_location(state)),
        )
        state.observations.append(ob)