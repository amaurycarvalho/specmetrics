from __future__ import annotations

import hashlib
import re
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

_EXPECTED_RULE_PACK_MAJOR_VERSION = 1


def _is_likely_binary(content: str) -> bool:
    if not content:
        return False
    control = sum(1 for c in content if ord(c) < 32 and c not in "\n\r\t\f\v")
    return control / len(content) > _NON_TEXT_THRESHOLD


def _content_hash(document_id: str, section_id: str | None, text: str) -> str:
    raw = f"{document_id}::{section_id or ''}::{text}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _parse_major_version(version: str) -> int | None:
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError):
        return None


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

    def _check_pack_version(self, path: str | Path) -> None:
        try:
            meta = RulePackLoader.load_meta(path)
            if meta.version:
                if not RulePackLoader.validate_version(meta.version):
                    logger.warning(
                        "rule_pack_invalid_version",
                        path=str(path),
                        version=meta.version,
                    )
                else:
                    major = _parse_major_version(meta.version)
                    if major is not None and major != _EXPECTED_RULE_PACK_MAJOR_VERSION:
                        logger.warning(
                            "rule_pack_major_version_mismatch",
                            path=str(path),
                            version=meta.version,
                            expected_major=_EXPECTED_RULE_PACK_MAJOR_VERSION,
                        )
        except (FileNotFoundError, RuntimeError) as exc:
            logger.warning("rule_pack_version_check_failed", path=str(path), error=str(exc))

    def _match_rule_against_observation(
        self, rule: ExtractionRule, section_type: str, heading_text: str, content: str
    ) -> bool:
        pat = rule.pattern

        regex = pat.get("regex", "")
        if regex:
            try:
                if re.search(regex, content):
                    return True
                if re.search(regex, heading_text):
                    return True
            except re.error:
                logger.warning("regex_error", rule_id=rule.id, pattern=regex)
            return False

        heading_match = pat.get("heading", "")
        if heading_match:
            candidates = [section_type, heading_text]
            if section_type != heading_text:
                candidates.append(heading_text)
            match_values = [heading_match] if isinstance(heading_match, str) else heading_match
            for h_candidate in candidates:
                for m in match_values:
                    if isinstance(m, str) and m.lower() == h_candidate.lower():
                        return True
            return False

        keywords = pat.get("keywords", [])
        if keywords:
            min_matches = pat.get("min_matches", len(keywords))
            matched = sum(1 for kw in keywords if kw.lower() in content.lower())
            return matched >= min_matches

        structure = pat.get("structure")
        if structure:
            return True

        return False

    def _execute_rules(
        self, doc: Document, rules: list[ExtractionRule]
    ) -> tuple[list[ExtractedElement], int, int, int, set[str]]:
        if _md is None:
            logger.error("markdown_it_not_available")
            return [], 0, 0, len(rules), set()

        if _is_likely_binary(doc.content):
            logger.warning("skipping_binary_content", doc_id=doc.id)
            return [], 0, 0, len(rules), set()

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
        rules_attempted = 0
        rules_succeeded = 0
        rules_failed = 0
        failed_rule_ids: set[str] = set()
        doc_type = (doc.document_type or "").lower()

        for obs in state.observations:
            section_type = obs.context.get("section_type", "")
            content = obs.content
            doc_id = doc.id
            section_id = obs.location[1]

            for rule in rules:
                if rule.document_type and rule.document_type != doc_type:
                    continue
                if rule.target_sections:
                    st_lower = section_type.lower()
                    if not any(ts.lower() == st_lower for ts in rule.target_sections):
                        continue

                rules_attempted += 1
                try:
                    if self._match_rule_against_observation(rule, section_type, section_type, content):
                        elem_id = _content_hash(doc_id, section_id, content)
                        evidence = EvidenceReference(
                            document_id=doc_id,
                            section_id=section_id,
                            text=content,
                            rule_id=rule.id,
                        )
                        element = ExtractedElement(
                            id=elem_id,
                            type=rule.type,
                            content=content,
                            confidence=rule.confidence,
                            evidence=evidence,
                        )
                        elements.append(element)
                        rules_succeeded += 1
                except Exception as exc:
                    rules_failed += 1
                    failed_rule_ids.add(rule.id)
                    logger.warning(
                        "rule_execution_failed",
                        rule_id=rule.id,
                        doc_id=doc.id,
                        error=str(exc),
                    )

        return elements, rules_attempted, rules_succeeded, rules_failed, failed_rule_ids

    def _load_framework_packs(self, documents: list[Document]) -> list[str]:
        detected: set[str] = set()
        rules_dir = Path(__file__).parent / "rules"
        for doc in documents:
            dt = (doc.document_type or "").lower()
            if "openspec" in dt or dt in ("use_case", "actor", "requirement"):
                detected.add("openspec")
            if "speckit" in dt or dt in ("feature", "scenario", "background"):
                detected.add("speckit")
        packs: list[str] = []
        if "openspec" in detected:
            osp = str(rules_dir / "openspec_rules.yaml")
            if Path(osp).exists():
                self._check_pack_version(osp)
                packs.append(osp)
        if "speckit" in detected:
            skp = str(rules_dir / "speckit_rules.yaml")
            if Path(skp).exists():
                self._check_pack_version(skp)
                packs.append(skp)
        return packs

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
        self._extra_rule_packs.extend(self._load_framework_packs(documents))
        rules = self._load_rules()

        all_elements: list[ExtractedElement] = []
        documents_processed = 0
        errors_count = 0

        for doc in documents:
            doc_start = time.monotonic()
            elements, attempted, succeeded, failed, failed_ids = self._execute_rules(doc, rules)
            all_elements.extend(elements)

            duration = int((time.monotonic() - doc_start) * 1000)
            total_rules = attempted or 1
            success_rate = (succeeded / total_rules) * 100

            if attempted > 0 and success_rate < 99.0:
                logger.debug(
                    "low_extraction_success_rate",
                    document_id=doc.id,
                    success_rate=round(success_rate, 2),
                    rules_attempted=attempted,
                    rules_succeeded=succeeded,
                    rules_failed=failed,
                    failed_rule_ids=sorted(failed_ids),
                    duration_ms=duration,
                )

            if failed > 0:
                errors_count += failed
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
