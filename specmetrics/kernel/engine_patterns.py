from __future__ import annotations

import hashlib

import structlog

from .engine_rule import ExtractionRule
from .engine_visitors import Observation
from .semantic_extraction_engine import (
    EvidenceReference,
    ExtractedElement,
)

logger = structlog.get_logger(__name__)


def _content_hash(document_id: str, section_id: str | None, text: str) -> str:
    raw = f"{document_id}::{section_id or ''}::{text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class PatternLibrary:
    def __init__(self, rule_packs: list[list[ExtractionRule]]) -> None:
        merged: dict[str, ExtractionRule] = {}
        for pack in rule_packs:
            for rule in pack:
                existing = merged.get(rule.id)
                if existing is None or rule.priority > existing.priority:
                    merged[rule.id] = rule
                elif rule.priority == existing.priority and rule.id < existing.id:
                    merged[rule.id] = rule

        self._rules = sorted(merged.values(), key=lambda r: (-r.priority, r.id))
        logger.info("pattern_library_initialized", total_rules=len(self._rules))

    @property
    def rules(self) -> list[ExtractionRule]:
        return list(self._rules)

    def match(self, observations: list[Observation]) -> list[ExtractedElement]:
        elements: list[ExtractedElement] = []
        for obs in observations:
            section_type = obs.context.get("section_type", "")
            content = obs.content
            doc_id = obs.location[0] if obs.location else ""
            section_id = obs.location[1] if obs.location else None

            candidates: list[str] = [section_type, content]
            if section_type != content:
                candidates.append(content)

            matched_rule: ExtractionRule | None = None
            for rule in self._rules:
                pat = rule.pattern

                heading_match = pat.get("heading", "")
                if heading_match:
                    match_values = [heading_match] if isinstance(heading_match, str) else heading_match
                    for h_candidate in candidates:
                        for m in match_values:
                            if isinstance(m, str) and m.lower() == h_candidate.lower():
                                matched_rule = rule
                                break
                        if matched_rule:
                            break
                    if matched_rule:
                        break
                    continue

                keywords = pat.get("keywords", [])
                if keywords:
                    min_matches = pat.get("min_matches", len(keywords))
                    matched = sum(1 for kw in keywords if kw.lower() in content.lower())
                    if matched >= min_matches:
                        matched_rule = rule
                        break
                    continue

                structure = pat.get("structure")
                if structure:
                    matched_rule = rule
                    break

            if matched_rule is not None:
                elem_id = _content_hash(doc_id, section_id, content)
                evidence = EvidenceReference(
                    document_id=doc_id,
                    section_id=section_id,
                    text=content,
                )
                element = ExtractedElement(
                    id=elem_id,
                    type=matched_rule.type,
                    content=content,
                    confidence=matched_rule.confidence,
                    evidence=evidence,
                )
                elements.append(element)

        return elements
