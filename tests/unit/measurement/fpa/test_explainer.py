
from specmetrics.plugins.measurement.fpa.explainer import MeasurementExplainer
from specmetrics.plugins.measurement.fpa.models import (
    EvidenceRef,
    FPAMeasurementResult,
    MeasuredFunction,
    MeasurementSummary,
)


def _evidence(
    doc_id: str = "doc-1", section_id: str | None = "sec-1"
) -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="g-1",
        document_id=doc_id,
        section_id=section_id,
        text="evidence text",
    )


def _fn(
    fn_id: str,
    function_type: str,
    det: int = 5,
    ret: int | None = None,
    ftr: int | None = None,
    rule_applied: str | None = None,
    name: str | None = None,
) -> MeasuredFunction:
    return MeasuredFunction(
        id=fn_id,
        name=name or f"fn-{fn_id}",
        function_type=function_type,  # type: ignore[arg-type]
        complexity="Low",  # type: ignore[arg-type]
        det_count=det,
        ret_count=ret,
        ftr_count=ftr,
        ufp_weight=4,
        cfm_element_id=f"cfm-{fn_id}",
        cfm_element_type="DataGroup",
        evidence_refs=[_evidence()],
        rule_applied=rule_applied,
    )


def _result(functions: list[MeasuredFunction]) -> FPAMeasurementResult:

    return FPAMeasurementResult(
        run_id="run-1",
        cfm_run_id="cfm-1",
        measured_functions=functions,
        summary=MeasurementSummary(
            total_function_count=len(functions), total_ufp=0
        ),
    )


class TestBuildExplanations:
    def test_empty_result_returns_no_explanations(self) -> None:
        result = _result([])
        assert MeasurementExplainer().build_explanations(result) == []

    def test_builds_one_per_function(self) -> None:
        result = _result([_fn("f1", "ILF", ret=2), _fn("f2", "EI", ftr=3)])
        exps = MeasurementExplainer().build_explanations(result)
        assert len(exps) == 2
        assert {e.function_id for e in exps} == {"f1", "f2"}


class TestClassificationReason:
    def test_ilf_source_data_group(self) -> None:
        fn = _fn("f1", "ILF", ret=2)
        reason = MeasurementExplainer()._build_classification_reason(fn)
        assert "DataGroup" in reason
        assert "internal/shared" in reason
        assert "ILF" in reason

    def test_eif_source_data_group(self) -> None:
        fn = _fn("f1", "EIF", ret=1)
        reason = MeasurementExplainer()._build_classification_reason(fn)
        assert "DataGroup" in reason
        assert "external" in reason
        assert "EIF" in reason

    def test_transactional_source_operation(self) -> None:
        for ft, direction in [("EI", "input"), ("EO", "output"), ("EQ", "query")]:
            fn = _fn("f1", ft, ftr=2)
            reason = MeasurementExplainer()._build_classification_reason(fn)
            assert "Operation" in reason
            assert direction in reason
            assert ft in reason


class TestComplexityReason:
    def test_data_function_uses_ret(self) -> None:
        fn = _fn("f1", "ILF", det=10, ret=3)
        reason = MeasurementExplainer()._build_complexity_reason(fn)
        assert "10 DETs" in reason
        assert "3 RETs" in reason
        assert "per IFPUG data function matrix" in reason

    def test_transactional_uses_ftr(self) -> None:
        fn = _fn("f1", "EI", det=10, ftr=4)
        reason = MeasurementExplainer()._build_complexity_reason(fn)
        assert "10 DETs" in reason
        assert "4 FTRs" in reason
        assert "per IFPUG EI matrix" in reason


class TestEvidenceChain:
    def test_with_evidence_section(self) -> None:
        fn = _fn("f1", "ILF", ret=2)
        fn = fn.model_copy(update={"evidence_refs": [_evidence("doc-7", "sec-7")]})
        chain = MeasurementExplainer()._build_evidence_chain(fn)
        assert len(chain) == 1
        assert "(section sec-7)" in chain[0]
        assert "'doc-7'" in chain[0]
        assert "graph node 'g-1'" in chain[0]

    def test_without_section_omits_section(self) -> None:
        fn = _fn("f1", "ILF", ret=2)
        fn = fn.model_copy(update={"evidence_refs": [_evidence("doc-7", None)]})
        chain = MeasurementExplainer()._build_evidence_chain(fn)
        assert "(section" not in chain[0]

    def test_no_evidence_falls_back(self) -> None:
        fn = _fn("f1", "ILF", ret=2)
        fn = fn.model_copy(update={"evidence_refs": []})
        chain = MeasurementExplainer()._build_evidence_chain(fn)
        assert len(chain) == 1
        assert "no evidence graph refs" in chain[0]


class TestRuleExceptions:
    def test_matching_rule_applied_captured(self) -> None:
        fn = _fn("f1", "ILF", ret=2, rule_applied="weight_override")
        result = _result([fn])
        exp = MeasurementExplainer().build_explanations(result)[0]
        assert exp.rule_exceptions == ["weight_override"]

    def test_no_rule_applied_yields_empty(self) -> None:
        fn = _fn("f1", "ILF", ret=2)
        result = _result([fn])
        exp = MeasurementExplainer().build_explanations(result)[0]
        assert exp.rule_exceptions == []

    def test_rule_exceptions_only_from_same_function(self) -> None:
        """Mutmut 8: exceptions must come only from the same function with a rule."""
        fn = _fn("f1", "ILF", ret=2)
        other = _fn("f2", "EI", ftr=3, rule_applied="weight_override")
        result = _result([fn, other])
        exp = MeasurementExplainer().build_explanations(result)[0]
        assert exp.rule_exceptions == []