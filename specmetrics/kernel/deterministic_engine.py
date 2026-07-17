from __future__ import annotations

import hashlib
import time
from pathlib import Path

import structlog

from .adapter_interface import Document
from .engine_patterns import PatternLibrary
from .engine_rule import ExtractionRule, RulePackLoader
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
from .semantic_extraction_engine import (
    EvidenceReference,
    ExtractedElement,
    ExtractionResult,
    ProcessingStats,
    SemanticExtractionEngine,
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


try:
    from markdown_it import MarkdownIt

    _md = MarkdownIt()
except ImportError:
    _md = None


class DeterministicSemanticEngine(SemanticExtractionEngine):
    def __init__(
        self,
        max_heading_depth: int = 6,
        default_rule_pack: str | None = None,
        extra_rule_packs: list[str] | None = None,
        default_confidence: float = 0.70,
    ) -> None:
        self._max_heading_depth = max_heading_depth
        self._default_rule_pack = default_rule_pack
        self._extra_rule_packs = extra_rule_packs or []
        self._default_confidence = default_confidence
        self._pattern_library: PatternLibrary | None = None

    def _load_rules(self) -> list[ExtractionRule]:
        packs: list[list[ExtractionRule]] = []

        default_path = self._default_rule_pack
        if default_path is None:
            default_path = str(
                Path(__file__).parent / "rules" / "default_rule_pack.yaml"
            )
        try:
            packs.append(RulePackLoader.load(default_path))
        except (FileNotFoundError, RuntimeError) as exc:
            logger.warning("default_rule_pack_not_loaded", error=str(exc))

        for extra in self._extra_rule_packs:
            try:
                packs.append(RulePackLoader.load(extra))
            except (FileNotFoundError, RuntimeError) as exc:
                logger.warning("extra_rule_pack_not_loaded", path=extra, error=str(exc))

        merged: dict[str, ExtractionRule] = {}
        conflict_count = 0
        for pack in packs:
            for rule in pack:
                existing = merged.get(rule.id)
                if existing is None:
                    merged[rule.id] = rule
                else:
                    conflict_count += 1
                    if rule.priority > existing.priority:
                        logger.info(
                            "rule_conflict_resolved",
                            rule_id=rule.id,
                            winner=rule.name,
                            winner_priority=rule.priority,
                            loser_priority=existing.priority,
                        )
                        merged[rule.id] = rule
                    elif rule.priority == existing.priority and rule.id < existing.id:
                        merged[rule.id] = rule

        result = sorted(merged.values(), key=lambda r: (-r.priority, r.id))
        logger.info(
            "rules_loaded",
            total_rules=len(result),
            conflicts_detected=conflict_count,
        )
        return result

    def _process_document(
        self, doc: Document, rules: list[ExtractionRule]
    ) -> tuple[list[ExtractedElement], int]:
        if _md is None:
            logger.error("markdown_it_not_available")
            return [], 1

        if _is_likely_binary(doc.content):
            logger.warning("skipping_binary_content", doc_id=doc.id)
            return [], 1

        tokens = _md.parse(doc.content)

        state = ExtractionState()

        visitors = [
            HeadingVisitor(),
            ListVisitor(),
            TableVisitor(),
            ParagraphVisitor(),
            CodeBlockVisitor(),
            QuoteVisitor(),
            EmphasisVisitor(),
            LinkVisitor(),
        ]

        for visitor in visitors:
            try:
                visitor.visit(tokens, state)
            except Exception as exc:
                logger.warning("visitor_failed", visitor=type(visitor).__name__, error=str(exc))

        for obs in state.observations:
            obs.location = (doc.id, obs.location[1])

        elements: list[ExtractedElement] = []
        for obs in state.observations:
            heading_text = obs.context.get("section_type", "")
            content = obs.content
            doc_id = doc.id
            section_id = obs.location[1]

            matched_rule = None
            for rule in rules:
                pat = rule.pattern

                heading_match = pat.get("heading", "")
                if heading_match:
                    if isinstance(heading_match, str) and heading_match.lower() == heading_text.lower():
                        matched_rule = rule
                        break
                    if isinstance(heading_match, list):
                        for h in heading_match:
                            if isinstance(h, str) and h.lower() == heading_text.lower():
                                matched_rule = rule
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

        return elements, 0

    def extract(self, documents: list[Document]) -> ExtractionResult:
        if not documents:
            return ExtractionResult(
                elements=[],
                engine_id="deterministic",
                processing_stats=ProcessingStats(
                    documents_processed=0,
                    elements_extracted=0,
                    elements_by_type={},
                    duration_ms=0,
                    errors_count=0,
                ),
            )

        start = time.monotonic()
        rules = self._load_rules()

        all_elements: list[ExtractedElement] = []
        documents_processed = 0
        errors_count = 0

        for doc in documents:
            elements, err = self._process_document(doc, rules)
            all_elements.extend(elements)
            if err:
                errors_count += err
            else:
                documents_processed += 1

        duration_ms = int((time.monotonic() - start) * 1000)

        elements_by_type: dict[str, int] = {}
        for el in all_elements:
            t = str(el.type)
            elements_by_type[t] = elements_by_type.get(t, 0) + 1

        return ExtractionResult(
            elements=all_elements,
            engine_id="deterministic",
            processing_stats=ProcessingStats(
                documents_processed=documents_processed,
                elements_extracted=len(all_elements),
                elements_by_type=elements_by_type,
                duration_ms=duration_ms,
                errors_count=errors_count,
            ),
        )
