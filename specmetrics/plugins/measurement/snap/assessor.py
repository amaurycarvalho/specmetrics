"""Assessor that evaluates CFM elements against SNAP categories."""

from __future__ import annotations

from typing import Self
from uuid import uuid4

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from ._processing import _AssessorProcessingMixin
from ._summarize import _AssessorAggregationMixin
from .models import (
    DEFAULT_CATEGORIES,
    AssessedItem,
    AssessmentWarning,
    CategoryDefinition,
    CategoryId,
    RulePack,
    SNAPMeasurementResult,
)
from .rule_applicator import RulePackApplicator

__all__ = ["SNAPAssessor"]


class SNAPAssessor(_AssessorProcessingMixin, _AssessorAggregationMixin):
    """Assesses CFM elements and produces a SNAP measurement result."""

    def __init__(
        self: Self, categories: list[CategoryDefinition] | None = None
    ) -> None:
        """Initialize the assessor with the given category definitions."""
        self.categories = categories or DEFAULT_CATEGORIES
        self._category_map: dict[CategoryId, CategoryDefinition] = {
            cat.id: cat for cat in self.categories
        }

    def assess(
        self: Self,
        cfm: CanonicalFunctionalModel,
        rule_pack: RulePack | None = None,
        run_id: str | None = None,
        previous_result: SNAPMeasurementResult | None = None,
        modified_element_ids: list[str] | None = None,
    ) -> SNAPMeasurementResult:
        """Assess SNAP points for the given canonical functional model."""
        applicator = RulePackApplicator()
        applicator_warnings = applicator.validate_rule_pack(rule_pack)
        rule_pack_id = rule_pack.id if rule_pack else None

        rp_config = self._build_rule_pack_config(rule_pack)

        items: list[AssessedItem] = []
        warnings: list[AssessmentWarning] = list(applicator_warnings)
        seen_fingerprints: dict[str, str] = {}
        item_counter = 0

        elements = self._collect_elements(cfm)

        for elem_id, elem in elements:
            processed = self._process_element(
                elem_id, elem, rp_config, seen_fingerprints, item_counter, warnings
            )
            if processed is None:
                continue
            item, item_counter = processed
            items.append(item)

        self._merge_previous(items, previous_result, modified_element_ids)

        categories = self._build_categories(items)
        summary = self._build_summary(items)
        result = SNAPMeasurementResult(
            run_id=run_id or str(uuid4()),
            cfm_run_id=cfm.run_id,
            rule_pack_id=rule_pack_id,
            categories=categories,
            assessed_items=items,
            summary=summary,
            warnings=warnings,
        )

        return result