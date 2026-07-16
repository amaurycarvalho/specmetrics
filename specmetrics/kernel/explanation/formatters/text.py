from __future__ import annotations

from ..models import (
    ExplanationComparison,
    MeasurementExplanation,
    MetricChange,
    MetricExplanation,
)


class TextFormatter:
    name = "text"

    def format(self, explanation: MeasurementExplanation) -> str:
        return format_explanation(explanation)

    def format_comparison(self, comparison: ExplanationComparison) -> str:
        return format_comparison(comparison)


def _format_metric(metric: MetricExplanation, indent: str = "  ") -> str:
    lines: list[str] = []
    lines.append(f"{indent}{metric.metric_name} = {metric.metric_value}")
    if metric.computation_summary:
        lines.append(f"{indent}  Summary: {metric.computation_summary}")
    for el in metric.elements:
        label = f"{el.element_label} ({el.element_type})"
        if el.complexity:
            label += f" [{el.complexity}]"
        if el.weight is not None:
            label += f" = {el.weight}"
        lines.append(f"{indent}  Element: {label}")
        if not el.evidence:
            lines.append(f"{indent}    ⚠ No evidence reference — orphan element")
        else:
            for ev in el.evidence[:5]:
                section = f" in {ev.section_id}" if ev.section_id else ""
                snippet = ev.text[:80] + "..." if len(ev.text) > 80 else ev.text
                conf = f" (confidence: {ev.confidence:.2f})" if ev.confidence is not None else ""
                lines.append(f"{indent}    Evidence{section}{conf}: \"{snippet}\"")
            if len(el.evidence) > 5:
                lines.append(f"{indent}    ... and {len(el.evidence) - 5} more evidence references")
        for rule in el.applied_rules:
            lines.append(f"{indent}    Rule: {rule.rule_id} ({rule.effect})")
    for rule in metric.applied_rules:
        lines.append(f"{indent}  Rule: {rule.rule_id} ({rule.effect})")
    return "\n".join(lines)


def format_explanation(explanation: MeasurementExplanation) -> str:
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
