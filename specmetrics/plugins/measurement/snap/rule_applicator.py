"""Rule pack resolution helpers for the SNAP measurement plugin."""

from __future__ import annotations

from typing import Self

from .models import AssessmentWarning, CategoryId, RulePack


class RulePackApplicator:
    """Applies rule pack overrides to SNAP assessment configuration."""

    def validate_rule_pack(
        self: Self, rule_pack: RulePack | None
    ) -> list[AssessmentWarning]:
        """Validate the rule pack and return a list of warnings."""
        warnings: list[AssessmentWarning] = []
        if rule_pack is None:
            return warnings
        self._validate_methodology(rule_pack, warnings)
        self._validate_contribution_overrides(rule_pack, warnings)
        self._validate_excluded_categories(rule_pack, warnings)
        self._validate_inclusion_policies(rule_pack, warnings)
        return warnings

    def _validate_methodology(
        self: Self, rule_pack: RulePack, warnings: list[AssessmentWarning]
    ) -> None:
        if rule_pack.methodology and rule_pack.methodology != "SNAP":
            warnings.append(
                AssessmentWarning(
                    code="RULE_PACK_METHODOLOGY_MISMATCH",
                    message=f"Rule Pack methodology '{rule_pack.methodology}' does not match SNAP; applying defaults for unrecognized fields",
                )
            )

    def _validate_contribution_overrides(
        self: Self, rule_pack: RulePack, warnings: list[AssessmentWarning]
    ) -> None:
        if rule_pack.contribution_overrides:
            for cat_id, val in rule_pack.contribution_overrides.items():
                if val <= 0:
                    warnings.append(
                        AssessmentWarning(
                            code="INVALID_CONTRIBUTION_OVERRIDE",
                            message=f"Invalid contribution override for {cat_id}: {val}; must be positive. Override ignored.",
                        )
                    )

    def _validate_excluded_categories(
        self: Self, rule_pack: RulePack, warnings: list[AssessmentWarning]
    ) -> None:
        if rule_pack.excluded_categories:
            valid_ids = {
                "presentation",
                "data_operations",
                "operational_capabilities",
                "technical_interaction",
            }
            for cat_id in rule_pack.excluded_categories:
                if cat_id not in valid_ids:
                    warnings.append(
                        AssessmentWarning(
                            code="UNKNOWN_CATEGORY",
                            message=f"Unknown category '{cat_id}' in excluded_categories; ignored",
                        )
                    )

    def _validate_inclusion_policies(
        self: Self, rule_pack: RulePack, warnings: list[AssessmentWarning]
    ) -> None:
        if rule_pack.inclusion_policies:
            for policy in rule_pack.inclusion_policies:
                if not isinstance(policy, dict):
                    warnings.append(
                        AssessmentWarning(
                            code="INVALID_INCLUSION_POLICY",
                            message="Invalid inclusion policy entry; must be a mapping with 'semantic_marker' and 'category'",
                        )
                    )
                    continue
                marker = policy.get("semantic_marker")
                category = policy.get("category")
                if not marker or not category:
                    warnings.append(
                        AssessmentWarning(
                            code="INCOMPLETE_INCLUSION_POLICY",
                            message="Inclusion policy missing 'semantic_marker' or 'category'",
                        )
                    )

    def resolve_contribution_overrides(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[CategoryId, float] | None:
        """Resolve contribution overrides from the rule pack."""
        if rule_pack is None or rule_pack.contribution_overrides is None:
            return None
        overrides: dict[CategoryId, float] = {}
        for cat_id in (
            "presentation",
            "data_operations",
            "operational_capabilities",
            "technical_interaction",
        ):
            if cat_id in rule_pack.contribution_overrides:
                overrides[cat_id] = rule_pack.contribution_overrides[cat_id]
        return overrides if overrides else None

    def resolve_excluded_categories(
        self: Self,
        rule_pack: RulePack | None,
    ) -> list[CategoryId]:
        """Resolve the list of excluded categories from the rule pack."""
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_categories)

    def resolve_item_exclusions(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, list[str]] | None:
        """Resolve item exclusion rules from the rule pack."""
        if rule_pack is None:
            return None
        return rule_pack.item_exclusions

    def resolve_inclusion_policies(
        self: Self,
        rule_pack: RulePack | None,
    ) -> list[dict[str, str]] | None:
        """Resolve inclusion policies from the rule pack."""
        if rule_pack is None:
            return None
        return rule_pack.inclusion_policies
