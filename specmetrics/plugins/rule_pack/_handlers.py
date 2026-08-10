"""Internal handlers that translate rule pack rules into apply state."""

from __future__ import annotations

from typing import Any

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.cfm.models import Rule, RulePack

from ._state import RuleApplyState
from .annotator import RuleAnnotator

logger = structlog.get_logger(__name__)


def _notify_duplicate_reference(
    event: str,
    pack: RulePack,
    rule: Rule,
    **extra: object,
) -> None:
    logger.warning(event, rule_pack_id=pack.id, rule_id=rule.id, **extra)


def handle_exclusion_rule(
    annotator: RuleAnnotator,
    pack: RulePack,
    rule: Rule,
    state: RuleApplyState,
) -> None:
    """Apply an exclusion rule to the rule apply state."""
    ftypes = rule.config.function_types or []
    seen = state.seen_for(rule.type)
    for ft in ftypes:
        if ft in seen:
            _notify_duplicate_reference(
                "rule_pack_override_exclusion",
                pack,
                rule,
                function_type=ft,
                message=(
                    f"Exclusion for '{ft}' already defined by another pack; "
                    "this pack's rule takes precedence"
                ),
            )
        seen.add(ft)
    state.excluded_types.update(ftypes)
    annotator.record_application(
        rule_pack_id=pack.id,
        rule_id=rule.id,
        rule_type="exclusion",
        description=f"Excluded function types: {', '.join(ftypes)}",
        methodology=pack.methodology,
        after_state={"excluded_types": list(ftypes)},
    )


def handle_element_exclusion_rule(
    annotator: RuleAnnotator,
    pack: RulePack,
    rule: Rule,
    state: RuleApplyState,
) -> None:
    """Apply an element exclusion rule to the rule apply state."""
    eids = rule.config.element_ids or []
    state.excluded_element_ids.update(eids)
    annotator.record_application(
        rule_pack_id=pack.id,
        rule_id=rule.id,
        rule_type="element_exclusion",
        description=f"Excluded element IDs: {', '.join(eids)}",
        methodology=pack.methodology,
        after_state={"excluded_element_ids": list(eids)},
    )


def handle_complexity_override_rule(
    annotator: RuleAnnotator,
    pack: RulePack,
    rule: Rule,
    state: RuleApplyState,
) -> None:
    """Apply a complexity override rule to the rule apply state."""
    ft_key = (rule.config.function_type or "").upper()
    seen = state.seen_for(rule.type)
    if ft_key in seen:
        _notify_duplicate_reference(
            "rule_pack_override_complexity",
            pack,
            rule,
            function_type=rule.config.function_type,
            message=(
                f"Complexity override for '{rule.config.function_type}' already defined "
                "by another pack; this pack's rule takes precedence"
            ),
        )
    seen.add(ft_key)
    override = {
        "pack_id": pack.id,
        "rule_id": rule.id,
        "function_type": rule.config.function_type,
        "thresholds": rule.config.thresholds or {},
    }
    state.complexity_overrides.append(override)
    annotator.record_application(
        rule_pack_id=pack.id,
        rule_id=rule.id,
        rule_type="complexity_override",
        description=(
            f"Complexity thresholds override for {rule.config.function_type}: "
            f"{rule.config.thresholds}"
        ),
        methodology=pack.methodology,
        after_state={
            "function_type": rule.config.function_type,
            "thresholds": rule.config.thresholds or {},
        },
    )


def handle_weight_override_rule(
    annotator: RuleAnnotator,
    pack: RulePack,
    rule: Rule,
    state: RuleApplyState,
) -> None:
    """Apply a weight override rule to the rule apply state."""
    wk = f"{rule.config.function_type or ''}|{rule.config.complexity or ''}"
    seen = state.seen_for(rule.type)
    if wk in seen:
        _notify_duplicate_reference(
            "rule_pack_override_weight",
            pack,
            rule,
            function_type=rule.config.function_type,
            complexity=rule.config.complexity,
            message=(
                f"Weight override for '{rule.config.function_type}/"
                f"{rule.config.complexity}' already defined by another pack; "
                "this pack's rule takes precedence"
            ),
        )
    seen.add(wk)
    override = {
        "pack_id": pack.id,
        "rule_id": rule.id,
        "function_type": rule.config.function_type,
        "complexity": rule.config.complexity,
        "weight": rule.config.weight,
    }
    state.weight_overrides.append(override)
    annotator.record_application(
        rule_pack_id=pack.id,
        rule_id=rule.id,
        rule_type="weight_override",
        description=(
            f"Weight override for {rule.config.function_type}/"
            f"{rule.config.complexity}: {rule.config.weight}"
        ),
        methodology=pack.methodology,
        after_state={
            "function_type": rule.config.function_type,
            "complexity": rule.config.complexity,
            "weight": rule.config.weight,
        },
    )


def handle_vaf_rule(
    annotator: RuleAnnotator,
    pack: RulePack,
    rule: Rule,
    state: RuleApplyState,
) -> None:
    """Apply a VAF rule, computing and storing the value adjustment factor."""
    gsc = rule.config.gsc
    if not gsc:
        return
    total = sum(gsc.values())
    vaf_value = round(0.65 + 0.01 * total, 2)
    state.vaf_value = vaf_value
    annotator.record_application(
        rule_pack_id=pack.id,
        rule_id=rule.id,
        rule_type="vaf",
        description=f"Computed VAF={vaf_value} from GSC (total={total})",
        methodology=pack.methodology,
        after_state={"vaf": vaf_value, "gsc_total": total},
    )


def log_unused_references(
    cfm: CanonicalFunctionalModel,
    packs: list[RulePack],
) -> None:
    """Log rules whose referenced types or elements are unused in the CFM."""
    cfm_types = {
        metadata.get("function_type", "").upper()
        for _pid, process in cfm.functional_processes.items()
        if (metadata := getattr(process, "metadata", None) or {})
    }
    for pack in packs:
        for rule in pack.rules:
            if rule.type == "exclusion":
                log_unused_types(pack, rule, cfm_types)
            elif rule.type == "element_exclusion":
                log_unused_elements(pack, rule, cfm.functional_processes)


def log_unused_types(
    pack: RulePack,
    rule: Rule,
    cfm_types: set[str],
) -> None:
    """Log excluded function types not present in the CFM."""
    for ft in rule.config.function_types or []:
        if ft.upper() not in cfm_types:
            logger.info(
                "rule_pack_unused_type",
                rule_pack_id=pack.id,
                rule_id=rule.id,
                function_type=ft,
                message=f"Rule references function type '{ft}' not present in CFM",
            )


def log_unused_elements(
    pack: RulePack,
    rule: Rule,
    processes: dict[str, Any],
) -> None:
    """Log excluded element IDs not present in the CFM."""
    for eid in rule.config.element_ids or []:
        if eid not in processes:
            logger.info(
                "rule_pack_unused_element",
                rule_pack_id=pack.id,
                rule_id=rule.id,
                element_id=eid,
                message=f"Rule references element ID '{eid}' not present in CFM",
            )