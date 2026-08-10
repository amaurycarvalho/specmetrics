"""Private helpers for collecting and building metric explanations."""

from __future__ import annotations

from typing import Any

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel

from .evidence_tracer import EvidenceTracer
from .models import (
    AppliedRule,
    ElementContribution,
    ExplanationSummary,
    MetricExplanation,
)


def _build_metrics_from_elements(
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
    cfm: CanonicalFunctionalModel | None,
) -> list[MetricExplanation]:
    type_counts: dict[str, int] = {}
    for el in elements:
        t = el["element_type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    metrics: list[MetricExplanation] = [
        MetricExplanation(
            metric_name="function_count",
            metric_value=len(elements),
            computation_summary=f"Total elements identified: {len(elements)}",
            elements=[ElementContribution(**el) for el in elements],
            applied_rules=applied_rules,
        ),
    ]

    for elem_type, count in sorted(type_counts.items()):
        type_elements = [el for el in elements if el["element_type"] == elem_type]
        metrics.append(
            MetricExplanation(
                metric_name=f"{elem_type}_count",
                metric_value=count,
                computation_summary=f"Total {elem_type} elements: {count}",
                elements=[ElementContribution(**el) for el in type_elements],
                applied_rules=applied_rules,
            )
        )

    return metrics


def _build_metrics_from_measurement_result(
    measurement_result: dict[str, Any],
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
) -> list[MetricExplanation]:
    metrics: list[MetricExplanation] = []

    total_fp = (
        measurement_result.get("fpa_total_function_points")
        or measurement_result.get("total_function_points")
        or 0
    )
    if total_fp is not None:
        metrics.append(
            MetricExplanation(
                metric_name="functional_size",
                metric_value=total_fp,
                computation_summary=f"Total function points: {total_fp}",
                elements=[ElementContribution(**el) for el in elements],
                applied_rules=applied_rules,
            )
        )

    breakdown = measurement_result.get("breakdown", {})
    for ft, bd in breakdown.items():
        metrics.append(
            MetricExplanation(
                metric_name=f"{ft}_count",
                metric_value=bd.get("count", 0),
                computation_summary=f"Total {ft} elements: {bd.get('count', 0)} (UFP: {bd.get('total_ufp', 0)})",
                elements=[
                    ElementContribution(**el)
                    for el in elements
                    if el["element_type"] == ft
                ],
                applied_rules=applied_rules,
            )
        )

    complexity_dist = measurement_result.get("complexity_distribution", [])
    for cd in complexity_dist:
        fn_type = cd.get("function_type", "unknown")
        comp = cd.get("complexity", "unknown")
        metrics.append(
            MetricExplanation(
                metric_name=f"{fn_type}_{comp}_count",
                metric_value=cd.get("count", 0),
                computation_summary=f"Total {fn_type} ({comp}): {cd.get('count', 0)}",
                elements=[],
                applied_rules=applied_rules,
            )
        )

    return metrics


def _collect_cfm_elements(
    cfm: CanonicalFunctionalModel | None,
    tracer: EvidenceTracer,
) -> tuple[list[dict[str, Any]], list[AppliedRule]]:
    elements: list[dict[str, Any]] = []
    applied_rules: list[AppliedRule] = []

    if cfm is None:
        return elements, applied_rules

    for category_name in (
        "actors",
        "functional_processes",
        "business_rules",
        "data_groups",
        "operations",
    ):
        category = cfm.get_elements_by_category(category_name)
        for eid, elem in category.items():
            evidence_refs = tracer.trace_element(eid, cfm=cfm)
            elements.append(
                {
                    "element_id": eid,
                    "element_type": category_name,
                    "element_label": getattr(elem, "name", eid),
                    "complexity": None,
                    "weight": None,
                    "evidence": evidence_refs,
                    "applied_rules": [],
                }
            )

    for rid, rule in cfm.business_rules.items():
        applied_rules.append(
            AppliedRule(
                rule_pack_id=str(getattr(cfm, "run_id", rid)),
                rule_id=rid,
                rule_type="business_rule",
                description=rule.description or rule.name,
                effect="Identified as business rule in CFM",
            )
        )

    return elements, applied_rules


def _collect_metrics(
    measurement_result: dict[str, Any] | None,
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
    cfm: CanonicalFunctionalModel | None,
) -> list[MetricExplanation]:
    """Build metric explanations from a measurement result or from elements."""
    if measurement_result:
        return _build_metrics_from_measurement_result(
            measurement_result, elements, applied_rules
        )
    return _build_metrics_from_elements(elements, applied_rules, cfm)


def _filter_metrics(
    metrics: list[MetricExplanation],
    metric_name: str | None,
    run_id: str,
) -> list[MetricExplanation]:
    """Restrict metrics to the requested metric name, if any."""
    if metric_name is None:
        return metrics
    filtered = [m for m in metrics if m.metric_name == metric_name]
    if not filtered:
        raise ValueError(f"Metric '{metric_name}' not found in run {run_id}")
    return filtered


def _resolve_spec_path(run_id: str, cfm: CanonicalFunctionalModel | None) -> str:
    """Resolve a fallback spec path from the CFM metadata."""
    if cfm and cfm.metadata:
        return cfm.metadata.run_id
    return run_id


def _build_summary(
    metrics: list[MetricExplanation],
    elements: list[dict[str, Any]],
    applied_rules: list[AppliedRule],
) -> ExplanationSummary:
    """Build the summary counters for an explanation."""
    return ExplanationSummary(
        total_metrics=len(metrics),
        total_elements=len(elements),
        total_evidence_refs=sum(len(el.evidence) for el in metrics[0].elements)
        if metrics
        else 0,
        total_rules_applied=len(applied_rules),
    )