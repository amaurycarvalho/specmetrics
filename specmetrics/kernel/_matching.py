"""Rule matching and element building for the deterministic extraction engine."""

from __future__ import annotations

import hashlib
import re
from typing import Self

import structlog

from .adapter_interface import Document
from .engine_rule import ExtractionRule
from .semantic_extraction_engine import (
    EvidenceReference,
    ExtractedElement,
)

logger = structlog.get_logger(__name__)

_NON_TEXT_THRESHOLD = 0.3


def _is_likely_binary(content: str) -> bool:
    if not content:
        return False
    control = sum(1 for c in content if ord(c) < 32 and c not in "\n\r\t\f\v")
    return control / len(content) > _NON_TEXT_THRESHOLD


def _content_hash(document_id: str, section_id: str | None, text: str) -> str:
    raw = f"{document_id}::{section_id or ''}::{text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class MatchingMixin:
    """Provide rule matching and attempt logic for the engine."""

    def _match_rule_against_observation(
        self: Self, rule: ExtractionRule, section_type: str, heading_text: str, content: str
    ) -> bool:
        pat = rule.pattern
        if pat.get("regex"):
            return self._match_regex_pattern(pat, content, heading_text, rule.id)
        if pat.get("heading"):
            return self._match_heading_pattern(pat, section_type, heading_text)
        if pat.get("keywords"):
            return self._match_keyword_pattern(pat, content)
        return bool(pat.get("structure"))

    def _match_regex_pattern(
        self: Self, pat: dict, content: str, heading_text: str, rule_id: str
    ) -> bool:
        regex = pat.get("regex", "")
        try:
            if re.search(regex, content) or re.search(regex, heading_text):
                return True
        except re.error:
            logger.warning("regex_error", rule_id=rule_id, pattern=regex)
        return False

    def _match_heading_pattern(
        self: Self, pat: dict, section_type: str, heading_text: str
    ) -> bool:
        heading_match = pat.get("heading", "")
        candidates = [section_type, heading_text]
        if section_type != heading_text:
            candidates.append(heading_text)
        match_values = (
            [heading_match] if isinstance(heading_match, str) else heading_match
        )
        for h_candidate in candidates:
            for m in match_values:
                if isinstance(m, str) and m.lower() == h_candidate.lower():
                    return True
        return False

    def _match_keyword_pattern(self: Self, pat: dict, content: str) -> bool:
        keywords = pat.get("keywords", [])
        min_matches = pat.get("min_matches", len(keywords))
        matched = sum(1 for kw in keywords if kw.lower() in content.lower())
        return matched >= min_matches

    def _rule_applies(
        self: Self, rule: ExtractionRule, doc_type: str, section_type: str
    ) -> bool:
        if rule.document_type and rule.document_type != doc_type:
            return False
        if rule.target_sections:
            st_lower = section_type.lower()
            if not any(ts.lower() == st_lower for ts in rule.target_sections):
                return False
        return True

    def _attempt_rule(
        self: Self,
        rule: ExtractionRule,
        doc: Document,
        section_type: str,
        content: str,
        section_id: str | None,
        elements: list[ExtractedElement],
    ) -> str:
        """Try applying a single rule, returning matched/failed/skipped."""
        try:
            if self._match_rule_against_observation(
                rule, section_type, section_type, content
            ):
                elements.append(
                    self._build_element(rule, doc, content, section_id)
                )
                return "matched"
        except Exception as exc:
            logger.warning(
                "rule_execution_failed",
                rule_id=rule.id,
                doc_id=doc.id,
                error=str(exc),
            )
            return "failed"
        return "skipped"

    def _build_element(
        self: Self,
        rule: ExtractionRule,
        doc: Document,
        content: str,
        section_id: str | None,
    ) -> ExtractedElement:
        elem_id = _content_hash(doc.id, section_id, content)
        evidence = EvidenceReference(
            document_id=doc.id,
            section_id=section_id,
            text=content,
            rule_id=rule.id,
        )
        return ExtractedElement(
            id=elem_id,
            type=rule.type,
            content=content,
            confidence=rule.confidence,
            evidence=evidence,
        )