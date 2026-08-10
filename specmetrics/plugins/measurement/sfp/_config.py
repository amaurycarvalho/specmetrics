"""Configuration helpers for the SFP counter."""
from __future__ import annotations

import dataclasses

from .models import ComponentType

DEFAULT_FP_CONTRIBUTION = 4.6
DEFAULT_LF_CONTRIBUTION = 7.1


@dataclasses.dataclass(frozen=True)
class _ComponentSpec:
    excluded_name: str
    contribution: float
    node_types: set[str]
    element_type_name: str
    component_type: str


@dataclasses.dataclass(frozen=True)
class _CountConfig:
    excluded_types: set[str] = dataclasses.field(default_factory=set)
    fp_contribution: float = DEFAULT_FP_CONTRIBUTION
    lf_contribution: float = DEFAULT_LF_CONTRIBUTION
    fp_node_types: set[str] = dataclasses.field(default_factory=set)
    lf_node_types: set[str] = dataclasses.field(default_factory=set)
    excluded_ids: set[str] = dataclasses.field(default_factory=set)
    excluded_patterns: list[str] = dataclasses.field(default_factory=list)
    included_ids: set[str] = dataclasses.field(default_factory=set)
    included_patterns: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_params(
        cls: type[_CountConfig],
        excluded_types: list[str] | None,
        contribution_overrides: dict[ComponentType, float] | None,
        inclusion_criteria: dict[str, dict[str, list[str]]] | None,
        element_exclusions: dict[str, list[str]] | None,
        element_inclusions: dict[str, list[str]] | None,
    ) -> _CountConfig:
        overrides = contribution_overrides or {}
        exclusions = element_exclusions or {}
        inclusions = element_inclusions or {}

        fp_criteria = (inclusion_criteria or {}).get("functional_process", {})
        lf_criteria = (inclusion_criteria or {}).get("logical_function", {})

        return cls(
            excluded_types=set(excluded_types or []),
            fp_contribution=overrides.get("functional_process", DEFAULT_FP_CONTRIBUTION),
            lf_contribution=overrides.get("logical_function", DEFAULT_LF_CONTRIBUTION),
            fp_node_types=set(fp_criteria.get("node_types", []) or []),
            lf_node_types=set(lf_criteria.get("node_types", []) or []),
            excluded_ids=set(exclusions.get("by_id", [])),
            excluded_patterns=exclusions.get("by_pattern", []),
            included_ids=set(inclusions.get("by_id", [])),
            included_patterns=inclusions.get("by_pattern", []),
        )