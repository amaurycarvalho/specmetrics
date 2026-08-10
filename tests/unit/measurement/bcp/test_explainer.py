from __future__ import annotations

from specmetrics.plugins.measurement.bcp.explainer import (
    build_explanation,
    component_breakdown_summary,
    evidence_assembly,
    top_contributors,
)
from specmetrics.plugins.measurement.bcp.models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
    MeasurementEvidence,
)


def _item(
    element_id: str,
    score: float,
    breakdown: dict[str, float] | None = None,
    evidence: list[MeasurementEvidence] | None = None,
) -> BCPWorkItem:
    return BCPWorkItem(
        element_id=element_id,
        element_name=f"Process {element_id}",
        generated_story="story",
        bcp_score=score,
        component_breakdown=breakdown or {},
        evidence_refs=evidence or [],
        status="success",
    )


def _result(items: list[BCPWorkItem]) -> BCPMeasurementResult:
    return BCPMeasurementResult(
        run_id="run-1",
        items=items,
        total_bcp=sum(i.bcp_score for i in items),
        execution_metadata=ExecutionMetadata(),
    )


class TestBuildExplanation:
    def test_returns_empty_for_empty_result(self) -> None:
        assert build_explanation(_result([])) == []

    def test_ranks_by_bcp_score_descending(self) -> None:
        low = _item("low", 5.0)
        high = _item("high", 20.0)
        mid = _item("mid", 10.0)
        result = _result([low, high, mid])
        ranked = build_explanation(result)
        assert [i.element_id for i in ranked] == ["high", "mid", "low"]

    def test_stable_for_equal_scores(self) -> None:
        a = _item("a", 5.0)
        b = _item("b", 5.0)
        ranked = build_explanation(_result([a, b]))
        assert [i.element_id for i in ranked] == ["a", "b"]


class TestTopContributors:
    def test_limits_to_top_n(self) -> None:
        items = [_item(f"i{i}", float(i)) for i in range(15)]
        top = top_contributors(_result(items), top_n=3)
        assert len(top) == 3
        assert top[0].element_id == "i14"

    def test_returns_all_when_fewer_than_top_n(self) -> None:
        top = top_contributors(_result([_item("a", 1.0)]), top_n=10)
        assert len(top) == 1

    def test_default_top_n_is_ten(self) -> None:
        items = [_item(f"i{i}", float(i)) for i in range(20)]
        top = top_contributors(_result(items))
        assert len(top) == 10
        assert top[0].element_id == "i19"


class TestEvidenceAssembly:
    def test_flattens_evidence_refs(self) -> None:
        ev = MeasurementEvidence(
            element_id="fp-1",
            document_id="doc-1",
            section_id="sec-1",
            text="evidence text",
        )
        item = _item("fp-1", 5.0, evidence=[ev])
        assembled = evidence_assembly(item)
        assert assembled == [
            {
                "element_id": "fp-1",
                "document_id": "doc-1",
                "section_id": "sec-1",
                "text": "evidence text",
            }
        ]

    def test_empty_evidence_returns_empty_list(self) -> None:
        assert evidence_assembly(_item("fp-1", 5.0)) == []


class TestComponentBreakdownSummary:
    def test_aggregates_across_items(self) -> None:
        a = _item("a", 5.0, breakdown={"complexity": 3.0, "effort": 2.0})
        b = _item("b", 5.0, breakdown={"complexity": 1.0})
        summary = component_breakdown_summary(_result([a, b]))
        assert summary == {"complexity": 4.0, "effort": 2.0}

    def test_empty_result_returns_empty_dict(self) -> None:
        assert component_breakdown_summary(_result([])) == {}