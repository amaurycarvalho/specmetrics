from __future__ import annotations

from typing import Optional

from .models import AssessmentWarning, CategoryId, RulePack


class RulePackApplicator:
    def validate_rule_pack(self, rule_pack: Optional[RulePack]) -> list[AssessmentWarning]:
        warnings: list[AssessmentWarning] = []
        if rule_pack is None:
            return warnings
        if rule_pack.methodology and rule_pack.methodology != "SNAP":
            warnings.append(AssessmentWarning(
                code="RULE_PACK_METHODOLOGY_MISMATCH",
                message=f"Rule Pack methodology '{rule_pack.methodology}' does not match SNAP; applying defaults for unrecognized fields",
            ))
        if rule_pack.contribution_overrides:
            for cat_id, val in rule_pack.contribution_overrides.items():
                if val <= 0:
                    warnings.append(AssessmentWarning(
                        code="INVALID_CONTRIBUTION_OVERRIDE",
                        message=f"Invalid contribution override for {cat_id}: {val}; must be positive. Override ignored.",
                    ))
        if rule_pack.excluded_categories:
            valid_ids = {"presentation", "data_operations", "operational_capabilities", "technical_interaction"}
            for cat_id in rule_pack.excluded_categories:
                if cat_id not in valid_ids:
                    warnings.append(AssessmentWarning(
                        code="UNKNOWN_CATEGORY",
                        message=f"Unknown category '{cat_id}' in excluded_categories; ignored",
                    ))
        if rule_pack.inclusion_policies:
            for policy in rule_pack.inclusion_policies:
                if not isinstance(policy, dict):
                    warnings.append(AssessmentWarning(
                        code="INVALID_INCLUSION_POLICY",
                        message="Invalid inclusion policy entry; must be a mapping with 'semantic_marker' and 'category'",
                    ))
                    continue
                marker = policy.get("semantic_marker")
                category = policy.get("category")
                if not marker or not category:
                    warnings.append(AssessmentWarning(
                        code="INCOMPLETE_INCLUSION_POLICY",
                        message="Inclusion policy missing 'semantic_marker' or 'category'",
                    ))
        return warnings

    def resolve_contribution_overrides(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[CategoryId, float]]:
        if rule_pack is None or rule_pack.contribution_overrides is None:
            return None
        overrides: dict[CategoryId, float] = {}
        for cat_id in ("presentation", "data_operations", "operational_capabilities", "technical_interaction"):
            if cat_id in rule_pack.contribution_overrides:
                overrides[cat_id] = rule_pack.contribution_overrides[cat_id]
        return overrides if overrides else None

    def resolve_excluded_categories(
        self,
        rule_pack: Optional[RulePack],
    ) -> list[CategoryId]:
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_categories)

    def resolve_item_exclusions(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, list[str]]]:
        if rule_pack is None:
            return None
        return rule_pack.item_exclusions

    def resolve_inclusion_policies(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[list[dict[str, str]]]:
        if rule_pack is None:
            return None
        return rule_pack.inclusion_policies
