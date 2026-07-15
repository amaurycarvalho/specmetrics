from __future__ import annotations

from typing import Optional

from .complexity import (
    UFP_WEIGHTS,
)
from .models import FunctionType, RulePack


class RulePackApplicator:
    def resolve_weights(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, dict[str, int]]]:
        if rule_pack is None or rule_pack.weight_overrides is None:
            return None
        merged: dict[str, dict[str, int]] = {}
        for ft in ("ILF", "EIF", "EI", "EO", "EQ"):
            defaults = UFP_WEIGHTS.get(ft, {})
            overrides = rule_pack.weight_overrides.get(ft, {})
            merged[ft] = {**defaults, **overrides}
        return merged

    def resolve_excluded_types(
        self,
        rule_pack: Optional[RulePack],
    ) -> list[FunctionType]:
        if rule_pack is None:
            return []
        return list(rule_pack.excluded_types)

    def resolve_complexity_overrides(
        self,
        rule_pack: Optional[RulePack],
    ) -> Optional[dict[str, dict[str, list[int]]]]:
        if rule_pack is None or rule_pack.complexity_overrides is None:
            return None
        return rule_pack.complexity_overrides

    def compute_vaf(self, rule_pack: Optional[RulePack]) -> Optional[float]:
        if rule_pack is None or rule_pack.vaf is None:
            return None
        gsc = rule_pack.vaf
        total = sum(gsc.values())
        return 0.65 + (0.01 * total)

    def apply_to_function(
        self,
        function_type: FunctionType,
        cfm_element_id: str,
        rule_pack: Optional[RulePack],
    ) -> Optional[str]:
        if rule_pack is None:
            return None
        if rule_pack.element_exclusions:
            by_id = rule_pack.element_exclusions.get("by_id", [])
            if cfm_element_id in by_id:
                return "excluded_by_id"
        return None
