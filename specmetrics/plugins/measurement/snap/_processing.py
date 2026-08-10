"""Element processing helpers for the SNAP assessor."""
from __future__ import annotations

import fnmatch
import hashlib
from dataclasses import dataclass, field
from typing import Self

from .models import (
    SEMANTIC_MARKER_TO_CATEGORY,
    AssessedItem,
    AssessmentWarning,
    CategoryId,
    EvidenceRef,
    RulePack,
)


@dataclass
class _RulePackConfig:
    """Resolved rule pack configuration used while assessing elements."""

    excluded_categories: set[CategoryId] = field(default_factory=set)
    contribution_overrides: dict[CategoryId, float] = field(default_factory=dict)
    inclusion_overrides: dict[str, str] = field(default_factory=dict)
    exclusion_by_id: set[str] = field(default_factory=set)
    exclusion_patterns: list[str] = field(default_factory=list)


class _AssessorProcessingMixin:
    """Resolves element assignments and applies rule pack exclusions."""

    def _build_rule_pack_config(
        self: Self, rule_pack: RulePack | None
    ) -> _RulePackConfig:
        config = _RulePackConfig()
        if rule_pack is None:
            return config
        config.excluded_categories = set(rule_pack.excluded_categories or [])
        if rule_pack.contribution_overrides:
            config.contribution_overrides = rule_pack.contribution_overrides
        if rule_pack.inclusion_policies:
            for policy in rule_pack.inclusion_policies:
                marker = policy.get("semantic_marker")
                category = policy.get("category")
                if marker and category:
                    config.inclusion_overrides[marker] = category
        if rule_pack.item_exclusions:
            config.exclusion_by_id = set(rule_pack.item_exclusions.get("by_id", []))
            config.exclusion_patterns = rule_pack.item_exclusions.get("by_pattern", [])
        return config

    def _process_element(
        self: Self,
        elem_id: str,
        elem: object,
        config: _RulePackConfig,
        seen_fingerprints: dict[str, str],
        item_counter: int,
        warnings: list[AssessmentWarning],
    ) -> tuple[AssessedItem, int] | None:
        assignment = self._resolve_assignment(elem_id, elem, config, warnings)
        if assignment is None:
            return None

        semantic_marker, category_id, contribution = assignment
        item_counter += 1
        item = AssessedItem(
            id=f"snap-item-{item_counter}",
            name=elem.name if hasattr(elem, "name") else elem_id,
            category_id=category_id,
            contribution=contribution,
            cfm_element_id=elem_id,
            cfm_semantic_marker=semantic_marker,
            evidence_refs=self._evidence_refs(elem),
        )

        item, dedup_warning = self._deduplicate(
            item, seen_fingerprints, elem_id, elem
        )
        if dedup_warning:
            warnings.append(dedup_warning)
        if item is None:
            return None

        _excluded_flag, exclusion_warning = self._check_exclusion(
            item,
            elem_id,
            elem,
            config.exclusion_by_id,
            config.exclusion_patterns,
            None,
        )
        if exclusion_warning:
            warnings.append(exclusion_warning)

        return item, item_counter

    def _resolve_assignment(
        self: Self,
        elem_id: str,
        elem: object,
        config: _RulePackConfig,
        warnings: list[AssessmentWarning],
    ) -> tuple[str, CategoryId, float] | None:
        semantic_marker = elem.metadata.get("semantic_marker", "")
        if not semantic_marker:
            warnings.append(
                AssessmentWarning(
                    code="MISSING_SEMANTIC_MARKER",
                    message=f"Element '{elem_id}' has no semantic metadata marker",
                    cfm_element_id=elem_id,
                )
            )
            return None

        if (
            semantic_marker not in SEMANTIC_MARKER_TO_CATEGORY
            and semantic_marker not in config.inclusion_overrides
        ):
            warnings.append(
                AssessmentWarning(
                    code="UNSUPPORTED_MARKER",
                    message=f"Unsupported semantic marker '{semantic_marker}' on element '{elem_id}'",
                    cfm_element_id=elem_id,
                    details={"marker": semantic_marker},
                )
            )
            return None

        category_id = self._category_for(semantic_marker, config)
        if category_id is None:
            return None
        if category_id in config.excluded_categories:
            return None
        cat_def = self._category_map.get(category_id)
        if cat_def is None:
            return None
        contribution = config.contribution_overrides.get(
            category_id, cat_def.default_contribution
        )
        return semantic_marker, category_id, contribution

    def _category_for(
        self: Self, semantic_marker: str, config: _RulePackConfig
    ) -> CategoryId | None:
        resolved: CategoryId | None = config.inclusion_overrides.get(
            semantic_marker, SEMANTIC_MARKER_TO_CATEGORY.get(semantic_marker)
        )
        return resolved

    def _evidence_refs(self: Self, elem: object) -> list[EvidenceRef]:
        if not hasattr(elem, "evidence") or not elem.evidence:
            return []
        return [
            EvidenceRef(
                graph_node_id=elem.evidence.graph_node_id,
                document_id=elem.evidence.document_id,
                section_id=elem.evidence.section_id,
                text=elem.evidence.text,
            )
        ]

    def _fingerprint(self: Self, elem_id: str, elem: object) -> str:
        evidence = getattr(elem, "evidence", None)
        doc_id = evidence.document_id if evidence else ""
        section_id = evidence.section_id if evidence else ""
        text = evidence.text if evidence else ""
        semantic_marker = (
            elem.metadata.get("semantic_marker", "")
            if hasattr(elem, "metadata")
            else ""
        )
        raw = f"{elem_id}:{doc_id}:{section_id or ''}:{text}:{semantic_marker}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _deduplicate(
        self: Self,
        item: AssessedItem,
        seen_fingerprints: dict[str, str],
        elem_id: str,
        elem: object,
    ) -> tuple[AssessedItem | None, AssessmentWarning | None]:
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
        self: Self,
        item: AssessedItem,
        elem_id: str,
        elem: object,
        exclusion_by_id: set[str],
        exclusion_patterns: list[str],
        rule_pack: RulePack | None,
    ) -> tuple[bool, AssessmentWarning | None]:
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