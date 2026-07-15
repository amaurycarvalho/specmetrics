from datetime import datetime, timezone

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.plugins.measurement.apf.counter import APFCounter
from specmetrics.plugins.measurement.apf.models import RulePack
from specmetrics.plugins.measurement.apf.plugin import APFMeasurementPlugin


def _evidence(text: str = "src") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="n1",
        document_id="doc1",
        section_id="s1",
        text=text,
    )


def _make_cfm() -> CanonicalFunctionalModel:
    now = datetime.now(timezone.utc)
    return CanonicalFunctionalModel(
        run_id="integ-test-run",
        data_groups={
            "dg1": DataGroup(id="dg1", name="Orders", data_type="internal", evidence=_evidence("order data")),
            "dg2": DataGroup(id="dg2", name="Products", data_type="internal", evidence=_evidence("product data")),
            "dg3": DataGroup(id="dg3", name="TaxService", data_type="external", evidence=_evidence("tax api")),
        },
        operations={
            "op1": Operation(id="op1", name="CreateOrder", parent_process_id="p1",
                            evidence=_evidence("create order flow"),
                            metadata={"direction": "input"}),
            "op2": Operation(id="op2", name="PrintInvoice", parent_process_id="p1",
                            evidence=_evidence("invoice output"),
                            metadata={"direction": "output"}),
            "op3": Operation(id="op3", name="CheckPrice", parent_process_id="p1",
                            evidence=_evidence("price lookup"),
                            metadata={"direction": "query"}),
        },
        metadata=BuildMetadata(
            run_id="integ-test-run",
            build_duration_ms=100,
            element_counts={"data_groups": 3, "operations": 3},
            total_input_nodes=6,
            unclassified_count=0,
            conflicts=[],
            created_at=now,
        ),
    )


class TestFullMeasurement:
    def test_basic_apf_count(self):
        cfm = _make_cfm()
        counter = APFCounter()
        result = counter.count(cfm)

        assert result.summary.total_function_count == 6
        assert result.summary.total_ufp > 0

        by_type = result.summary.by_type
        assert by_type["ILF"].count == 2  # Orders, Products
        assert by_type["EIF"].count == 1  # TaxService
        assert by_type["EI"].count == 1   # CreateOrder
        assert by_type["EO"].count == 1   # PrintInvoice
        assert by_type["EQ"].count == 1   # CheckPrice

        assert len(result.measured_functions) == 6

    def test_all_functions_have_evidence(self):
        cfm = _make_cfm()
        counter = APFCounter()
        result = counter.count(cfm)

        for fn in result.measured_functions:
            assert len(fn.evidence_refs) > 0, f"Function {fn.id} missing evidence"
            assert fn.evidence_refs[0].graph_node_id is not None

    def test_determinism(self):
        cfm = _make_cfm()
        counter = APFCounter()

        result_a = counter.count(cfm)
        result_b = counter.count(cfm)

        json_a = result_a.model_dump_json()
        json_b = result_b.model_dump_json()

        # Only compare fields that should be deterministic
        assert result_a.summary.model_dump() == result_b.summary.model_dump()
        assert len(result_a.measured_functions) == len(result_b.measured_functions)

    def test_empty_cfm(self):
        now = datetime.now(timezone.utc)
        empty_cfm = CanonicalFunctionalModel(
            run_id="empty-run",
            metadata=BuildMetadata(
                run_id="empty-run", build_duration_ms=0, element_counts={},
                total_input_nodes=0, unclassified_count=0, conflicts=[],
                created_at=now,
            ),
        )
        counter = APFCounter()
        result = counter.count(empty_cfm)
        assert result.summary.total_function_count == 0
        assert result.summary.total_ufp == 0

    def test_rule_pack_excludes_eq(self):
        cfm = _make_cfm()
        plugin = APFMeasurementPlugin()
        rule_pack = RulePack(id="no-eq", excluded_types=["EQ"])

        result_default = plugin.measure(cfm)
        result_custom = plugin.measure(cfm, rule_pack)

        eq_default = [f for f in result_default.measured_functions if f.function_type == "EQ"]
        eq_custom = [f for f in result_custom.measured_functions if f.function_type == "EQ"]

        assert len(eq_default) > 0
        assert len(eq_custom) == 0

    def test_rule_pack_weight_override(self):
        cfm = _make_cfm()
        plugin = APFMeasurementPlugin()
        rule_pack = RulePack(
            id="half-weight",
            weight_overrides={"ILF": {"Low": 1, "Average": 1, "High": 1}},
        )

        result_default = plugin.measure(cfm)
        result_custom = plugin.measure(cfm, rule_pack)

        ilf_default = sum(f.ufp_weight for f in result_default.measured_functions if f.function_type == "ILF")
        ilf_custom = sum(f.ufp_weight for f in result_custom.measured_functions if f.function_type == "ILF")

        # With 2 ILFs at weight 1 each, should be 2
        assert ilf_custom == 2
        # Default ILF weights (7 or 10) should be higher
        assert ilf_default > ilf_custom

    def test_plugin_discovery(self):
        from importlib.metadata import entry_points
        eps = entry_points(group="specmetrics.plugins.measurement")
        names = [ep.name for ep in eps]
        assert "apf" in names

    def test_plugin_explanations(self):
        cfm = _make_cfm()
        plugin = APFMeasurementPlugin()
        result = plugin.measure(cfm)

        for fn in result.measured_functions:
            assert len(fn.evidence_refs) > 0

        assert len(result.explanations) == len(result.measured_functions)
        for exp in result.explanations:
            assert exp.classification_reason
            assert exp.complexity_reason
            assert len(exp.evidence_chain) > 0
