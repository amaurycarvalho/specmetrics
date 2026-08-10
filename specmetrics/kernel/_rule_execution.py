"""Rule execution and visitor running for the deterministic extraction engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import structlog

from ._matching import _is_likely_binary
from .adapter_interface import Document
from .engine_rule import ExtractionRule
from .engine_visitors import (
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
from .semantic_extraction_engine import ExtractedElement

logger = structlog.get_logger(__name__)

try:
    from markdown_it import MarkdownIt

    _md = MarkdownIt()
except ImportError:
    _md = None

if TYPE_CHECKING:
    from markdown_it.token import Token

_VISITORS = [
    HeadingVisitor(),
    ListVisitor(),
    TableVisitor(),
    ParagraphVisitor(),
    CodeBlockVisitor(),
    QuoteVisitor(),
    EmphasisVisitor(),
    LinkVisitor(),
]


class ExecutionMixin:
    """Provide rule execution over documents for the engine."""

    def _execute_rules(
        self: Self, doc: Document, rules: list[ExtractionRule]
    ) -> tuple[list[ExtractedElement], int, int, int, set[str]]:
        if _md is None:
            logger.error("markdown_it_not_available")
            return [], 0, 0, len(rules), set()

        if _is_likely_binary(doc.content):
            logger.warning("skipping_binary_content", doc_id=doc.id)
            return [], 0, 0, len(rules), set()

        tokens = _md.parse(doc.content)
        state = ExtractionState()

        self._run_visitors(tokens, state)

        for obs in state.observations:
            obs.location = (doc.id, obs.location[1])

        elements: list[ExtractedElement] = []
        rules_attempted = 0
        rules_succeeded = 0
        rules_failed = 0
        failed_rule_ids: set[str] = set()
        doc_type = (doc.document_type or "").lower()

        for obs in state.observations:
            section_type = obs.context.get("section_type", "")
            content = obs.content
            section_id = obs.location[1]

            for rule in rules:
                if not self._rule_applies(rule, doc_type, section_type):
                    continue

                rules_attempted += 1
                status = self._attempt_rule(
                    rule, doc, section_type, content, section_id, elements
                )
                if status == "matched":
                    rules_succeeded += 1
                elif status == "failed":
                    rules_failed += 1
                    failed_rule_ids.add(rule.id)

        return elements, rules_attempted, rules_succeeded, rules_failed, failed_rule_ids

    def _run_visitors(
        self: Self, tokens: list[Token], state: ExtractionState
    ) -> None:
        for visitor in _VISITORS:
            try:
                visitor.visit(tokens, state)
            except Exception as exc:
                logger.warning(
                    "visitor_failed", visitor=type(visitor).__name__, error=str(exc)
                )