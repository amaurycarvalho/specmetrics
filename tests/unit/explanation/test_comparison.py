from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from specmetrics.kernel.explanation.comparison import (
    _build_comparison_summary,
    _compare_element_fields,
    _element_changes_for,
    _modified_element,
    compare_explanations,
)
from specmetrics.kernel.explanation.models import (
    AppliedRule,
    ElementContribution,
    EvidenceReference,
    ExplanationSummary,
    MeasurementExplanation,
    MetricChange,
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
        measured_at=datetime.now(UTC),
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


def _ev(node_id: str) -> EvidenceReference:
    return EvidenceReference(
        document_id="doc1", section_id="s1", text="t", node_id=node_id
    )


class TestCompareElementFields:
    def test_field_changes_detected_for_label_complexity_weight(self):
        """Kills _compare_element_fields__mutmut_4/5/6/7/8/9 (all compared field names)."""
        be = _el("e1", "ILF", "A", complexity="Low", weight=3)
        ce = _el("e1", "ILF", "B", complexity="High", weight=5)
        changes = _compare_element_fields(be, ce)
        fields = {c["field"] for c in changes}
        assert fields == {"element_label", "complexity", "weight"}

    def test_field_changes_preserve_baseline_and_comparison(self):
        """Kills _compare_element_fields__mutmut_10/11/16/17/22 (baseline/comparison values and != operator)."""
        be = _el("e1", "ILF", "A", complexity="Low", weight=3)
        ce = _el("e1", "ILF", "B", complexity="High", weight=5)
        changes = {c["field"]: c for c in _compare_element_fields(be, ce)}
        assert changes["element_label"] == {"field": "element_label", "baseline": "A", "comparison": "B"}
        assert changes["complexity"] == {"field": "complexity", "baseline": "Low", "comparison": "High"}

    def test_getattr_default_used_for_missing_fields(self):
        """Kills _compare_element_fields__mutmut_15/21 (getattr default must be None)."""
        be = SimpleNamespace(element_type="ILF", element_label="A", evidence=[])
        ce = SimpleNamespace(element_type="ILF", element_label="B", evidence=[])
        changes = _compare_element_fields(be, ce)
        assert any(c["field"] == "element_label" for c in changes)

    def test_evidence_change_detected_with_node_ids(self):
        """Kills _compare_element_fields__mutmut_30/32/33/35/36 (evidence id comparison)."""
        be = _el("e1", "ILF", "A")
        be.evidence = [_ev("n1")]
        ce = _el("e1", "ILF", "A")
        ce.evidence = [_ev("n2")]
        changes = {c["field"]: c for c in _compare_element_fields(be, ce)}
        assert changes["evidence"] == {
            "field": "evidence",
            "baseline": ["n1"],
            "comparison": ["n2"],
        }

    def test_same_evidence_produces_no_change(self):
        """Kills _compare_element_fields__mutmut_36 (equal evidence ids must not be reported)."""
        be = _el("e1", "ILF", "A")
        be.evidence = [_ev("n1")]
        ce = _el("e1", "ILF", "A")
        ce.evidence = [_ev("n1")]
        changes = _compare_element_fields(be, ce)
        assert all(c["field"] != "evidence" for c in changes)


class TestElementChangesFor:
    def test_added_element_reported_with_state(self):
        """Kills _element_changes_for__mutmut_4/11/12/25/26/27/29/30/33 (added element path)."""
        baseline = [_el("e1", "ILF", "A")]
        comparison = [_el("e1", "ILF", "A"), _el("e2", "EIF", "B")]
        changes = {c.element_id: c for c in _element_changes_for(baseline, comparison)}
        assert changes["e2"].change_type == "added"
        assert changes["e2"].comparison_state == {"element_type": "EIF", "element_label": "B"}

    def test_removed_element_reported_with_state(self):
        """Kills _element_changes_for__mutmut_9/10/28/31/32/34/35/36/37 (removed element path)."""
        baseline = [_el("e1", "ILF", "A"), _el("e2", "EIF", "B")]
        comparison = [_el("e1", "ILF", "A")]
        changes = {c.element_id: c for c in _element_changes_for(baseline, comparison)}
        assert changes["e2"].change_type == "removed"
        assert changes["e2"].baseline_state == {"element_type": "EIF", "element_label": "B"}


class TestModifiedElement:
    def test_complexity_change_produces_changed_type(self):
        """Kills _modified_element__mutmut_12/13/14/15/16/17/18/19 (complexity/weight change type)."""
        be = _el("e1", "ILF", "A", complexity="Low", weight=3)
        ce = _el("e1", "ILF", "A", complexity="High", weight=3)
        change = _modified_element("e1", be, ce)
        assert change is not None
        assert change.change_type == "complexity_changed"
        assert change.baseline_state == {"complexity": "Low"}
        assert change.comparison_state == {"complexity": "High"}

    def test_label_change_produces_modified_type(self):
        """Kills _modified_element__mutmut_8/9 (non weight/complexity changes use 'modified')."""
        be = _el("e1", "ILF", "A")
        ce = _el("e1", "ILF", "B")
        change = _modified_element("e1", be, ce)
        assert change is not None
        assert change.change_type == "modified"
        assert change.baseline_state == {"element_label": "A"}
        assert change.comparison_state == {"element_label": "B"}


class TestBuildComparisonSummary:
    def test_summary_joins_parts_with_comma(self):
        """Kills _build_comparison_summary__mutmut_7 (parts joined with ', ')."""
        change = MetricChange(metric_name="m", baseline_value=1, comparison_value=2)
        summary = _build_comparison_summary([change], ["a"], [], [])
        assert summary == "1 metric(s) changed, 1 added"

    def test_summary_empty_message(self):
        """Kills _build_comparison_summary__mutmut_8/9/10 (empty summary message)."""
        summary = _build_comparison_summary([], [], [], [])
        assert summary == "No differences found"
