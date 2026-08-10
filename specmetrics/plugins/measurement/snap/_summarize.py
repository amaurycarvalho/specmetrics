"""Element collection and aggregation helpers for the SNAP assessor."""
from __future__ import annotations

from typing import Self

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .models import (
    AssessedItem,
    AssessmentSummary,
    CategoryAssessment,
    CategoryBreakdown,
    CategoryId,
    SNAPMeasurementResult,
)


class _AssessorAggregationMixin:
    """Collects CFM elements and builds category and summary results."""

    def _merge_previous(
        self: Self,
        items: list[AssessedItem],
        previous_result: SNAPMeasurementResult | None,
        modified_element_ids: list[str] | None,
    ) -> None:
        if previous_result is None or modified_element_ids is None:
            return
        modified_set = set(modified_element_ids)
        existing_ids = {i.cfm_element_id for i in items}
        for i in previous_result.assessed_items:
            if i.cfm_element_id not in modified_set and i.cfm_element_id not in existing_ids:
                items.append(i)

    def _collect_elements(
        self: Self, cfm: CanonicalFunctionalModel
    ) -> list[tuple[str, object]]:
        elements: list[tuple[str, object]] = []
        for elem_id, elem in cfm.operations.items():
            elements.append((elem_id, elem))
        for elem_id, elem in cfm.data_groups.items():
            elements.append((elem_id, elem))
        for elem_id, elem in cfm.functional_processes.items():
            elements.append((elem_id, elem))
        for elem_id, elem in cfm.business_rules.items():
            elements.append((elem_id, elem))
        for elem_id, elem in cfm.actors.items():
            elements.append((elem_id, elem))
        for elem_id, elem in cfm.unclassified.items():
            elements.append((elem_id, elem))
        return elements

    def _build_categories(self: Self, items: list[AssessedItem]) -> list[CategoryAssessment]:
        cat_items: dict[CategoryId, list[AssessedItem]] = {}
        for item in items:
            if item.category_id not in cat_items:
                cat_items[item.category_id] = []
            cat_items[item.category_id].append(item)

        categories: list[CategoryAssessment] = []
        for cat_def in self.categories:
            cat_item_list = cat_items.get(cat_def.id, [])
            if not cat_item_list:
                continue
            total_contribution = sum(i.contribution for i in cat_item_list)
            categories.append(
                CategoryAssessment(
                    category_id=cat_def.id,
                    category_name=cat_def.name,
                    category_version=cat_def.version,
                    items=cat_item_list,
                    total_contribution=total_contribution,
                )
            )
        return categories

    def _build_summary(self: Self, items: list[AssessedItem]) -> AssessmentSummary:
        total_items = len(items)
        active_items = [i for i in items if not i.excluded]
        total_active = len(active_items)
        total_snap = sum(i.contribution for i in active_items)

        by_category: dict[CategoryId, CategoryBreakdown] = {}
        for item in items:
            if item.category_id not in by_category:
                by_category[item.category_id] = CategoryBreakdown(
                    item_count=0, total_snap=0.0
                )
            by_category[item.category_id].item_count += 1
            if not item.excluded:
                by_category[item.category_id].total_snap += item.contribution

        return AssessmentSummary(
            total_item_count=total_items,
            total_active_count=total_active,
            total_snap=total_snap,
            by_category=by_category,
        )