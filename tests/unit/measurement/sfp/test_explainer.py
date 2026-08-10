from __future__ import annotations

from specmetrics.plugins.measurement.sfp.explainer import MeasurementExplainer
from specmetrics.plugins.measurement.sfp.models import (
    EvidenceRef,
    MeasuredComponent,
    MeasurementSummary,
    SFPMeasurementResult,
)


def _make_component(
    cid: str = "cmp-1",
    element_id: str = "op-001",
    component_type: str = "functional_process",
    rule_applied: str | None = None,
    section_id: str | None = "s1",
) -> MeasuredComponent:
    return MeasuredComponent(
        id=cid,
        name="comp",
        component_type=component_type,
        contribution=4.6,
        cfm_element_id=element_id,
        cfm_element_type="Operation",
        evidence_refs=[
            EvidenceRef(
                graph_node_id="gn-001",
                document_id="doc-001",
                section_id=section_id,
                text="some text",
            )
        ],
        rule_applied=rule_applied,
    )


def _make_result(components: list[MeasuredComponent]) -> SFPMeasurementResult:
    return SFPMeasurementResult(
        run_id="r",
        cfm_run_id="x",
        measured_components=components,
        summary=MeasurementSummary(
            total_component_count=len(components),
            total_sfp=sum(c.contribution for c in components),
        ),
    )


class TestBuildExplanations:
    def test_builds_one_explanation_per_component(self):
        explainer = MeasurementExplainer()
        result = _make_result([_make_component(), _make_component("cmp-2")])
        explanations = explainer.build_explanations(result)
        assert len(explanations) == 2

    def test_explains_rule_applied(self):
        explainer = MeasurementExplainer()
        component = _make_component(rule_applied="excluded_by_id")
        result = _make_result([component])
        exp = explainer.build_explanations(result)[0]
        assert exp.rule_exceptions == ["excluded_by_id"]
        assert "Rule Pack override" in exp.contribution_reason

    def test_explains_no_rule(self):
        explainer = MeasurementExplainer()
        result = _make_result([_make_component()])
        exp = explainer.build_explanations(result)[0]
        assert exp.rule_exceptions == []


class TestIdentificationReason:
    def test_functional_process_reason(self):
        explainer = MeasurementExplainer()
        component = _make_component(component_type="functional_process")
        reason = explainer._build_identification_reason(component)
        assert "Functional Process" in reason
        assert "Logical Function" not in reason

    def test_logical_function_reason(self):
        explainer = MeasurementExplainer()
        component = _make_component(
            cid="cmp-lg",
            element_id="dg-001",
            component_type="logical_function",
        )
        reason = explainer._build_identification_reason(component)
        assert "Logical Function" in reason
        assert "Functional Process" not in reason


class TestEvidenceChain:
    def test_evidence_chain_includes_section(self):
        explainer = MeasurementExplainer()
        component = _make_component(section_id="s1")
        chain = explainer._build_evidence_chain(component)
        assert "(section s1)" in chain[0]
        assert "XXXX" not in chain[0]

    def test_evidence_chain_fallback_when_no_refs(self):
        explainer = MeasurementExplainer()
        component = MeasuredComponent(
            id="cmp-1",
            name="comp",
            component_type="functional_process",
            contribution=4.6,
            cfm_element_id="op-001",
            cfm_element_type="Operation",
            evidence_refs=[],
        )
        chain = explainer._build_evidence_chain(component)
        assert len(chain) == 1
        assert "no evidence graph refs" in chain[0]
        assert all(isinstance(c, str) for c in chain)

class TestExplainComponent:
    def test_rule_exceptions_propagated(self):
        """Kills MeasurementExplainer::_explain_component__mutmut_21 (rule_exceptions arg deleted)."""
        explainer = MeasurementExplainer()
        component = _make_component(rule_applied="excluded_by_id")
        result = _make_result([component])
        exp = explainer._explain_component(component, result)
        assert exp.rule_exceptions == ["excluded_by_id"]

    def test_rule_exceptions_empty_when_no_rule(self):
        """Kills MeasurementExplainer::_explain_component__mutmut_21 (deleted default empty list)."""
        explainer = MeasurementExplainer()
        component = _make_component()
        result = _make_result([component])
        exp = explainer._explain_component(component, result)
        assert exp.rule_exceptions == []
