from __future__ import annotations

import uuid

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
    SFPCounter,
)


def _make_cfm(
    operations: dict | None = None,
    data_groups: dict | None = None,
) -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="test-run-001",
        operations=operations or {},
        data_groups=data_groups or {},
        metadata=BuildMetadata(run_id="test-run-001", version="1.0", source="test"),
    )


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


def _make_operation(
    op_id: str,
    name: str,
    node_type: str | None = "elementary_process",
    evidence: EvidenceRef | None = None,
) -> Operation:
    meta = {}
    if node_type:
        meta["node_type"] = node_type
    return Operation(
        id=op_id,
        name=name,
        parent_process_id="fp-001",
        evidence=evidence or _make_evidence(),
        metadata=meta,
    )


def _make_data_group(
    dg_id: str,
    name: str,
    node_type: str | None = "data_group",
    evidence: EvidenceRef | None = None,
) -> DataGroup:
    meta = {}
    if node_type:
        meta["node_type"] = node_type
    return DataGroup(
        id=dg_id,
        name=name,
        data_type="internal",
        evidence=evidence or _make_evidence(),
        metadata=meta,
    )


class TestT006_ElementaryProcessToFunctionalProcess:
    def test_identifies_functional_processes_from_operations(self):
        op = _make_operation("op-001", "Create Order")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1
        assert fps[0].name == "Create Order"
        assert fps[0].cfm_element_id == "op-001"

    def test_skips_operations_with_non_elementary_node_type(self):
        op = _make_operation("op-001", "Internal Step", node_type="internal_step")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 0

    def test_handles_no_node_type_metadata(self):
        op = _make_operation("op-001", "Create Order", node_type=None)
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1


