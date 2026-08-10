"""Table visitor and its token-dispatch helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from ._visitor_state import ExtractionState, Observation

if TYPE_CHECKING:
    from markdown_it.token import Token


class TableVisitor:
    """Visitor that records table observations."""

    def visit(self: Self, tokens: list, state: ExtractionState) -> None:
        """Record table observations from the token stream."""
        ctx: dict[str, Any] = {
            "headers": [],
            "rows": [],
            "in_header": False,
            "in_body": False,
            "current_row": [],
        }
        for tok in tokens:
            handler = _TABLE_DISPATCH.get(tok.type)
            if handler is not None:
                handler(ctx, tok)

        if ctx["headers"] or ctx["rows"]:
            self._append_table(state, ctx)

    def _append_table(self: Self, state: ExtractionState, ctx: dict[str, Any]) -> None:
        headers = ctx["headers"]
        rows = ctx["rows"]
        location = "/".join(state.heading_stack) if state.heading_stack else None
        ob = Observation(
            type="table",
            content=str({"headers": headers, "rows": rows}),
            context={
                "column_count": len(headers),
                "row_count": len(rows),
                "heading_path": "/".join(state.heading_stack),
            },
            location=("", location),
        )
        state.observations.append(ob)


def _table_thead_open(ctx: dict[str, Any], _tok: Token) -> None:
    ctx["in_header"] = True


def _table_thead_close(ctx: dict[str, Any], _tok: Token) -> None:
    ctx["in_header"] = False


def _table_tbody_open(ctx: dict[str, Any], _tok: Token) -> None:
    ctx["in_body"] = True


def _table_tbody_close(ctx: dict[str, Any], _tok: Token) -> None:
    ctx["in_body"] = False


def _table_tr_open(ctx: dict[str, Any], _tok: Token) -> None:
    ctx["current_row"] = []


def _table_tr_close(ctx: dict[str, Any], _tok: Token) -> None:
    if ctx["current_row"]:
        if ctx["in_header"]:
            ctx["headers"] = list(ctx["current_row"])
        else:
            ctx["rows"].append(list(ctx["current_row"]))
    ctx["current_row"] = []


def _table_inline(ctx: dict[str, Any], tok: Token) -> None:
    if ctx["in_header"] or ctx["in_body"]:
        ctx["current_row"].append(tok.content.strip())


_TABLE_DISPATCH: dict[str, Any] = {
    "thead_open": _table_thead_open,
    "thead_close": _table_thead_close,
    "tbody_open": _table_tbody_open,
    "tbody_close": _table_tbody_close,
    "tr_open": _table_tr_open,
    "tr_close": _table_tr_close,
    "inline": _table_inline,
}