from datetime import UTC, datetime

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.plugins.measurement.fpa.counter import FPACounter
from specmetrics.plugins.measurement.fpa.models import MeasuredFunction


def _make_cfm(
    data_groups: list[DataGroup] | None = None,
    operations: list[Operation] | None = None,
) -> CanonicalFunctionalModel:
    now = datetime.now(UTC)
    return CanonicalFunctionalModel(
        run_id="test-run",
        data_groups={g.id: g for g in (data_groups or [])},
        operations={o.id: o for o in (operations or [])},
        metadata=BuildMetadata(
            run_id="test-run",
            build_duration_ms=0,
            element_counts={},
            total_input_nodes=0,
            unclassified_count=0,
            conflicts=[],
            created_at=now,
        ),
    )


def _evidence(text: str = "src") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="n1",
        document_id="doc1",
        section_id="s1",
        text=text,
    )


class TestDataGroupClassification:
    def test_internal_data_group_to_ilf(self):
        dg = DataGroup(
            id="dg1", name="Orders", data_type="internal", evidence=_evidence()
        )
        cfm = _make_cfm(data_groups=[dg])
        counter = FPACounter()
        result = counter.count(cfm)
        ilf_fns = [f for f in result.measured_functions if f.function_type == "ILF"]
        assert len(ilf_fns) == 1
        assert ilf_fns[0].cfm_element_id == "dg1"
        assert ilf_fns[0].name == "Orders"

    def test_external_data_group_to_eif(self):
        dg = DataGroup(
            id="dg1", name="TaxAPI", data_type="external", evidence=_evidence()
        )
        cfm = _make_cfm(data_groups=[dg])
        counter = FPACounter()
        result = counter.count(cfm)
        eif_fns = [f for f in result.measured_functions if f.function_type == "EIF"]
        assert len(eif_fns) == 1

    def test_shared_data_group_treated_as_ilf(self):
        dg = DataGroup(id="dg1", name="Cache", data_type="shared", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        counter = FPACounter()
        result = counter.count(cfm)
        ilf_fns = [f for f in result.measured_functions if f.function_type == "ILF"]
        assert len(ilf_fns) == 1

    def test_multiple_data_groups_classified_correctly(self):
        dgs = [
            DataGroup(
                id="dg1", name="Internal", data_type="internal", evidence=_evidence("a")
            ),
            DataGroup(
                id="dg2", name="External", data_type="external", evidence=_evidence("b")
            ),
            DataGroup(
                id="dg3", name="Shared", data_type="shared", evidence=_evidence("c")
            ),
        ]
        cfm = _make_cfm(data_groups=dgs)
        counter = FPACounter()
        result = counter.count(cfm)
        types = {f.cfm_element_id: f.function_type for f in result.measured_functions}
        assert types["dg1"] == "ILF"
        assert types["dg2"] == "EIF"
        assert types["dg3"] == "ILF"

    def test_data_function_preserves_element_type_and_section(self):
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        fn = FPACounter().count(cfm).measured_functions[0]
        assert fn.cfm_element_type == "DataGroup"
        assert fn.evidence_refs[0].section_id == "s1"

    def test_excluded_first_does_not_break_remaining_data_groups(self):
        dgs = [
            DataGroup(
                id="dg1", name="Internal", data_type="internal",
                evidence=_evidence("a"),
            ),
            DataGroup(
                id="dg2", name="External", data_type="external",
                evidence=_evidence("b"),
            ),
        ]
        cfm = _make_cfm(data_groups=dgs)
        result = FPACounter().count(cfm, excluded_types=["ILF"])
        assert [f.function_type for f in result.measured_functions] == ["EIF"]


class TestOperationClassification:
    def test_input_operation_to_ei(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input"},
        )
        cfm = _make_cfm(operations=[op])
        counter = FPACounter()
        result = counter.count(cfm)
        ei_fns = [f for f in result.measured_functions if f.function_type == "EI"]
        assert len(ei_fns) == 1
        assert ei_fns[0].cfm_element_id == "op1"

    def test_output_operation_to_eo(self):
        op = Operation(
            id="op1",
            name="PrintReport",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "output"},
        )
        cfm = _make_cfm(operations=[op])
        counter = FPACounter()
        result = counter.count(cfm)
        eo_fns = [f for f in result.measured_functions if f.function_type == "EO"]
        assert len(eo_fns) == 1

    def test_query_operation_to_eq(self):
        op = Operation(
            id="op1",
            name="LookupProduct",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "query"},
        )
        cfm = _make_cfm(operations=[op])
        counter = FPACounter()
        result = counter.count(cfm)
        eq_fns = [f for f in result.measured_functions if f.function_type == "EQ"]
        assert len(eq_fns) == 1

    def test_operation_without_direction_is_skipped(self):
        op = Operation(
            id="op1",
            name="UnknownOp",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={},
        )
        cfm = _make_cfm(operations=[op])
        counter = FPACounter()
        result = counter.count(cfm)
        assert len(result.measured_functions) == 0
        assert len(result.warnings) == 1

    def test_unclassified_warning_uses_expected_code(self):
        op = Operation(
            id="op1",
            name="UnknownOp",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={},
        )
        cfm = _make_cfm(operations=[op])
        result = FPACounter().count(cfm)
        assert result.warnings[0].code == "UNCLASSIFIED_OPERATION"
        assert result.warnings[0].cfm_element_id == "op1"

    def test_unclassified_first_does_not_break_later_operations(self):
        ops = [
            Operation(
                id="op1", name="UnknownOp", parent_process_id="p1",
                evidence=_evidence(), metadata={},
            ),
            Operation(
                id="op2", name="CreateOrder", parent_process_id="p1",
                evidence=_evidence(), metadata={"direction": "input"},
            ),
        ]
        cfm = _make_cfm(operations=ops)
        result = FPACounter().count(cfm)
        assert [f.cfm_element_id for f in result.measured_functions] == ["op2"]

    def test_excluded_first_does_not_break_later_operations(self):
        ops = [
            Operation(
                id="op1", name="Lookup", parent_process_id="p1",
                evidence=_evidence(), metadata={"direction": "query"},
            ),
            Operation(
                id="op2", name="CreateOrder", parent_process_id="p1",
                evidence=_evidence(), metadata={"direction": "input"},
            ),
        ]
        cfm = _make_cfm(operations=ops)
        result = FPACounter().count(cfm, excluded_types=["EQ"])
        assert [f.function_type for f in result.measured_functions] == ["EI"]

    def test_transactional_function_preserves_element_type_and_section(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input"},
        )
        cfm = _make_cfm(operations=[op])
        fn = FPACounter().count(cfm).measured_functions[0]
        assert fn.cfm_element_type == "Operation"
        assert fn.evidence_refs[0].section_id == "s1"


