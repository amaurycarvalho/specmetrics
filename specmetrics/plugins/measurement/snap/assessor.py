from __future__ import annotations

import hashlib
from typing import Optional
from uuid import uuid4

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .models import (
    SNAPMeasurementResult,
    AssessedItem,
    AssessmentSummary,
    CategoryAssessment,
    CategoryBreakdown,
    AssessmentWarning,
    CategoryDefinition,
    CategoryId,
    DEFAULT_CATEGORIES,
    EvidenceRef,
    RulePack,
    SEMANTIC_MARKER_TO_CATEGORY,
)
from .rule_applicator import RulePackApplicator


class SNAPAssessor:
    def __init__(self, categories: Optional[list[CategoryDefinition]] = None):
        self.categories = categories or DEFAULT_CATEGORIES
        self._category_map: dict[CategoryId, CategoryDefinition] = {
            cat.id: cat for cat in self.categories
        }

    def assess(
        self,
        cfm: CanonicalFunctionalModel,
        rule_pack: Optional[RulePack] = None,
        run_id: Optional[str] = None,
        previous_result: Optional[SNAPMeasurementResult] = None,
        modified_element_ids: Optional[list[str]] = None,
    ) -> SNAPMeasurementResult:
        applicator = RulePackApplicator()
        applicator_warnings = applicator.validate_rule_pack(rule_pack)
        rule_pack_id = rule_pack.id if rule_pack else None

        excluded_categories: set[CategoryId] = set()
        contribution_overrides: dict[CategoryId, float] = {}
        inclusion_overrides: dict[str, str] = {}
        exclusion_by_id: set[str] = set()
        exclusion_patterns: list[str] = []

        if rule_pack is not None:
            excluded_categories = set(rule_pack.excluded_categories or [])
            if rule_pack.contribution_overrides:
                contribution_overrides = rule_pack.contribution_overrides
            if rule_pack.inclusion_policies:
                for policy in rule_pack.inclusion_policies:
                    marker = policy.get("semantic_marker")
                    category = policy.get("category")
                    if marker and category:
                        inclusion_overrides[marker] = category
            if rule_pack.item_exclusions:
                exclusion_by_id = set(rule_pack.item_exclusions.get("by_id", []))
                exclusion_patterns = rule_pack.item_exclusions.get("by_pattern", [])

        items: list[AssessedItem] = []
        warnings: list[AssessmentWarning] = list(applicator_warnings)
        seen_fingerprints: dict[str, str] = {}
        item_counter = 0

        elements = self._collect_elements(cfm)

        for elem_id, elem in elements:
            semantic_marker = elem.metadata.get("semantic_marker", "")
            if not semantic_marker:
                warnings.append(AssessmentWarning(
                    code="MISSING_SEMANTIC_MARKER",
                    message=f"Element '{elem_id}' has no semantic metadata marker",
                    cfm_element_id=elem_id,
                ))
                continue

            if semantic_marker not in SEMANTIC_MARKER_TO_CATEGORY and semantic_marker not in inclusion_overrides:
                warnings.append(AssessmentWarning(
                    code="UNSUPPORTED_MARKER",
                    message=f"Unsupported semantic marker '{semantic_marker}' on element '{elem_id}'",
                    cfm_element_id=elem_id,
                    details={"marker": semantic_marker},
                ))
                continue

            category_id_str = inclusion_overrides.get(semantic_marker, SEMANTIC_MARKER_TO_CATEGORY.get(semantic_marker))
            if category_id_str is None:
                continue

            category_id: CategoryId = category_id_str
            if category_id in excluded_categories:
                continue

            cat_def = self._category_map.get(category_id)
            if cat_def is None:
                continue

            contribution = contribution_overrides.get(category_id, cat_def.default_contribution)

            refs: list[EvidenceRef] = []
            if hasattr(elem, "evidence") and elem.evidence:
                refs.append(EvidenceRef(
                    graph_node_id=elem.evidence.graph_node_id,
                    document_id=elem.evidence.document_id,
                    section_id=elem.evidence.section_id,
                    text=elem.evidence.text,
                ))

            item_counter += 1
            item = AssessedItem(
                id=f"snap-item-{item_counter}",
                name=elem.name if hasattr(elem, "name") else elem_id,
                category_id=category_id,
                contribution=contribution,
                cfm_element_id=elem_id,
                cfm_semantic_marker=semantic_marker,
                evidence_refs=refs,
            )

            item, dedup_warning = self._deduplicate(item, seen_fingerprints, elem_id, elem)
            if dedup_warning:
                warnings.append(dedup_warning)
            if item is None:
                item_counter -= 1
                continue

            excluded_flag, exclusion_warning = self._check_exclusion(
                item, elem_id, elem, exclusion_by_id, exclusion_patterns, rule_pack
            )
            if exclusion_warning:
                warnings.append(exclusion_warning)

            items.append(item)

        if previous_result is not None and modified_element_ids is not None:
            modified_set = set(modified_element_ids)
            kept = [i for i in previous_result.assessed_items if i.cfm_element_id not in modified_set]
            existing_ids = {i.cfm_element_id for i in items}
            for i in kept:
                if i.cfm_element_id not in existing_ids:
                    items.append(i)

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

    def _collect_elements(self, cfm: CanonicalFunctionalModel) -> list[tuple[str, object]]:
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

    def _fingerprint(self, elem_id: str, elem) -> str:
        evidence = getattr(elem, "evidence", None)
        doc_id = evidence.document_id if evidence else ""
        section_id = evidence.section_id if evidence else ""
        text = evidence.text if evidence else ""
        semantic_marker = elem.metadata.get("semantic_marker", "") if hasattr(elem, "metadata") else ""
        raw = f"{elem_id}:{doc_id}:{section_id or ''}:{text}:{semantic_marker}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _deduplicate(
        self,
        item: AssessedItem,
        seen_fingerprints: dict[str, str],
        elem_id: str,
        elem,
    ) -> tuple[Optional[AssessedItem], Optional[AssessmentWarning]]:
        fp = self._fingerprint(elem_id, elem)
        if fp in seen_fingerprints:
            return None, AssessmentWarning(
                code="DUPLICATE_MERGED",
                message=f"Duplicate item '{item.name}' merged; only one counted",
                cfm_element_id=item.cfm_element_id,
                details={"merged_into": seen_fingerprints[fp]},
            )
        seen_fingerprints[fp] = item.id
        return item, None

    def _check_exclusion(
        self,
        item: AssessedItem,
        elem_id: str,
        elem,
        exclusion_by_id: set[str],
        exclusion_patterns: list[str],
        rule_pack: Optional[RulePack],
    ) -> tuple[bool, Optional[AssessmentWarning]]:
        import fnmatch

        if elem_id in exclusion_by_id:
            item.excluded = True
            item.contribution = 0.0
            item.rule_applied = "excluded_by_id"
            return True, AssessmentWarning(
                code="ITEM_EXCLUDED",
                message=f"Item '{item.name}' excluded by Rule Pack (by_id)",
                cfm_element_id=elem_id,
            )

        elem_name = getattr(elem, "name", "")
        for pattern in exclusion_patterns:
            if fnmatch.fnmatch(elem_id, pattern) or fnmatch.fnmatch(elem_name, pattern):
                item.excluded = True
                item.contribution = 0.0
                item.rule_applied = f"excluded_by_pattern:{pattern}"
                return True, AssessmentWarning(
                    code="ITEM_EXCLUDED",
                    message=f"Item '{item.name}' excluded by Rule Pack pattern '{pattern}'",
                    cfm_element_id=elem_id,
                )

        return False, None

    def _build_categories(self, items: list[AssessedItem]) -> list[CategoryAssessment]:
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
            categories.append(CategoryAssessment(
                category_id=cat_def.id,
                category_name=cat_def.name,
                category_version=cat_def.version,
                items=cat_item_list,
                total_contribution=total_contribution,
            ))
        return categories

    def _build_summary(self, items: list[AssessedItem]) -> AssessmentSummary:
        total_items = len(items)
        active_items = [i for i in items if not i.excluded]
        total_active = len(active_items)
        total_snap = sum(i.contribution for i in active_items)

        by_category: dict[CategoryId, CategoryBreakdown] = {}
        for item in items:
            if item.category_id not in by_category:
                by_category[item.category_id] = CategoryBreakdown(item_count=0, total_snap=0.0)
            by_category[item.category_id].item_count += 1
            if not item.excluded:
                by_category[item.category_id].total_snap += item.contribution

        return AssessmentSummary(
            total_item_count=total_items,
            total_active_count=total_active,
            total_snap=total_snap,
            by_category=by_category,
        )
