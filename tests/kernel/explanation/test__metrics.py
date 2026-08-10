from __future__ import annotations

from types import SimpleNamespace

from specmetrics.kernel.cfm.model import (
    Actor,
    BuildMetadata,
    BusinessRule,
    CanonicalFunctionalModel,
    EvidenceRef,
)
from specmetrics.kernel.explanation._metrics import (
    _build_metrics_from_elements,
    _build_metrics_from_measurement_result,
    _build_summary,
    _collect_cfm_elements,
    _collect_metrics,
)
from specmetrics.kernel.explanation.models import AppliedRule, MetricExplanation


def _el(eid: str, etype: str = "ILF") -> dict:
    return {
        "element_id": eid,
        "element_type": etype,
        "element_label": eid,
        "complexity": None,
        "weight": None,
        "evidence": [],
        "applied_rules": [],
    }


def _make_cfm(run_id: str = "run-1") -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id=run_id,
        actors={
            "a1": Actor(
                id="a1",
                name="User",
                evidence=EvidenceRef(graph_node_id="n1", document_id="d1", text="t"),
            ),
        },
        functional_processes={},
        business_rules={
            "br1": BusinessRule(
                id="br1",
                name="BR1",
                description="desc",
                evidence=EvidenceRef(graph_node_id="n1", document_id="d1", text="t"),
            ),
        },
        data_groups={},
        relationships=[],
        operations={},
        unclassified={},
        metadata=BuildMetadata(
            run_id=run_id,
            build_duration_ms=0,
            element_counts={},
            total_input_nodes=0,
            unclassified_count=0,
        ),
    )


class _SpyTracer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def trace_element(self, eid, cfm=None):
        self.calls.append((eid, cfm))
        return []


class _NoNameCfm:
    """Stub CFM whose elements lack a ``name`` attribute."""

    def __init__(self) -> None:
        self.business_rules: dict = {}

    def get_elements_by_category(self, category: str) -> dict:
        if category == "actors":
            return {"x1": SimpleNamespace()}
        return {}


class _NoRunIdCfm:
    """Stub CFM without a ``run_id`` attribute."""

    def __init__(self) -> None:
        self.business_rules = {"br1": SimpleNamespace(description="", name="BR1")}

    def get_elements_by_category(self, category: str) -> dict:
        return {}


def test_metrics_counts_elements_by_type():
    """Kills _build_metrics_from_elements__mutmut_6/7 (type counts must accumulate)."""
    metrics = _build_metrics_from_elements([_el("a"), _el("b")], [], None)
    by_name = {m.metric_name: m for m in metrics}
    assert by_name["function_count"].metric_value == 2
    assert by_name["ILF_count"].metric_value == 2


def test_metrics_single_type_counts_once():
    """Kills _build_metrics_from_elements__mutmut_11/12 (single element count must be one)."""
    metrics = _build_metrics_from_elements([_el("a")], [], None)
    by_name = {m.metric_name: m for m in metrics}
    assert by_name["ILF_count"].metric_value == 1


def test_metrics_function_count_summary():
    """Kills _build_metrics_from_elements__mutmut_21 (function_count computation summary)."""
    metrics = _build_metrics_from_elements([_el("a"), _el("b")], [], None)
    assert metrics[0].computation_summary == "Total elements identified: 2"


def test_metrics_includes_all_elements():
    """Kills _build_metrics_from_elements__mutmut_22 (all elements included in function_count)."""
    metrics = _build_metrics_from_elements([_el("a"), _el("b")], [], None)
    assert [e.element_id for e in metrics[0].elements] == ["a", "b"]


def test_metrics_forwards_applied_rules():
    """Kills _build_metrics_from_elements__mutmut_23 (applied_rules forwarded to metrics)."""
    rules = [AppliedRule(rule_pack_id="p", rule_id="r", rule_type="fact")]
    metrics = _build_metrics_from_elements([_el("a")], rules, None)
    assert metrics[0].applied_rules == rules


def test_metrics_per_type_filters_elements():
    """Kills _build_metrics_from_elements__mutmut_30/39/40 (per-type metrics filter and summarize)."""
    elements = [_el("a", "ILF"), _el("b", "EIF")]
    metrics = _build_metrics_from_elements(elements, [], None)
    by_name = {m.metric_name: m for m in metrics}
    assert [e.element_id for e in by_name["ILF_count"].elements] == ["a"]
    assert by_name["ILF_count"].computation_summary == "Total ILF elements: 1"
    assert [e.element_id for e in by_name["EIF_count"].elements] == ["b"]
    assert by_name["EIF_count"].computation_summary == "Total EIF elements: 1"


