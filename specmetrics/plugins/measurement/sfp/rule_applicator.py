from __future__ import annotations

from typing import Optional

from .models import ComponentType, RulePack

DEFAULT_FP_CONTRIBUTION = 4.6
DEFAULT_LF_CONTRIBUTION = 7.1


class RulePackApplicator:
    def resolve_contribution_overrides(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[ComponentType, float]]:
        if rule_pack is None or rule_pack.contribution_overrides is None:
            return None
        overrides: dict[ComponentType, float] = {}
        for ct in ("functional_process", "logical_function"):
            if ct in rule_pack.contribution_overrides:
                overrides[ct] = rule_pack.contribution_overrides[ct]
        return overrides if overrides else None

    def resolve_excluded_types(
        self,
        rule_pack: Optional[RulePack],
    ) -> list[ComponentType]:
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_types)

    def resolve_element_exclusions(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, list[str]]]:
        if rule_pack is None:
            return None
        return rule_pack.element_exclusions

    def resolve_element_inclusions(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, list[str]]]:
        if rule_pack is None:
            return None
        return rule_pack.element_inclusions

    def resolve_inclusion_criteria(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, dict[str, list[str]]]]:
        if rule_pack is None:
            return None
        return rule_pack.inclusion_criteria

    def apply_to_component(
        self,
        component_type: ComponentType,
        cfm_element_id: str,
        rule_pack: Optional[RulePack],
    ) -> Optional[str]:
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

    def validate_rule_pack(self, rule_pack: Optional[RulePack]) -> list[str]:
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
