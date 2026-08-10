"""Mutable accumulation of rule overrides while scanning rule packs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Self


@dataclass
class RuleApplyState:
    """Mutable accumulation of rule overrides while scanning rule packs."""

    excluded_types: set[str] = field(default_factory=set)
    excluded_element_ids: set[str] = field(default_factory=set)
    vaf_value: float | None = None
    complexity_overrides: list[dict[str, Any]] = field(default_factory=list)
    weight_overrides: list[dict[str, Any]] = field(default_factory=list)
    glossary: dict[str, str] = field(default_factory=dict)
    seen_exclusions: set[str] = field(default_factory=set)
    seen_complexity: set[str] = field(default_factory=set)
    seen_weight: set[str] = field(default_factory=set)

    def seen_for(self: Self, rule_type: str) -> set[str]:
        """Return the 'seen' set tracking duplicate overrides for a rule type."""
        if rule_type == "exclusion":
            return self.seen_exclusions
        if rule_type == "complexity_override":
            return self.seen_complexity
        return self.seen_weight