def test_measurement_result_reads_fpa_key():
    """Kills _build_metrics_from_measurement_result__mutmut_5/6/7 (fpa_total_function_points key)."""
    result = {"fpa_total_function_points": 10}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    assert metrics[0].metric_name == "functional_size"
    assert metrics[0].metric_value == 10
    assert metrics[0].computation_summary == "Total function points: 10"


def test_measurement_result_missing_breakdown_is_empty():
    """Kills _build_metrics_from_measurement_result__mutmut_30 (missing breakdown defaults to empty mapping)."""
    result = {"total_function_points": 5}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    assert metrics[0].metric_name == "functional_size"


def test_measurement_result_breakdown_count_present():
    """Kills _build_metrics_from_measurement_result__mutmut_44/48/49 (breakdown count read by key)."""
    result = {"breakdown": {"ILF": {"count": 3, "total_ufp": 6}}}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    ilf = next(m for m in metrics if m.metric_name == "ILF_count")
    assert ilf.metric_value == 3


def test_measurement_result_breakdown_count_missing():
    """Kills _build_metrics_from_measurement_result__mutmut_45/47/50 (missing breakdown count defaults to zero)."""
    result = {"breakdown": {"ILF": {"other": 1}}}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    ilf = next(m for m in metrics if m.metric_name == "ILF_count")
    assert ilf.metric_value == 0


def test_measurement_result_breakdown_summary_exact():
    """Kills _build_metrics_from_measurement_result__mutmut_41/51/53/55/56/58/60/62/63 (breakdown summary string)."""
    result = {"breakdown": {"ILF": {"count": 3, "total_ufp": 6}}}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    ilf = next(m for m in metrics if m.metric_name == "ILF_count")
    assert ilf.computation_summary == "Total ILF elements: 3 (UFP: 6)"


def test_measurement_result_breakdown_summary_missing_keys():
    """Kills _build_metrics_from_measurement_result__mutmut_52/54/57/59/61/64 (breakdown summary default values)."""
    result = {"breakdown": {"ILF": {}}}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    ilf = next(m for m in metrics if m.metric_name == "ILF_count")
    assert ilf.computation_summary == "Total ILF elements: 0 (UFP: 0)"


def test_measurement_result_breakdown_filters_elements():
    """Kills _build_metrics_from_measurement_result__mutmut_42/67 (breakdown metrics filter elements by type)."""
    elements = [_el("a", "ILF"), _el("b", "EIF")]
    result = {"breakdown": {"ILF": {"count": 1}}}
    metrics = _build_metrics_from_measurement_result(result, elements, [])
    ilf = next(m for m in metrics if m.metric_name == "ILF_count")
    assert [e.element_id for e in ilf.elements] == ["a"]


def test_measurement_result_complexity_distribution_missing():
    """Kills _build_metrics_from_measurement_result__mutmut_70/72 (missing complexity distribution defaults to empty)."""
    result = {"breakdown": {}}
    metrics = _build_metrics_from_measurement_result(result, [], [])
    assert all(not m.metric_name.endswith("_count") or m.metric_name == "ILF_count" for m in metrics)


def test_measurement_result_complexity_defaults():
    """Kills _build_metrics_from_measurement_result__mutmut_77/79/82/83/86/88/91/92 (complexity defaults)."""
    result = {
        "breakdown": {},
        "complexity_distribution": [{"count": 2}],
    }
    metrics = _build_metrics_from_measurement_result(result, [], [])
    cd_metric = next(m for m in metrics if m.metric_name == "unknown_unknown_count")
    assert cd_metric.metric_value == 2
    assert cd_metric.computation_summary == "Total unknown (unknown): 2"


def test_measurement_result_complexity_count_present():
    """Kills _build_metrics_from_measurement_result__mutmut_104/108/109 (complexity count read by key)."""
    result = {
        "breakdown": {},
        "complexity_distribution": [{"function_type": "ILF", "complexity": "Low", "count": 2}],
    }
    metrics = _build_metrics_from_measurement_result(result, [], [])
    cd_metric = next(m for m in metrics if m.metric_name == "ILF_Low_count")
    assert cd_metric.metric_value == 2
    assert cd_metric.computation_summary == "Total ILF (Low): 2"
    assert cd_metric.elements == []