class TestEmptyCFM:
    def test_empty_cfm_returns_zero_count(self):
        cfm = _make_cfm()
        counter = FPACounter()
        result = counter.count(cfm)
        assert result.summary.total_function_count == 0
        assert result.summary.total_ufp == 0
        assert len(result.measured_functions) == 0
        assert len(result.errors) == 0

    def test_cfm_with_only_actors_returns_zero_count(self):
        now = datetime.now(UTC)
        from specmetrics.kernel.cfm.model import Actor

        cfm = CanonicalFunctionalModel(
            run_id="test-run",
            actors={"a1": Actor(id="a1", name="User", evidence=_evidence())},
            metadata=BuildMetadata(
                run_id="test-run",
                build_duration_ms=0,
                element_counts={},
                total_input_nodes=1,
                unclassified_count=0,
                conflicts=[],
                created_at=now,
            ),
        )
        counter = FPACounter()
        result = counter.count(cfm)
        assert result.summary.total_function_count == 0


class TestEvidencePreservation:
    def test_measured_function_contains_evidence_refs(self):
        ev = _evidence("source text here")
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=ev)
        cfm = _make_cfm(data_groups=[dg])
        counter = FPACounter()
        result = counter.count(cfm)
        fn = result.measured_functions[0]
        assert len(fn.evidence_refs) > 0
        assert fn.evidence_refs[0].text == "source text here"
        assert fn.evidence_refs[0].graph_node_id == "n1"


