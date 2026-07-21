from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Observation:
    type: str
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    location: tuple[str, str | None] = ("", None)


@dataclass
class ExtractionState:
    heading_stack: list[str] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    elements: list = field(default_factory=list)


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
    def visit(self, tokens: list, state: ExtractionState) -> None:
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
    def visit(self, tokens: list, state: ExtractionState) -> None:
        list_depth = 0
        current_items: list[str] = []
        for tok in tokens:
            if tok.type in ("bullet_list_open", "ordered_list_open"):
                list_depth += 1
            elif tok.type in ("bullet_list_close", "ordered_list_close"):
                list_depth -= 1
                if list_depth == 0 and current_items:
                    doc_id = ""
                    ob = Observation(
                        type="list",
                        content="\n".join(current_items),
                        context={
                            "item_count": len(current_items),
                            "heading_path": "/".join(state.heading_stack),
                        },
                        location=(
                            doc_id,
                            "/".join(state.heading_stack)
                            if state.heading_stack
                            else None,
                        ),
                    )
                    state.observations.append(ob)
                    current_items = []
            elif tok.type == "list_item_open":
                pass
            elif tok.type == "inline" and list_depth > 0:
                current_items.append(tok.content.strip())


class TableVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        headers: list[str] = []
        rows: list[list[str]] = []
        in_header = False
        in_body = False
        current_row: list[str] = []

        for tok in tokens:
            if tok.type == "thead_open":
                in_header = True
            elif tok.type == "thead_close":
                in_header = False
            elif tok.type == "tbody_open":
                in_body = True
            elif tok.type == "tbody_close":
                in_body = False
            elif tok.type == "tr_open":
                current_row = []
            elif tok.type == "tr_close":
                if current_row:
                    if in_header:
                        headers = list(current_row)
                    else:
                        rows.append(list(current_row))
                current_row = []
            elif tok.type == "inline" and (in_header or in_body):
                current_row.append(tok.content.strip())

        if headers or rows:
            doc_id = ""
            ob = Observation(
                type="table",
                content=str({"headers": headers, "rows": rows}),
                context={
                    "column_count": len(headers),
                    "row_count": len(rows),
                    "heading_path": "/".join(state.heading_stack),
                },
                location=(
                    doc_id,
                    "/".join(state.heading_stack) if state.heading_stack else None,
                ),
            )
            state.observations.append(ob)


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


class ParagraphVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        depth = 0
        for tok in tokens:
            if tok.type in _CONTAINER_OPEN:
                depth += 1
            elif tok.type in _CONTAINER_CLOSE:
                depth = max(0, depth - 1)
            elif tok.type == "inline" and depth == 0:
                text = tok.content.strip()
                if text:
                    doc_id = ""
                    ob = Observation(
                        type="paragraph",
                        content=text,
                        context={
                            "heading_path": "/".join(state.heading_stack),
                        },
                        location=(
                            doc_id,
                            "/".join(state.heading_stack)
                            if state.heading_stack
                            else None,
                        ),
                    )
                    state.observations.append(ob)


class CodeBlockVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        for tok in tokens:
            if tok.type == "fence":
                language = (tok.info or "").strip()
                doc_id = ""
                ob = Observation(
                    type="code_block",
                    content=tok.content,
                    context={
                        "language": language,
                        "heading_path": "/".join(state.heading_stack),
                    },
                    location=(
                        doc_id,
                        "/".join(state.heading_stack) if state.heading_stack else None,
                    ),
                )
                state.observations.append(ob)


class QuoteVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        in_quote = False
        parts: list[str] = []
        for tok in tokens:
            if tok.type == "blockquote_open":
                in_quote = True
                parts = []
            elif tok.type == "blockquote_close":
                in_quote = False
                if parts:
                    doc_id = ""
                    ob = Observation(
                        type="blockquote",
                        content="\n".join(parts),
                        context={
                            "heading_path": "/".join(state.heading_stack),
                        },
                        location=(
                            doc_id,
                            "/".join(state.heading_stack)
                            if state.heading_stack
                            else None,
                        ),
                    )
                    state.observations.append(ob)
                    parts = []
            elif tok.type == "inline" and in_quote:
                parts.append(tok.content.strip())


class EmphasisVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        for tok in tokens:
            if tok.type == "inline" and tok.children:
                for child in tok.children:
                    if child.type in ("strong", "em"):
                        text = (
                            child.content.strip() if hasattr(child, "content") else ""
                        )
                        if text:
                            doc_id = ""
                            ob = Observation(
                                type="emphasis",
                                content=text,
                                context={
                                    "emphasis_type": child.tag,
                                    "heading_path": "/".join(state.heading_stack),
                                },
                                location=(
                                    doc_id,
                                    "/".join(state.heading_stack)
                                    if state.heading_stack
                                    else None,
                                ),
                            )
                            state.observations.append(ob)


class LinkVisitor:
    def visit(self, tokens: list, state: ExtractionState) -> None:
        for tok in tokens:
            if tok.type == "inline" and tok.children:
                for child in tok.children:
                    if child.type == "link_open":
                        url = (
                            child.attrs.get("href", "")
                            if hasattr(child, "attrs")
                            else ""
                        )
                        link_text = ""
                        for j, c in enumerate(tok.children):
                            if c.type == "link_open" and id(c) == id(child):
                                if j + 1 < len(tok.children):
                                    sibling = tok.children[j + 1]
                                    if hasattr(sibling, "content"):
                                        link_text = sibling.content
                                break
                        doc_id = ""
                        ob = Observation(
                            type="link",
                            content=f"{link_text} ({url})" if url else link_text,
                            context={
                                "url": url,
                                "link_text": link_text,
                                "heading_path": "/".join(state.heading_stack),
                            },
                            location=(
                                doc_id,
                                "/".join(state.heading_stack)
                                if state.heading_stack
                                else None,
                            ),
                        )
                        state.observations.append(ob)
