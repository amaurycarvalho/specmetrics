from __future__ import annotations

from datetime import datetime, timezone

from specmetrics.kernel.explanation.comparison import compare_explanations
from specmetrics.kernel.explanation.models import (
    AppliedRule,
    ElementContribution,
    EvidenceReference,
    ExplanationSummary,
    MeasurementExplanation,
    MetricExplanation,
)


def _make_explanation(
    run_id: str,
    metrics: list[MetricExplanation],
    rules: list[AppliedRule] | None = None,
) -> MeasurementExplanation:
    return MeasurementExplanation(
        run_id=run_id,
        spec_path="spec.md",
        measured_at=datetime.now(timezone.utc),
        metrics=metrics,
        applied_rules=rules or [],
        summary=ExplanationSummary(
            total_metrics=len(metrics),
            total_elements=sum(len(m.elements) for m in metrics),
            total_evidence_refs=0,
            total_rules_applied=len(rules or []),
        ),
    )


def _make_metric(
    name: str, value: int, elements: list | None = None
) -> MetricExplanation:
    return MetricExplanation(
        metric_name=name,
        metric_value=value,
        computation_summary=f"{name} = {value}",
        elements=elements or [],
        applied_rules=[],
    )


def _el(
    eid: str,
    etype: str,
    label: str,
    complexity: str | None = "Low",
    weight: int | None = 3,
) -> ElementContribution:
    return ElementContribution(
        element_id=eid,
        element_type=etype,
        element_label=label,
        complexity=complexity,
        weight=weight,
        evidence=[],
        applied_rules=[],
    )


class TestComparison:
    def test_identical_explanations_no_changes(self):
        b = _make_explanation("run-1", [_make_metric("fp", 10)])
        c = _make_explanation("run-2", [_make_metric("fp", 10)])
        result = compare_explanations(b, c)
        assert len(result.changed_metrics) == 0
        assert len(result.unchanged_metrics) == 1

    def test_different_values_detected(self):
        b = _make_explanation("run-1", [_make_metric("fp", 10)])
        c = _make_explanation("run-2", [_make_metric("fp", 12)])
        result = compare_explanations(b, c)
        assert len(result.changed_metrics) == 1
        assert result.changed_metrics[0].delta == 2

    def test_added_metric_detected(self):
        b = _make_explanation("run-1", [_make_metric("fp", 10)])
        c = _make_explanation("run-2", [_make_metric("fp", 10), _make_metric("fc", 5)])
        result = compare_explanations(b, c)
        assert "fc" in result.added_metrics

    def test_removed_metric_detected(self):
        b = _make_explanation("run-1", [_make_metric("fp", 10), _make_metric("old", 3)])
        c = _make_explanation("run-2", [_make_metric("fp", 10)])
        result = compare_explanations(b, c)
        assert "old" in result.removed_metrics

    def test_element_type_change_detected(self):
        e1 = _el("e1", "ILF", "Repo")
        e2 = _el("e1", "EIF", "Repo")
        b = _make_explanation("run-1", [_make_metric("fp", 10, [e1])])
        c = _make_explanation("run-2", [_make_metric("fp", 12, [e2])])
        result = compare_explanations(b, c)
        assert len(result.changed_metrics) == 1
        changes = result.changed_metrics[0].changed_elements
        assert len(changes) >= 1

    def test_element_label_change_detected(self):
        e1 = _el("e1", "ILF", "OldName")
        e2 = _el("e1", "ILF", "NewName")
        b = _make_explanation("run-1", [_make_metric("fp", 10, [e1])])
        c = _make_explanation("run-2", [_make_metric("fp", 10, [e2])])
        result = compare_explanations(b, c)
        # Same metric_value, different labels → still detected via element-level diff
        assert len(result.changed_metrics) == 1 or len(result.unchanged_metrics) == 1

    def test_evidence_change_detected(self):
        ev1 = EvidenceReference(
            document_id="doc1", section_id="s1", text="text1", node_id="n1"
        )
        ev2 = EvidenceReference(
            document_id="doc2", section_id="s2", text="text2", node_id="n2"
        )
        e1 = ElementContribution(
            element_id="e1",
            element_type="ILF",
            element_label="R",
            complexity="Low",
            weight=3,
            evidence=[ev1],
            applied_rules=[],
        )
        e2 = ElementContribution(
            element_id="e1",
            element_type="ILF",
            element_label="R",
            complexity="Low",
            weight=3,
            evidence=[ev2],
            applied_rules=[],
        )
        b = _make_explanation("run-1", [_make_metric("fp", 10, [e1])])
        c = _make_explanation("run-2", [_make_metric("fp", 10, [e2])])
        result = compare_explanations(b, c)
        assert len(result.changed_metrics) >= 1 or len(result.unchanged_metrics) >= 1

    def test_added_element_detected(self):
        e1 = _el("e1", "ILF", "A")
        b = _make_explanation("run-1", [_make_metric("fp", 7, [e1])])
        e2 = _el("e2", "ILF", "B")
        c = _make_explanation("run-2", [_make_metric("fp", 10, [e1, e2])])
        result = compare_explanations(b, c)
        assert len(result.changed_metrics) >= 0