class TestPerformance:
    """Performance benchmarks for SC-001 and SC-007."""

    def test_sc001_10_data_groups_15_processes_under_5_seconds(self):
        now = datetime.now(UTC)
        data_groups = [
            DataGroup(
                id=f"dg{i}",
                name=f"Group{i}",
                data_type="internal",
                evidence=_evidence(f"data{i}"),
            )
            for i in range(10)
        ]
        ops = []
        for i in range(15):
            ops.append(
                Operation(
                    id=f"op{i}",
                    name=f"Process{i}",
                    parent_process_id="p1",
                    evidence=_evidence(f"op{i}"),
                    metadata={"direction": "input"},
                )
            )
        cfm = CanonicalFunctionalModel(
            run_id="perf-test",
            data_groups={g.id: g for g in data_groups},
            operations={o.id: o for o in ops},
            metadata=BuildMetadata(
                run_id="perf-test",
                build_duration_ms=0,
                element_counts={},
                total_input_nodes=25,
                unclassified_count=0,
                conflicts=[],
                created_at=now,
            ),
        )
        counter = FPACounter()
        import time

        start = time.monotonic()
        result = counter.count(cfm)
        elapsed = time.monotonic() - start
        assert result.summary.total_function_count == 25
        assert elapsed < 5.0, f"SC-001: expected <5s, got {elapsed:.2f}s"

    def test_sc007_500_plus_functions_no_errors(self):
        now = datetime.now(UTC)
        data_groups = [
            DataGroup(
                id=f"dg{i}",
                name=f"Group{i}",
                data_type="internal",
                evidence=_evidence(f"d{i}"),
            )
            for i in range(100)
        ]
        ops = []
        for i in range(400):
            direction = ["input", "output", "query"][i % 3]
            ops.append(
                Operation(
                    id=f"op{i}",
                    name=f"Op{i}",
                    parent_process_id="p1",
                    evidence=_evidence(f"e{i}"),
                    metadata={"direction": direction},
                )
            )
        cfm = CanonicalFunctionalModel(
            run_id="perf-large",
            data_groups={g.id: g for g in data_groups},
            operations={o.id: o for o in ops},
            metadata=BuildMetadata(
                run_id="perf-large",
                build_duration_ms=0,
                element_counts={},
                total_input_nodes=500,
                unclassified_count=0,
                conflicts=[],
                created_at=now,
            ),
        )
        counter = FPACounter()
        result = counter.count(cfm)
        assert result.summary.total_function_count == 500
        assert len(result.warnings) == 0


class TestDataGroupMetadataCounts:
    def test_det_and_ret_counts_from_metadata(self):
        dg = DataGroup(
            id="dg1",
            name="Orders",
            data_type="internal",
            evidence=_evidence(),
            metadata={"det_count": "10", "ret_count": "3"},
        )
        cfm = _make_cfm(data_groups=[dg])
        result = FPACounter().count(cfm)
        fn = result.measured_functions[0]
        assert fn.function_type == "ILF"
        assert fn.det_count == 10
        assert fn.ret_count == 3

    def test_defaults_when_no_metadata(self):
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        fn = FPACounter().count(cfm).measured_functions[0]
        assert fn.det_count == 1
        assert fn.ret_count == 1

    def test_external_data_group_defaults_ret_count_to_one(self):
        dg = DataGroup(
            id="dg1",
            name="TaxAPI",
            data_type="external",
            evidence=_evidence(),
            metadata={"det_count": "10"},
        )
        cfm = _make_cfm(data_groups=[dg])
        result = FPACounter().count(cfm)
        fn = result.measured_functions[0]
        assert fn.function_type == "EIF"
        assert fn.ret_count == 1
        assert fn.det_count == 10


class TestOperationMetadataCounts:
    def test_ftr_and_det_counts_from_metadata(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input", "det_count": "12", "ftr_count": "2"},
        )
        cfm = _make_cfm(operations=[op])
        fn = FPACounter().count(cfm).measured_functions[0]
        assert fn.det_count == 12
        assert fn.ftr_count == 2

    def test_ftr_count_defaults_to_data_group_count(self):
        ops = [
            Operation(
                id="op1",
                name="Add",
                parent_process_id="p1",
                evidence=_evidence(),
                metadata={"direction": "input"},
            )
        ]
        dgs = [
            DataGroup(id="dg1", name="A", data_type="internal", evidence=_evidence()),
            DataGroup(id="dg2", name="B", data_type="external", evidence=_evidence()),
        ]
        cfm = _make_cfm(data_groups=dgs, operations=ops)
        fns = FPACounter().count(cfm).measured_functions
        fn = next(f for f in fns if f.function_type == "EI")
        assert fn.ftr_count == 2

    def test_det_defaults_to_one_when_no_metadata(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input"},
        )
        cfm = _make_cfm(operations=[op])
        fn = FPACounter().count(cfm).measured_functions[0]
        assert fn.det_count == 1


