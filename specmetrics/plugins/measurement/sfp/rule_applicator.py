"""Rule pack resolution helpers for the SFP measurement plugin."""

from __future__ import annotations

from typing import Self

from .models import ComponentType, RulePack

DEFAULT_FP_CONTRIBUTION = 4.6
DEFAULT_LF_CONTRIBUTION = 7.1


class RulePackApplicator:
    """Applies rule pack overrides to SFP measurement configuration."""

    def resolve_contribution_overrides(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[ComponentType, float] | None:
        """Resolve contribution overrides from the rule pack."""
        if rule_pack is None or rule_pack.contribution_overrides is None:
            return None
        overrides: dict[ComponentType, float] = {}
        for ct in ("functional_process", "logical_function"):
            if ct in rule_pack.contribution_overrides:
                overrides[ct] = rule_pack.contribution_overrides[ct]
        return overrides if overrides else None

    def resolve_excluded_types(
        self: Self,
        rule_pack: RulePack | None,
    ) -> list[ComponentType]:
        """Resolve the list of excluded component types from the rule pack."""
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_types)

    def resolve_element_exclusions(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, list[str]] | None:
        """Resolve element exclusion rules from the rule pack."""
        if rule_pack is None:
            return None
        return rule_pack.element_exclusions

    def resolve_element_inclusions(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, list[str]] | None:
        """Resolve element inclusion rules from the rule pack."""
        if rule_pack is None:
            return None
        return rule_pack.element_inclusions

    def resolve_inclusion_criteria(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, dict[str, list[str]]] | None:
        """Resolve inclusion criteria from the rule pack."""
        if rule_pack is None:
            return None
        return rule_pack.inclusion_criteria

    def apply_to_component(
        self: Self,
        component_type: ComponentType,
        cfm_element_id: str,
        rule_pack: RulePack | None,
    ) -> str | None:
        """Return the exclusion rule applied to a component, if any."""
        if rule_pack is None:
            return None
        if rule_pack.element_exclusions:
            by_id = rule_pack.element_exclusions.get("by_id", [])
            if cfm_element_id in by_id:
                return "excluded_by_id"
            by_pattern = rule_pack.element_exclusions.get("by_pattern", [])
            import fnmatch

            for pattern in by_pattern:
                if fnmatch.fnmatch(cfm_element_id, pattern):
                    return f"excluded_by_pattern:{pattern}"
        return None

    def validate_rule_pack(self: Self, rule_pack: RulePack | None) -> list[str]:
        """Validate the rule pack and return a list of warning messages."""
        warnings: list[str] = []
        if rule_pack is None:
            return warnings
        if rule_pack.methodology and rule_pack.methodology != "SFP":
            warnings.append(
                f"Rule Pack methodology '{rule_pack.methodology}' does not match "
                f"SFP; applying defaults for unrecognized fields"
            )
        if rule_pack.contribution_overrides:
            for ct, val in rule_pack.contribution_overrides.items():
                if val <= 0:
                    warnings.append(
                        f"Invalid contribution override for {ct}: {val}; "
                        f"must be positive. Override ignored."
                    )
        if rule_pack.excluded_types:
            for ct in rule_pack.excluded_types:
                if ct not in ("functional_process", "logical_function"):
                    warnings.append(
                        f"Unknown component type '{ct}' in excluded_types; ignored"
                    )
        return warnings