class TestT007_DataGroupToLogicalFunction:
    def test_identifies_logical_functions_from_data_groups(self):
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert len(lfs) == 1
        assert lfs[0].name == "Customer"
        assert lfs[0].cfm_element_id == "dg-001"

    def test_skips_data_groups_with_non_data_group_node_type(self):
        dg = _make_data_group("dg-001", "Config", node_type="configuration")
        cfm = _make_cfm(data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert len(lfs) == 0

    def test_handles_no_node_type_metadata_for_data_groups(self):
        dg = _make_data_group("dg-001", "Customer", node_type=None)
        cfm = _make_cfm(data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert len(lfs) == 1


class TestT008_FixedContributionValues:
    def test_functional_process_gets_default_fp_value(self):
        op = _make_operation("op-001", "Create Order")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert fps[0].contribution == DEFAULT_FP_CONTRIBUTION

    def test_logical_function_gets_default_lf_value(self):
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        lfs = [
            c
            for c in result.measured_components
            if c.component_type == "logical_function"
        ]
        assert lfs[0].contribution == DEFAULT_LF_CONTRIBUTION

    def test_contribution_overrides_are_applied(self):
        op = _make_operation("op-001", "Create Order")
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(
            cfm,
            contribution_overrides={"functional_process": 5.0, "logical_function": 8.0},
        )
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
        assert fps[0].contribution == 5.0
        assert lfs[0].contribution == 8.0


class TestT009_EmptyCFM:
    def test_empty_cfm_returns_zero_counts(self):
        cfm = _make_cfm()
        counter = SFPCounter()
        result = counter.count(cfm)
        assert len(result.measured_components) == 0
        assert result.summary.total_component_count == 0
        assert result.summary.total_sfp == 0.0


class TestT010_DuplicateMerging:
    def test_duplicate_operations_are_merged(self):
        ev = _make_evidence()
        op1 = _make_operation("op-001", "Create Order", evidence=ev)
        op2 = _make_operation("op-002", "Create Order", evidence=ev)
        cfm = _make_cfm(operations={"op-001": op1, "op-002": op2})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1
        warnings = [w for w in result.warnings if w.code == "DUPLICATE_MERGED"]
        assert len(warnings) == 1

    def test_different_content_not_merged(self):
        ev1 = _make_evidence(text="create order")
        ev2 = _make_evidence(text="delete order")
        op1 = _make_operation("op-001", "Create Order", evidence=ev1)
        op2 = _make_operation("op-002", "Delete Order", evidence=ev2)
        cfm = _make_cfm(operations={"op-001": op1, "op-002": op2})
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 2


class TestT011_DeterministicOutput:
    def test_repeated_execution_produces_byte_identical_results(self):
        op = _make_operation("op-001", "Create Order")
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result1 = counter.count(cfm, run_id="fixed-run-001")
        result2 = counter.count(cfm, run_id="fixed-run-001")

        d1 = result1.model_dump()
        d2 = result2.model_dump()
        d1.pop("measured_at", None)
        d2.pop("measured_at", None)

        assert d1 == d2


class TestT016_EvidenceTrailPreservation:
    def test_each_component_has_evidence_refs(self):
        ev = _make_evidence()
        op = _make_operation("op-001", "Create Order", evidence=ev)
        dg = _make_data_group("dg-001", "Customer", evidence=ev)
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        for component in result.measured_components:
            assert len(component.evidence_refs) > 0
            ref = component.evidence_refs[0]
            assert ref.document_id == "doc-001"
            assert ref.graph_node_id == "gn-001"

    def test_evidence_refs_contain_originating_cfm_element(self):
        ev = _make_evidence(graph_node_id="gn-op-001")
        op = _make_operation("op-001", "Create Order", evidence=ev)
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        fp = result.measured_components[0]
        assert fp.cfm_element_id == "op-001"
        assert fp.evidence_refs[0].graph_node_id == "gn-op-001"


class TestT034_IncrementalRecomputation:
    def test_incremental_recomputes_only_modified_components(self):
        ev1 = _make_evidence(text="create order")
        ev2 = _make_evidence(text="delete order")
        op1 = _make_operation("op-001", "Create Order", evidence=ev1)
        op2 = _make_operation("op-002", "Delete Order", evidence=ev2)
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(
            operations={"op-001": op1, "op-002": op2}, data_groups={"dg-001": dg}
        )
        counter = SFPCounter()
        result = counter.count(cfm)
        assert result.summary.total_component_count == 3

    def test_modified_ids_recompute_only_specified(self):
        ev1 = _make_evidence(text="create order")
        ev2 = _make_evidence(text="delete order")
        op1 = _make_operation("op-001", "Create Order", evidence=ev1)
        op2 = _make_operation("op-002", "Delete Order", evidence=ev2)
        cfm = _make_cfm(operations={"op-001": op1, "op-002": op2})
        counter = SFPCounter()
        full_result = counter.count(cfm, run_id="incr-test")
        assert full_result.summary.total_component_count == 2

        modified_ids = ["op-001"]
        incremental_result = counter.count(
            cfm,
            run_id="incr-test",
            previous_result=full_result,
            modified_element_ids=modified_ids,
        )
        assert incremental_result.summary.total_component_count == 2


class TestPerformance:
    @pytest.mark.slow
    def test_medium_cfm_completes_under_5_seconds(self):
        ops = {}
        for i in range(500):
            ops[f"op-{i:03d}"] = _make_operation(f"op-{i:03d}", f"Process {i}")
        dgs = {}
        for i in range(300):
            dgs[f"dg-{i:03d}"] = _make_data_group(f"dg-{i:03d}", f"Entity {i}")
        cfm = _make_cfm(operations=ops, data_groups=dgs)
        import time

        counter = SFPCounter()
        start = time.monotonic()
        counter.count(cfm)
        elapsed = time.monotonic() - start
        assert elapsed < 5.0


class TestProcessedComponentIdentity:
    def test_components_receive_sequential_ids(self):
        ops = {}
        for i in range(3):
            ev = _make_evidence(text=f"text {i}")
            ops[f"op-{i:03d}"] = _make_operation(
                f"op-{i:03d}", f"Process {i}", evidence=ev
            )
        cfm = _make_cfm(operations=ops)
        counter = SFPCounter()
        result = counter.count(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert [c.id for c in fps] == [
            "cmp-functional_process-1",
            "cmp-functional_process-2",
            "cmp-functional_process-3",
        ]

    def test_cfm_element_type_names(self):
        op = _make_operation("op-001", "Create Order")
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm)
        by_id = {c.cfm_element_id: c for c in result.measured_components}
        assert by_id["op-001"].cfm_element_type == "Operation"
        assert by_id["dg-001"].cfm_element_type == "DataGroup"


class TestInclusionCriteriaAndExclusions:
    def test_excluded_types_drops_functional_processes(self):
        op = _make_operation("op-001", "Create Order")
        dg = _make_data_group("dg-001", "Customer")
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(cfm, excluded_types=["functional_process"])
        assert len(result.measured_components) == 1
        assert result.measured_components[0].component_type == "logical_function"

    def test_inclusion_criteria_node_types_drive_classification(self):
        op = _make_operation("op-001", "Op", node_type="custom_process")
        dg = _make_data_group("dg-001", "Cust", node_type="custom_group")
        cfm = _make_cfm(operations={"op-001": op}, data_groups={"dg-001": dg})
        counter = SFPCounter()
        result = counter.count(
            cfm,
            inclusion_criteria={
                "functional_process": {
                    "node_types": ["custom_process"],
                    "semantic_types": [],
                },
                "logical_function": {
                    "node_types": ["custom_group"],
                    "semantic_types": [],
                },
            },
        )
        types = {c.component_type for c in result.measured_components}
        assert types == {"functional_process", "logical_function"}

    def test_element_inclusions_override_node_classification(self):
        op = _make_operation("op-001", "Op", node_type="internal_step")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(
            cfm, element_inclusions={"by_id": ["op-001"], "by_pattern": []}
        )
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1

    def test_element_inclusions_by_name_pattern(self):
        op = _make_operation("op-001", "Hidden Process", node_type="internal_step")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(
            cfm,
            element_inclusions={"by_id": [], "by_pattern": ["Hidden*"]},
        )
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1


class TestRunMeta:
    def test_warnings_are_a_list_when_duplicate(self):
        ev = _make_evidence()
        op1 = _make_operation("op-001", "Create Order", evidence=ev)
        op2 = _make_operation("op-002", "Create Order", evidence=ev)
        cfm = _make_cfm(operations={"op-001": op1, "op-002": op2})
        counter = SFPCounter()
        result = counter.count(cfm)
        assert isinstance(result.warnings, list)
        assert len(result.warnings) == 1

    def test_merge_previous_keeps_unmodified_absent(self):
        ev_a = _make_evidence(text="create order")
        ev_b = _make_evidence(text="delete order")
        op_a = _make_operation("op-001", "Create Order", evidence=ev_a)
        op_b = _make_operation("op-002", "Delete Order", evidence=ev_b)
        dg = _make_data_group("dg-001", "Customer")
        full_cfm = _make_cfm(
            operations={"op-001": op_a, "op-002": op_b}, data_groups={"dg-001": dg}
        )
        counter = SFPCounter()
        full = counter.count(full_cfm)
        current_cfm = _make_cfm(operations={"op-001": op_a, "op-002": op_b})
        inc = counter.count(
            current_cfm,
            previous_result=full,
            modified_element_ids=["op-001"],
        )
        assert inc.summary.total_component_count == 3

    def test_rule_pack_id_is_preserved(self):
        op = _make_operation("op-001", "Create Order")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm, rule_pack_id="rp-123")
        assert result.rule_pack_id == "rp-123"

    def test_run_id_is_a_uuid_when_omitted(self):
        op = _make_operation("op-001", "Create Order")
        cfm = _make_cfm(operations={"op-001": op})
        counter = SFPCounter()
        result = counter.count(cfm)
        assert result.run_id != "None"
        uuid.UUID(result.run_id)