class TestExclusionsAndOverrides:
    def test_excluded_data_function_type_skipped(self):
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        result = FPACounter().count(cfm, excluded_types=["ILF"])
        assert len(result.measured_functions) == 0

    def test_excluded_transactional_type_skipped(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input"},
        )
        cfm = _make_cfm(operations=[op])
        result = FPACounter().count(cfm, excluded_types=["EI"])
        assert len(result.measured_functions) == 0

    def test_weight_override_applied(self):
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        overrides = {"ILF": {"Low": 99}}
        fn = FPACounter().count(cfm, weight_overrides=overrides).measured_functions[0]
        assert fn.function_type == "ILF"
        assert fn.ufp_weight == 99

    def test_weight_override_applied_to_transactional(self):
        op = Operation(
            id="op1",
            name="CreateOrder",
            parent_process_id="p1",
            evidence=_evidence(),
            metadata={"direction": "input"},
        )
        cfm = _make_cfm(operations=[op])
        overrides = {"EI": {"Low": 99}}
        fn = FPACounter().count(cfm, weight_overrides=overrides).measured_functions[0]
        assert fn.function_type == "EI"
        assert fn.ufp_weight == 99


def _mf(fn_id, ftype, weight, det=1, ret=None, ftr=None, cx="Low"):
    return MeasuredFunction(
        id=fn_id,
        name=fn_id,
        function_type=ftype,
        complexity=cx,
        det_count=det,
        ret_count=ret,
        ftr_count=ftr,
        ufp_weight=weight,
        cfm_element_id=fn_id,
        cfm_element_type="DataGroup",
        evidence_refs=[],
    )


class TestSummaryTotals:
    def test_by_type_accumulates_count_and_ufp(self):
        fns = [
            _mf("f1", "ILF", 7, 4, ret="1"),
            _mf("f2", "ILF", 7, 6, ret="1"),
            _mf("f3", "EO", 5, 4, ftr="2", cx="Average"),
        ]
        summary = FPACounter()._build_summary(fns)
        assert summary.by_type["ILF"].count == 2
        assert summary.by_type["ILF"].total_ufp == 14
        assert summary.by_type["EO"].count == 1
        assert summary.by_type["EO"].total_ufp == 5

    def test_by_complexity_counts_accumulate(self):
        fns = [
            _mf("f1", "ILF", 7, ret="1"),
            _mf("f2", "ILF", 7, ret="1"),
            _mf("f3", "EO", 5, ftr="2", cx="Average"),
        ]
        summary = FPACounter()._build_summary(fns)
        assert summary.by_complexity == {"Low": 2, "Average": 1}

    def test_complexity_distribution_rows(self):
        fns = [
            _mf("f1", "ILF", 7, ret="1"),
            _mf("f2", "ILF", 7, ret="1"),
            _mf("f3", "EO", 5, ftr="2", cx="Average"),
        ]
        summary = FPACounter()._build_summary(fns)
        ilf_row = next(
            r for r in summary.complexity_distribution if r.function_type == "ILF"
        )
        assert ilf_row.count == 2
        assert ilf_row.total_ufp == 14
        assert ilf_row.ufp_per_function == 7
        assert isinstance(ilf_row.ufp_per_function, int)
        eo_row = next(
            r for r in summary.complexity_distribution if r.function_type == "EO"
        )
        assert eo_row.count == 1
        assert eo_row.ufp_per_function == 5


