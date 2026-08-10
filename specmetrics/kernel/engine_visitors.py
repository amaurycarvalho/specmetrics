"""Visitor classes that extract observations from markdown token streams.

These visitors walk the markdown-it token stream produced by the semantic
extraction engine and record structured observations for headings, lists,
tables, paragraphs, code blocks, quotes, emphasis, and links.
"""

from __future__ import annotations

from typing import Self

from ._visitor_content import (
    CodeBlockVisitor,
    EmphasisVisitor,
    LinkVisitor,
    ParagraphVisitor,
    QuoteVisitor,
)
from ._visitor_state import ExtractionState, Observation
from ._visitor_tables import TableVisitor

__all__ = [
    "CodeBlockVisitor",
    "EmphasisVisitor",
    "ExtractionState",
    "HeadingVisitor",
    "LinkVisitor",
    "ListVisitor",
    "Observation",
    "ParagraphVisitor",
    "QuoteVisitor",
    "TableVisitor",
]

_KNOWN_SECTIONS = {
    "actors": "Actors",
    "business rules": "Business Rules",
    "constraints": "Constraints",
    "assumptions": "Assumptions",
    "decisions": "Decisions",
    "glossary": "Glossary Terms",
    "user story": "User Story",
    "acceptance criteria": "Acceptance Criteria",
}


class HeadingVisitor:
    """Visitor that records heading observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record heading observations from the token stream."""
        for i, tok in enumerate(tokens):
            if tok.type == "heading_open":
                level = int(tok.tag[1]) if len(tok.tag) == 2 else 1
                level = min(level, 6)

                while len(state.heading_stack) >= level:
                    state.heading_stack.pop()
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text = tokens[i + 1].content.strip()
                    state.heading_stack.append(text)

                    heading_lower = text.lower()
                    section_type = _KNOWN_SECTIONS.get(heading_lower)
                    doc_id = ""
                    ob = Observation(
                        type="heading",
                        content=text,
                        context={
                            "level": level,
                            "section_type": section_type or "unknown",
                            "heading_path": "/".join(state.heading_stack),
                        },
                        location=(doc_id, "/".join(state.heading_stack)),
                    )
                    state.observations.append(ob)


class ListVisitor:
    """Visitor that records list observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record list observations from the token stream."""
        list_depth = 0
        current_items: list[str] = []
        for tok in tokens:
            if tok.type in ("bullet_list_open", "ordered_list_open"):
                list_depth += 1
            elif tok.type in ("bullet_list_close", "ordered_list_close"):
                list_depth -= 1
                if list_depth == 0 and current_items:
                    self._append_list(state, current_items)
                    current_items = []
            elif tok.type == "inline" and list_depth > 0:
                current_items.append(tok.content.strip())

    def _append_list(self: Self, state: ExtractionState, items: list[str]) -> None:
        doc_id = ""
        location = (
            "/".join(state.heading_stack) if state.heading_stack else None
        )
        ob = Observation(
            type="list",
            content="\n".join(items),
            context={
                "item_count": len(items),
                "heading_path": "/".join(state.heading_stack),
            },
            location=(doc_id, location),
        )
        state.observations.append(ob)
