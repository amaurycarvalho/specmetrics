from datetime import datetime, timezone


from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.plugins.measurement.fpa.counter import FPACounter


def _make_cfm(
    data_groups: list[DataGroup] | None = None,
    operations: list[Operation] | None = None,
) -> CanonicalFunctionalModel:
    now = datetime.now(timezone.utc)
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
        dg = DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence())
        cfm = _make_cfm(data_groups=[dg])
        counter = FPACounter()
        result = counter.count(cfm)
        ilf_fns = [f for f in result.measured_functions if f.function_type == "ILF"]
        assert len(ilf_fns) == 1
        assert ilf_fns[0].cfm_element_id == "dg1"
        assert ilf_fns[0].name == "Orders"

    def test_external_data_group_to_eif(self):
        dg = DataGroup(id="dg1", name="TaxAPI", data_type="external", evidence=_evidence())
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
            DataGroup(id="dg1", name="Internal", data_type="internal", evidence=_evidence("a")),
            DataGroup(id="dg2", name="External", data_type="external", evidence=_evidence("b")),
            DataGroup(id="dg3", name="Shared", data_type="shared", evidence=_evidence("c")),
        ]
        cfm = _make_cfm(data_groups=dgs)
        counter = FPACounter()
        result = counter.count(cfm)
        types = {f.cfm_element_id: f.function_type for f in result.measured_functions}
        assert types["dg1"] == "ILF"
        assert types["dg2"] == "EIF"
        assert types["dg3"] == "ILF"


class TestOperationClassification:
    def test_input_operation_to_ei(self):
        op = Operation(
            id="op1", name="CreateOrder", parent_process_id="p1",
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
            id="op1", name="PrintReport", parent_process_id="p1",
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
            id="op1", name="LookupProduct", parent_process_id="p1",
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
            id="op1", name="UnknownOp", parent_process_id="p1",
            evidence=_evidence(),
            metadata={},
        )
        cfm = _make_cfm(operations=[op])
        counter = FPACounter()
        result = counter.count(cfm)
        assert len(result.measured_functions) == 0
        assert len(result.warnings) == 1


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
        now = datetime.now(timezone.utc)
        from specmetrics.kernel.cfm.model import Actor
        cfm = CanonicalFunctionalModel(
            run_id="test-run",
            actors={"a1": Actor(id="a1", name="User", evidence=_evidence())},
            metadata=BuildMetadata(
                run_id="test-run", build_duration_ms=0, element_counts={},
                total_input_nodes=1, unclassified_count=0, conflicts=[],
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
        now = datetime.now(timezone.utc)
        data_groups = [
            DataGroup(id=f"dg{i}", name=f"Group{i}", data_type="internal",
                       evidence=_evidence(f"data{i}"))
            for i in range(10)
        ]
        ops = []
        for i in range(15):
            ops.append(Operation(
                id=f"op{i}", name=f"Process{i}", parent_process_id="p1",
                evidence=_evidence(f"op{i}"),
                metadata={"direction": "input"},
            ))
        cfm = CanonicalFunctionalModel(
            run_id="perf-test",
            data_groups={g.id: g for g in data_groups},
            operations={o.id: o for o in ops},
            metadata=BuildMetadata(
                run_id="perf-test", build_duration_ms=0, element_counts={},
                total_input_nodes=25, unclassified_count=0, conflicts=[],
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
        now = datetime.now(timezone.utc)
        data_groups = [
            DataGroup(id=f"dg{i}", name=f"Group{i}", data_type="internal",
                       evidence=_evidence(f"d{i}"))
            for i in range(100)
        ]
        ops = []
        for i in range(400):
            direction = ["input", "output", "query"][i % 3]
            ops.append(Operation(
                id=f"op{i}", name=f"Op{i}", parent_process_id="p1",
                evidence=_evidence(f"e{i}"),
                metadata={"direction": direction},
            ))
        cfm = CanonicalFunctionalModel(
            run_id="perf-large",
            data_groups={g.id: g for g in data_groups},
            operations={o.id: o for o in ops},
            metadata=BuildMetadata(
                run_id="perf-large", build_duration_ms=0, element_counts={},
                total_input_nodes=500, unclassified_count=0, conflicts=[],
                created_at=now,
            ),
        )
        counter = FPACounter()
        result = counter.count(cfm)
        assert result.summary.total_function_count == 500
        assert len(result.warnings) == 0
