from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.plugins.measurement.sfp.counter import (
    DEFAULT_FP_CONTRIBUTION,
    DEFAULT_LF_CONTRIBUTION,
)
from specmetrics.plugins.measurement.sfp.models import RulePack
from specmetrics.plugins.measurement.sfp.plugin import SFPMeasurementPlugin


def _make_evidence(
    graph_node_id: str = "gn-001",
    document_id: str = "doc-001",
    section_id: str = "s1",
    text: str = "test evidence",
) -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=graph_node_id,
        document_id=document_id,
        section_id=section_id,
        text=text,
    )


def _build_synthetic_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="integration-test-cfm",
        operations={
            "op-001": Operation(
                id="op-001",
                name="Create Order",
                parent_process_id="fp-001",
                evidence=_make_evidence(
                    graph_node_id="gn-op-001",
                    document_id="spec-001",
                    text="User submits order",
                ),
                metadata={"node_type": "elementary_process"},
            ),
            "op-002": Operation(
                id="op-002",
                name="Approve Order",
                parent_process_id="fp-001",
                evidence=_make_evidence(
                    graph_node_id="gn-op-002",
                    document_id="spec-001",
                    text="Manager approves order",
                ),
                metadata={"node_type": "elementary_process"},
            ),
            "op-003": Operation(
                id="op-003",
                name="Ship Order",
                parent_process_id="fp-002",
                evidence=_make_evidence(
                    graph_node_id="gn-op-003",
                    document_id="spec-002",
                    text="Warehouse ships order",
                ),
                metadata={"node_type": "elementary_process"},
            ),
        },
        data_groups={
            "dg-001": DataGroup(
                id="dg-001",
                name="Customer",
                evidence=_make_evidence(
                    graph_node_id="gn-dg-001",
                    document_id="spec-001",
                    text="Customer entity",
                ),
                metadata={"node_type": "data_group"},
            ),
            "dg-002": DataGroup(
                id="dg-002",
                name="Order",
                evidence=_make_evidence(
                    graph_node_id="gn-dg-002",
                    document_id="spec-001",
                    text="Order entity",
                ),
                metadata={"node_type": "data_group"},
            ),
            "dg-003": DataGroup(
                id="dg-003",
                name="Product",
                evidence=_make_evidence(
                    graph_node_id="gn-dg-003",
                    document_id="spec-002",
                    text="Product entity",
                ),
                metadata={"node_type": "data_group"},
            ),
        },
        metadata=BuildMetadata(
            run_id="integration-test-cfm", version="1.0", source="test"
        ),
    )


class TestT015_FullMeasurement:
    def test_full_measurement_with_synthetic_cfm(self):
        cfm = _build_synthetic_cfm()
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)

        assert result.run_id is not None
        assert result.cfm_run_id == "integration-test-cfm"

        assert result.summary.total_component_count == 6
        expected_total = (3 * DEFAULT_FP_CONTRIBUTION) + (3 * DEFAULT_LF_CONTRIBUTION)
        assert result.summary.total_sfp == expected_total

        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert len(fps) == 3
        assert len(lfs) == 3

        for component in result.measured_components:
            assert len(component.evidence_refs) > 0
            ref = component.evidence_refs[0]
            assert ref.document_id
            assert ref.text

    def test_measurement_is_deterministic(self):
        cfm = _build_synthetic_cfm()
        plugin = SFPMeasurementPlugin()

        result1 = plugin.measure(cfm)
        result2 = plugin.measure(cfm)

        d1 = result1.model_dump()
        d2 = result2.model_dump()
        d1.pop("run_id", None)
        d2.pop("run_id", None)
        d1.pop("measured_at", None)
        d2.pop("measured_at", None)

        assert d1 == d2


class TestT021_EvidenceTrailCompleteness:
    def test_all_components_have_evidence(self):
        cfm = _build_synthetic_cfm()
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        for component in result.measured_components:
            assert len(component.evidence_refs) > 0
            ref = component.evidence_refs[0]
            assert ref.graph_node_id
            assert ref.text


class TestT031_RulePackIntegration:
    def test_rule_pack_excludes_logical_functions(self):
        cfm = _build_synthetic_cfm()
        rule_pack = RulePack(
            id="exclude-lf-rules",
            methodology="SFP",
            excluded_types=["logical_function"],
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm, rule_pack=rule_pack)
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert len(lfs) == 0
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 3

    def test_rule_pack_overrides_contributions(self):
        cfm = _build_synthetic_cfm()
        rule_pack = RulePack(
            id="override-rules",
            methodology="SFP",
            contribution_overrides={"functional_process": 5.0, "logical_function": 8.0},
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm, rule_pack=rule_pack)
        for c in result.measured_components:
            if c.component_type == "functional_process":
                assert c.contribution == 5.0
            else:
                assert c.contribution == 8.0

    def test_rule_pack_element_exclusion_by_id(self):
        cfm = _build_synthetic_cfm()
        rule_pack = RulePack(
            id="exclude-op-001",
            methodology="SFP",
            element_exclusions={"by_id": ["op-001"], "by_pattern": []},
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm, rule_pack=rule_pack)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 2
        assert all(c.cfm_element_id != "op-001" for c in fps)


class TestT039_FullPipelineExecution:
    def test_plugin_measurement_invocation(self):
        cfm = _build_synthetic_cfm()
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        assert result.summary.total_component_count > 0
        assert result.summary.total_sfp > 0
        assert len(result.explanations) == result.summary.total_component_count


class TestT043_Scalability:
    @pytest.mark.slow
    def test_doubling_cfm_size_linear_deviation(self):
        import statistics
        import time

        plugin = SFPMeasurementPlugin()

        def _build_ops(count: int, prefix: str = ""):
            ops = {}
            for i in range(count):
                ev = _make_evidence(text=f"{prefix}process {i}")
                ops[f"op-{prefix}{i:04d}"] = Operation(
                    id=f"op-{prefix}{i:04d}",
                    name=f"Process {i}",
                    parent_process_id="fp-001",
                    evidence=ev,
                    metadata={"node_type": "elementary_process"},
                )
            return ops

        def _timed(ops) -> float:
            cfm = CanonicalFunctionalModel(
                run_id="test",
                operations=ops,
                metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
            )
            durations = []
            for _ in range(10):
                start = time.perf_counter()
                plugin.measure(cfm)
                durations.append(time.perf_counter() - start)
            durations.sort()
            return statistics.median(durations)

        base_ops = _build_ops(2000, "a")
        double_ops = _build_ops(4000, "b")

        for _ in range(5):
            _timed(base_ops)
            _timed(double_ops)

        base_time = _timed(base_ops)
        double_time = _timed(double_ops)

        ratio = double_time / base_time if base_time > 0 else 0
        assert abs(ratio - 2.0) <= 2.0
