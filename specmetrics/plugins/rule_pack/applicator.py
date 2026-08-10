"""Apply rule pack rules to a canonical functional model."""

from __future__ import annotations

from collections.abc import Callable
from typing import Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.cfm.models import AppliedRuleRecord, Rule, RulePack

from ._handlers import (
    handle_complexity_override_rule,
    handle_element_exclusion_rule,
    handle_exclusion_rule,
    handle_vaf_rule,
    handle_weight_override_rule,
    log_unused_references,
)
from ._overrides import (
    apply_complexity_overrides,
    apply_weight_overrides,
    mark_exclusions,
    set_vaf,
)
from ._state import RuleApplyState
from .annotator import RuleAnnotator

logger = structlog.get_logger(__name__)

GSC_KEYS: list[str] = [
    "data_communications",
    "distributed_data_processing",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change",
]


class RuleApplicator:
    """Applies rule pack rules to a canonical functional model."""

    def __init__(self: Self) -> None:
        """Initialize the applicator with a rule annotator."""
        self._annotator = RuleAnnotator()

    @property
    def applied_records(self: Self) -> list[AppliedRuleRecord]:
        """Return the applied rule records."""
        return self._annotator.records

    def apply(
        self: Self,
        cfm: CanonicalFunctionalModel,
        packs: list[RulePack],
    ) -> CanonicalFunctionalModel:
        """Apply the given rule packs to the CFM and return the updated model."""
        self._annotator.clear()
        result = cfm

        state = self._collect_state(packs)

        log_unused_references(cfm, packs)

        if state.excluded_types or state.excluded_element_ids:
            result = mark_exclusions(
                result, state.excluded_types, state.excluded_element_ids
            )

        if state.complexity_overrides:
            result = apply_complexity_overrides(result, state.complexity_overrides)

        if state.weight_overrides:
            result = apply_weight_overrides(result, state.weight_overrides)

        if state.vaf_value is not None:
            result = set_vaf(result, state.vaf_value)

        result = self._annotator.annotate_cfm(
            result, glossary_overrides=state.glossary or None
        )

        logger.info(
            "rule_applicator_applied",
            excluded_types=sorted(state.excluded_types),
            excluded_elements=sorted(state.excluded_element_ids),
            complexity_overrides=len(state.complexity_overrides),
            weight_overrides=len(state.weight_overrides),
            vaf=state.vaf_value,
            applied_record_count=len(self._annotator.records),
        )

        return result

    def _collect_state(self: Self, packs: list[RulePack]) -> RuleApplyState:
        state = RuleApplyState()

        handlers: dict[str, Callable[[RuleAnnotator, RulePack, Rule, RuleApplyState], None]] = {
            "exclusion": handle_exclusion_rule,
            "element_exclusion": handle_element_exclusion_rule,
            "complexity_override": handle_complexity_override_rule,
            "weight_override": handle_weight_override_rule,
            "vaf": handle_vaf_rule,
        }

        for pack in packs:
            state.glossary.update(pack.glossary_overrides)
            for rule in pack.rules:
                handler = handlers.get(rule.type)
                if handler:
                    handler(self._annotator, pack, rule, state)
        return state