def test_measurement_result_complexity_count_missing():
    """Kills _build_metrics_from_measurement_result__mutmut_101/102/105/107/110/112/114/117 (complexity count default)."""
    result = {
        "breakdown": {},
        "complexity_distribution": [{"function_type": "ILF", "complexity": "Low"}],
    }
    metrics = _build_metrics_from_measurement_result(result, [], [])
    cd_metric = next(m for m in metrics if m.metric_name == "ILF_Low_count")
    assert cd_metric.metric_value == 0
    assert cd_metric.computation_summary == "Total ILF (Low): 0"
    assert cd_metric.elements == []


def test_collect_cfm_elements_traces_each_element():
    """Kills _collect_cfm_elements__mutmut_17/18/20 (trace_element must receive element id and cfm)."""
    cfm = _make_cfm()
    spy = _SpyTracer()
    _elements, _rules = _collect_cfm_elements(cfm, spy)
    assert spy.calls == [("a1", cfm), ("br1", cfm)]


def test_collect_cfm_elements_label_falls_back_to_id():
    """Kills _collect_cfm_elements__mutmut_33 (element label falls back to element id when name is missing)."""
    spy = _SpyTracer()
    elements, _rules = _collect_cfm_elements(_NoNameCfm(), spy)
    assert elements[0]["element_id"] == "x1"
    assert elements[0]["element_label"] == "x1"


def test_collect_cfm_elements_rule_pack_id():
    """Kills _collect_cfm_elements__mutmut_45/50/55/56/57/59/60/62/63 (rule_pack_id from cfm run_id)."""
    cfm = _make_cfm()
    _elements, rules = _collect_cfm_elements(cfm, _SpyTracer())
    assert rules[0].rule_pack_id == "run-1"


def test_collect_cfm_elements_rule_pack_id_fallback():
    """Kills _collect_cfm_elements__mutmut_58/61 (rule_pack_id falls back to rule id)."""
    _elements, rules = _collect_cfm_elements(_NoRunIdCfm(), _SpyTracer())
    assert rules[0].rule_pack_id == "br1"


def test_collect_cfm_elements_rule_fields():
    """Kills _collect_cfm_elements__mutmut_46/47/48/49/51/52/53/54/64/65/67/68/69 (applied rule fields)."""
    cfm = _make_cfm()
    _elements, rules = _collect_cfm_elements(cfm, _SpyTracer())
    assert rules[0].rule_id == "br1"
    assert rules[0].rule_type == "business_rule"
    assert rules[0].description == "desc"
    assert rules[0].effect == "Identified as business rule in CFM"


def test_collect_cfm_elements_description_falls_back_to_name():
    """Kills _collect_cfm_elements__mutmut_66 (description falls back to rule name)."""
    _elements, rules = _collect_cfm_elements(_NoRunIdCfm(), _SpyTracer())
    assert rules[0].description == "BR1"


def test_collect_metrics_uses_elements_builder():
    """Kills _collect_metrics__mutmut_9 (elements path delegates to the elements builder)."""
    cfm = _make_cfm()
    elements = [_el("a")]
    from specmetrics.kernel.explanation._metrics import _build_metrics_from_elements

    expected = _build_metrics_from_elements(elements, [], cfm)
    actual = _collect_metrics(None, elements, [], cfm)
    assert actual == expected


def test_build_summary_counts():
    """Kills _build_summary__mutmut_5/6/7/8 (summary counters from metrics, elements, rules)."""
    from specmetrics.kernel.explanation.models import (
        ElementContribution,
        EvidenceReference,
    )

    rules = [AppliedRule(rule_pack_id="p", rule_id="r", rule_type="fact")]
    contrib = ElementContribution(
        element_id="e1",
        element_type="ILF",
        element_label="E1",
        evidence=[
            EvidenceReference(document_id="d", section_id="s", text="t", node_id="n")
        ],
    )
    metrics = [
        MetricExplanation(
            metric_name="m",
            metric_value=1,
            computation_summary="",
            elements=[contrib],
            applied_rules=rules,
        )
    ]
    summary = _build_summary(metrics, [{"element_id": "e1"}], rules)
    assert summary.total_metrics == 1
    assert summary.total_elements == 1
    assert summary.total_evidence_refs == 1
    assert summary.total_rules_applied == 1
