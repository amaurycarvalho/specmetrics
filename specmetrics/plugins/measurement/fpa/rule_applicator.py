"""Rule pack resolution helpers for the FPA measurement plugin."""

from __future__ import annotations

from typing import Self

from .complexity import (
    UFP_WEIGHTS,
)
from .models import FunctionType, RulePack


class RulePackApplicator:
    """Applies rule pack overrides to FPA measurement configuration."""

    def resolve_weights(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, dict[str, int]] | None:
        """Resolve merged UFP weight tables from the rule pack."""
        if rule_pack is None or rule_pack.weight_overrides is None:
            return None
        merged: dict[str, dict[str, int]] = {}
        for ft in ("ILF", "EIF", "EI", "EO", "EQ"):
            defaults = UFP_WEIGHTS.get(ft, {})
            overrides = rule_pack.weight_overrides.get(ft, {})
            merged[ft] = {**defaults, **overrides}
        return merged

    def resolve_excluded_types(
        self: Self,
        rule_pack: RulePack | None,
    ) -> list[FunctionType]:
        """Resolve the list of excluded function types from the rule pack."""
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_types)

    def resolve_complexity_overrides(
        self: Self,
        rule_pack: RulePack | None,
    ) -> dict[str, dict[str, list[int]]] | None:
        """Resolve complexity override tables from the rule pack."""
        if rule_pack is None or rule_pack.complexity_overrides is None:
            return None
        return rule_pack.complexity_overrides

    def compute_vaf(self: Self, rule_pack: RulePack | None) -> float | None:
        """Compute the value adjustment factor from the rule pack."""
        if rule_pack is None or rule_pack.vaf is None:
            return None
        gsc = rule_pack.vaf
        total = sum(gsc.values())
        return 0.65 + (0.01 * total)

    def apply_to_function(
        self: Self,
        function_type: FunctionType,
        cfm_element_id: str,
        rule_pack: RulePack | None,
    ) -> str | None:
        """Return the exclusion rule applied to a function, if any."""
        if rule_pack is None:
            return None
        if rule_pack.element_exclusions:
            by_id = rule_pack.element_exclusions.get("by_id", [])
            if cfm_element_id in by_id:
                return "excluded_by_id"
        return None
