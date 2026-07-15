from __future__ import annotations

from datetime import datetime, timezone

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.kernel.cfm.models import Rule, RuleConfig, RulePack
from specmetrics.plugins.rule_pack.applicator import RuleApplicator


def _make_cfm(
    processes: dict[str, dict] | None = None,
) -> CanonicalFunctionalModel:
    if processes is None:
        processes = {
            "fp-001": {"name": "User Login"},
            "fp-002": {"name": "Generate Report"},
            "fp-003": {"name": "Search Records"},
        }
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(timezone.utc),
    )
    return CanonicalFunctionalModel(
        run_id="test-run",
        functional_processes={
            pid: FunctionalProcess(
                id=pid,
                name=props["name"],
                evidence=EvidenceRef(
                    graph_node_id=f"n-{pid}",
                    document_id="doc-1",
                    text=f"Process {props['name']}",
                ),
                metadata={"function_type": props.get("function_type", "EI")},
            )
            for pid, props in processes.items()
        },
        metadata=metadata,
    )


class TestRuleApplicator:
    def setup_method(self) -> None:
        self.applicator = RuleApplicator()

    def test_no_rules_passes_through(self) -> None:
        cfm = _make_cfm()
        result = self.applicator.apply(cfm, [])
        assert result == cfm
        assert len(self.applicator.applied_records) == 0

    def test_exclusion_rule_marks_functions(self) -> None:
        cfm = _make_cfm({
            "fp-001": {"name": "Inquiry", "function_type": "EQ"},
            "fp-002": {"name": "Input", "function_type": "EI"},
        })
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="exclude-eq",
                    type="exclusion",
                    config=RuleConfig(function_types=["EQ"]),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        fp001 = result.functional_processes["fp-001"]
        assert fp001.metadata.get("excluded") is True
        assert "EQ" in fp001.metadata.get("excluded_by", "")
        fp002 = result.functional_processes["fp-002"]
        assert fp002.metadata.get("excluded") is not True

    def test_element_exclusion(self) -> None:
        cfm = _make_cfm()
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="exclude-fp001",
                    type="element_exclusion",
                    config=RuleConfig(element_ids=["fp-001"]),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        assert result.functional_processes["fp-001"].metadata.get("excluded") is True
        assert result.functional_processes["fp-002"].metadata.get("excluded") is not True

    def test_vaf_computation(self) -> None:
        cfm = _make_cfm()
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="vaf-rule",
                    type="vaf",
                    config=RuleConfig(
                        gsc={
                            "data_communications": 3,
                            "distributed_data_processing": 2,
                            "performance": 4,
                            "heavily_used_configuration": 3,
                            "transaction_rate": 3,
                            "online_data_entry": 4,
                            "end_user_efficiency": 3,
                            "online_update": 3,
                            "complex_processing": 2,
                            "reusability": 2,
                            "installation_ease": 2,
                            "operational_ease": 3,
                            "multiple_sites": 1,
                            "facilitate_change": 2,
                        },
                    ),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        assert result.metadata.vaf is not None
        assert isinstance(result.metadata.vaf, float)

    def test_complexity_override(self) -> None:
        cfm = _make_cfm({
            "fp-001": {"name": "Input", "function_type": "EI"},
        })
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="comp-override",
                    type="complexity_override",
                    config=RuleConfig(
                        function_type="EI",
                        thresholds={"det": [2, 8], "ftr": [1, 2]},
                    ),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        fp001 = result.functional_processes["fp-001"]
        assert fp001.metadata.get("complexity_source") == "rule_pack_override"

    def test_weight_override(self) -> None:
        cfm = _make_cfm({
            "fp-001": {"name": "Input", "function_type": "EI"},
        })
        fp001 = cfm.functional_processes["fp-001"]
        fp001 = fp001.model_copy(update={
            "metadata": {
                **fp001.metadata,
                "function_type": "EI",
                "complexity_rating": "High",
            }
        })
        cfm = cfm.model_copy(update={"functional_processes": {"fp-001": fp001}})

        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="weight-override",
                    type="weight_override",
                    config=RuleConfig(
                        function_type="EI",
                        complexity="High",
                        weight=5,
                    ),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        fp001_result = result.functional_processes["fp-001"]
        assert fp001_result.metadata.get("weight_source") == "rule_pack_override"
        assert fp001_result.metadata.get("ufp_weight") == 5

    def test_applied_records_created(self) -> None:
        cfm = _make_cfm()
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="exclude-eq",
                    type="exclusion",
                    config=RuleConfig(function_types=["EQ"]),
                ),
            ],
        )
        self.applicator.apply(cfm, [pack])
        assert len(self.applicator.applied_records) == 1
        record = self.applicator.applied_records[0]
        assert record.rule_pack_id == "test-pack"
        assert record.rule_id == "exclude-eq"
        assert record.rule_type == "exclusion"

    def test_multiple_rule_types(self) -> None:
        cfm = _make_cfm()
        pack = RulePack(
            id="multi-pack",
            rules=[
                Rule(id="ex-eq", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(
                    id="comp-ei",
                    type="complexity_override",
                    config=RuleConfig(function_type="EI", thresholds={"det": [1, 5]}),
                ),
                Rule(
                    id="vaf-default",
                    type="vaf",
                    config=RuleConfig(
                        gsc={k: 2 for k in [
                            "data_communications", "distributed_data_processing",
                            "performance", "heavily_used_configuration",
                            "transaction_rate", "online_data_entry",
                            "end_user_efficiency", "online_update",
                            "complex_processing", "reusability",
                            "installation_ease", "operational_ease",
                            "multiple_sites", "facilitate_change",
                        ]}
                    ),
                ),
            ],
        )
        result = self.applicator.apply(cfm, [pack])
        assert len(self.applicator.applied_records) == 3
        assert result.metadata.vaf == 0.93  # 0.65 + 0.01 * 28
