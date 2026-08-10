"""Deterministic semantic extraction engine based on pattern rules."""

from __future__ import annotations

import time
from typing import Self

from ._framework_packs import FrameworkPackMixin
from ._matching import MatchingMixin
from ._rule_execution import ExecutionMixin
from ._rule_loading import RuleLoadingMixin
from .adapter_interface import Document
from .engine_patterns import PatternLibrary
from .semantic_extraction_engine import (
    ExtractionResult,
    ProcessingStats,
    SemanticExtractionEngine,
)

_MARKDOWN_NOT_AVAILABLE = False


class DeterministicSemanticEngine(
    RuleLoadingMixin,
    MatchingMixin,
    ExecutionMixin,
    FrameworkPackMixin,
    SemanticExtractionEngine,
):
    """Semantic extraction engine that matches documents against rule packs."""

    def __init__(
        self: Self,
        max_heading_depth: int = 6,
        default_rule_pack: str | None = None,
        extra_rule_packs: list[str] | None = None,
        default_confidence: float = 0.70,
    ) -> None:
        """Initialize the deterministic extraction engine with rule packs."""
        self._max_heading_depth = max_heading_depth
        self._default_rule_pack = default_rule_pack
        self._extra_rule_packs = extra_rule_packs or []
        self._default_confidence = default_confidence
        self._pattern_library: PatternLibrary | None = None

    def extract(self: Self, documents: list[Document]) -> ExtractionResult:
        """Run deterministic rule extraction over the given documents."""
        if not documents:
            return self._empty_result()

        start = time.monotonic()
        self._extra_rule_packs.extend(self._load_framework_packs(documents))
        rules = self._load_rules()

        all_elements: list = []
        documents_processed = 0
        errors_count = 0

        for doc in documents:
            doc_start = time.monotonic()
            elements, attempted, succeeded, failed, failed_ids = self._execute_rules(
                doc, rules
            )
            all_elements.extend(elements)

            duration = int((time.monotonic() - doc_start) * 1000)
            total_rules = attempted or 1
            success_rate = (succeeded / total_rules) * 100

            if attempted > 0 and success_rate < 99.0:
                self._log_low_success(
                    doc, success_rate, attempted, succeeded, failed, failed_ids, duration
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

    def _empty_result(self: Self) -> ExtractionResult:
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

    def _log_low_success(
        self: Self,
        doc: Document,
        success_rate: float,
        attempted: int,
        succeeded: int,
        failed: int,
        failed_ids: set[str],
        duration: int,
    ) -> None:
        import structlog

        logger = structlog.get_logger(__name__)
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