def test_excluded_data_function_does_not_break_later():
    """Mutmut 13: an excluded data function must not stop later ones."""
    dgs = [
        DataGroup(
            id="dg1", name="Internal", data_type="internal",
            evidence=_evidence("a"),
        ),
        DataGroup(
            id="dg2", name="External", data_type="external",
            evidence=_evidence("b"),
        ),
    ]
    cfm = _make_cfm(data_groups=dgs)
    result = FPACounter().count(cfm, excluded_types=["ILF"])
    assert [f.function_type for f in result.measured_functions] == ["EIF"]


def test_excluded_transactional_does_not_break_later():
    """Mutmut 23/25: an excluded transactional function must not stop later ones."""
    ops = [
        Operation(
            id="op1", name="Lookup", parent_process_id="p1",
            evidence=_evidence(), metadata={"direction": "query"},
        ),
        Operation(
            id="op2", name="CreateOrder", parent_process_id="p1",
            evidence=_evidence(), metadata={"direction": "input"},
        ),
    ]
    cfm = _make_cfm(operations=ops)
    result = FPACounter().count(cfm, excluded_types=["EQ"])
    assert [f.function_type for f in result.measured_functions] == ["EI"]


def test_data_function_default_det_ret_counts():
    """Mutmut 15/24: data functions without metadata default to det=1, ret=1."""
    dg = DataGroup(
        id="dg1", name="Orders", data_type="internal", evidence=_evidence()
    )
    cfm = _make_cfm(data_groups=[dg])
    fn = FPACounter().count(cfm).measured_functions[0]
    assert fn.det_count == 1
    assert fn.ret_count == 1


def test_transactional_default_det_count():
    """Mutmut 27: transactional functions default det_count to 1."""
    op = Operation(
        id="op1", name="CreateOrder", parent_process_id="p1",
        evidence=_evidence(), metadata={"direction": "input"},
    )
    cfm = _make_cfm(operations=[op])
    fn = FPACounter().count(cfm).measured_functions[0]
    assert fn.det_count == 1


def test_weight_overrides_applied_to_data_functions():
    """Mutmut 55/58: data function weight must honor weight overrides."""
    dg = DataGroup(
        id="dg1", name="Orders", data_type="internal", evidence=_evidence()
    )
    cfm = _make_cfm(data_groups=[dg])
    overrides = {"ILF": {"Low": 99}}
    fn = FPACounter().count(cfm, weight_overrides=overrides).measured_functions[0]
    assert fn.function_type == "ILF"
    assert fn.ufp_weight == 99


def test_data_function_section_and_type_preserved():
    """Mutmut 52/56/79/80/81: data functions preserve section and element type."""
    dg = DataGroup(
        id="dg1", name="Orders", data_type="internal", evidence=_evidence()
    )
    cfm = _make_cfm(data_groups=[dg])
    fn = FPACounter().count(cfm).measured_functions[0]
    assert fn.cfm_element_type == "DataGroup"
    assert fn.evidence_refs[0].section_id == "s1"


def test_unclassified_operation_warning_exact():
    """Mutmut 5/7/10/21/22: missing direction yields UNCLASSIFIED_OPERATION."""
    op = Operation(
        id="op1", name="UnknownOp", parent_process_id="p1",
        evidence=_evidence(), metadata={},
    )
    cfm = _make_cfm(operations=[op])
    result = FPACounter().count(cfm)
    assert len(result.measured_functions) == 0
    assert result.warnings[0].code == "UNCLASSIFIED_OPERATION"
    assert result.warnings[0].cfm_element_id == "op1"


def test_transactional_element_id_preserved():
    """Mutmut 17/20: transactional functions preserve the CFM element id."""
    op = Operation(
        id="op1", name="CreateOrder", parent_process_id="p1",
        evidence=_evidence(), metadata={"direction": "input"},
    )
    cfm = _make_cfm(operations=[op])
    fn = FPACounter().count(cfm).measured_functions[0]
    assert fn.cfm_element_id == "op1"


def test_transactional_section_and_type_preserved():
    """Mutmut 62/66/89/90/91: transactional functions preserve section and type."""
    op = Operation(
        id="op1", name="CreateOrder", parent_process_id="p1",
        evidence=_evidence(), metadata={"direction": "input"},
    )
    cfm = _make_cfm(operations=[op])
    fn = FPACounter().count(cfm).measured_functions[0]
    assert fn.cfm_element_type == "Operation"
    assert fn.evidence_refs[0].section_id == "s1"
