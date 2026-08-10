"""Plain-text output formatter for measurement explanations and comparisons."""

from __future__ import annotations

from typing import Self

from ..models import (
    ElementContribution,
    EvidenceReference,
    ExplanationComparison,
    MeasurementExplanation,
    MetricChange,
    MetricExplanation,
)


class TextFormatter:
    """Format explanations and comparisons as human-readable text."""

    name = "text"

    def format(self: Self, explanation: MeasurementExplanation) -> str:
        """Format a single measurement explanation as text."""
        return format_explanation(explanation)

    def format_comparison(self: Self, comparison: ExplanationComparison) -> str:
        """Format a comparison of two explanations as text."""
        return format_comparison(comparison)


def _format_metric(metric: MetricExplanation, indent: str = "  ") -> str:
    lines: list[str] = []
    lines.append(f"{indent}{metric.metric_name} = {metric.metric_value}")
    if metric.computation_summary:
        lines.append(f"{indent}  Summary: {metric.computation_summary}")
    for el in metric.elements:
        lines.extend(_format_element(el, indent))
    for rule in metric.applied_rules:
        lines.append(f"{indent}  Rule: {rule.rule_id} ({rule.effect})")
    return "\n".join(lines)


def _format_element(element: ElementContribution, indent: str) -> list[str]:
    """Format a single contributing element and its evidence into text lines."""
    lines: list[str] = []
    label = f"{element.element_label} ({element.element_type})"
    if element.complexity:
        label += f" [{element.complexity}]"
    if element.weight is not None:
        label += f" = {element.weight}"
    lines.append(f"{indent}  Element: {label}")
    if not element.evidence:
        lines.append(f"{indent}    ⚠ No evidence reference — orphan element")
    else:
        for ev in element.evidence[:5]:
            lines.append(f"{indent}    {_format_evidence(ev)}")
        if len(element.evidence) > 5:
            lines.append(
                f"{indent}    ... and {len(element.evidence) - 5} more evidence references"
            )
    for rule in element.applied_rules:
        lines.append(f"{indent}    Rule: {rule.rule_id} ({rule.effect})")
    return lines


def _format_evidence(ev: EvidenceReference) -> str:
    """Format a single evidence reference into a one-line string."""
    section = f" in {ev.section_id}" if ev.section_id else ""
    snippet = ev.text[:80] + "..." if len(ev.text) > 80 else ev.text
    conf = f" (confidence: {ev.confidence:.2f})" if ev.confidence is not None else ""
    return f'Evidence{section}{conf}: "{snippet}"'


def format_explanation(explanation: MeasurementExplanation) -> str:
    """Format a measurement explanation as human-readable text."""
    lines: list[str] = [
        f"Measurement Run: {explanation.run_id}",
        f"Spec: {explanation.spec_path}",
        "",
        "Metrics:",
    ]
    for metric in explanation.metrics:
        lines.append(_format_metric(metric))
    lines.append("")
    if explanation.applied_rules:
        lines.append(f"Rules Applied: {len(explanation.applied_rules)}")
        for rule in explanation.applied_rules:
            lines.append(f"  {rule.rule_id} ({rule.description})")
    lines.append("")
    s = explanation.summary
    lines.append(
        f"Summary: {s.total_metrics} metrics, {s.total_elements} elements, "
        f"{s.total_evidence_refs} evidence refs, {s.total_rules_applied} rules"
    )
    return "\n".join(lines)


def _format_metric_change(change: MetricChange, indent: str = "  ") -> str:
    lines: list[str] = [
        f"{indent}{change.metric_name}: {change.baseline_value} \u2192 {change.comparison_value} (\u0394 {change.delta:+})"
    ]
    for ec in change.changed_elements:
        lines.append(f"{indent}  Element {ec.element_id}: {ec.change_type}")
    return "\n".join(lines)


def format_comparison(comparison: ExplanationComparison) -> str:
    """Format an explanation comparison as human-readable text."""
    lines: list[str] = [
        f"Comparison: {comparison.baseline_run_id} \u2192 {comparison.comparison_run_id}",
        "",
    ]
    if comparison.summary:
        lines.append(comparison.summary)
        lines.append("")
    if comparison.changed_metrics:
        lines.append("Changed Metrics:")
        for change in comparison.changed_metrics:
            lines.append(_format_metric_change(change))
        lines.append("")
    if comparison.added_metrics:
        lines.append(f"Added Metrics: {', '.join(comparison.added_metrics)}")
    if comparison.removed_metrics:
        lines.append(f"Removed Metrics: {', '.join(comparison.removed_metrics)}")
    if comparison.unchanged_metrics:
        lines.append(f"Unchanged Metrics: {', '.join(comparison.unchanged_metrics)}")
    return "\n".join(lines)
