from __future__ import annotations

from datetime import UTC, datetime

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
)
from specmetrics.plugins.rule_pack.annotator import RuleAnnotator


def _make_cfm() -> CanonicalFunctionalModel:
    metadata = BuildMetadata(
        run_id="test-run",
        created_at=datetime.now(UTC),
    )
    return CanonicalFunctionalModel(
        run_id="test-run",
        functional_processes={
            "fp-001": FunctionalProcess(
                id="fp-001",
                name="User Login",
                evidence=EvidenceRef(
                    graph_node_id="n-fp-001",
                    document_id="doc-1",
                    text="Process User Login",
                ),
                metadata={"function_type": "EI"},
            ),
        },
        metadata=metadata,
    )


class TestRuleAnnotator:
    def setup_method(self) -> None:
        self.annotator = RuleAnnotator()

    def test_records_initialized_empty(self) -> None:
        assert self.annotator.records == []
        self.annotator.clear()
        assert self.annotator.records == []

    def test_record_application_defaults(self) -> None:
        record = self.annotator.record_application(
            rule_pack_id="pack-1",
            rule_id="rule-1",
            rule_type="exclusion",
            description="Exclude EQ functions",
        )
        assert record.rule_pack_id == "pack-1"
        assert record.rule_id == "rule-1"
        assert record.rule_type == "exclusion"
        assert record.description == "Exclude EQ functions"
        assert record.methodology == ""
        assert record.before_state == {}
        assert record.after_state == {}
        assert self.annotator.records == [record]
        assert self.annotator.records[0] is record

    def test_record_application_full(self) -> None:
        record = self.annotator.record_application(
            rule_pack_id="pack-2",
            rule_id="rule-2",
            rule_type="vaf",
            description="VAF",
            methodology="IFPUG",
            before_state={"fp-001": {"ufp_weight": 0}},
            after_state={"fp-001": {"ufp_weight": 5}},
        )
        assert record.methodology == "IFPUG"
        assert record.before_state == {"fp-001": {"ufp_weight": 0}}
        assert record.after_state == {"fp-001": {"ufp_weight": 5}}
        assert record.rule_pack_id == "pack-2"

    def test_record_default_rules(self) -> None:
        record = self.annotator.record_default_rules()
        assert record.rule_pack_id == ""
        assert record.rule_id == ""
        assert record.rule_type == "default"
        assert record.description == (
            "No Rule Pack files found. Default IFPUG rules applied."
        )
        assert len(self.annotator.records) == 1

    def test_clear_resets_records(self) -> None:
        self.annotator.record_default_rules()
        assert len(self.annotator.records) == 1
        self.annotator.clear()
        assert self.annotator.records == []

    def test_annotate_cfm_adds_applied_rules(self) -> None:
        cfm = _make_cfm()
        self.annotator.record_default_rules()
        result = self.annotator.annotate_cfm(cfm)
        assert result is not cfm
        assert result.metadata.applied_rules == [
            {
                "rule_pack_id": "",
                "rule_id": "",
                "rule_type": "default",
                "description": "No Rule Pack files found. Default IFPUG rules applied.",
                "methodology": "",
                "before_state": {},
                "after_state": {},
            }
        ]

    def test_annotate_cfm_adds_glossary_overrides(self) -> None:
        cfm = _make_cfm()
        result = self.annotator.annotate_cfm(cfm, glossary_overrides={"cadeira": "chair"})
        assert result.metadata.glossary_overrides == {"cadeira": "chair"}

    def test_annotate_cfm_no_records(self) -> None:
        cfm = _make_cfm()
        result = self.annotator.annotate_cfm(cfm)
        assert result.metadata.applied_rules == []