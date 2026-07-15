from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.models import FileLoadResult, Rule, RuleConfig, RulePack
from specmetrics.plugins.rule_pack.validator import RulePackValidator


def _make_load_result(
    file_path: str = "test.yml",
    status: str = "loaded",
    rule_pack_id: str = "test-pack",
) -> FileLoadResult:
    return FileLoadResult(
        file_path=file_path,
        status=status,
        rule_pack_id=rule_pack_id,
    )


class TestRulePackValidator:
    def setup_method(self) -> None:
        self.validator = RulePackValidator()

    def test_valid_exclusion_rule(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="r1", type="exclusion", config=RuleConfig(function_types=["EQ"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.total_rules == 1
        assert report.active_rules == 1
        assert len(report.errors) == 0

    def test_valid_complexity_override(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="complexity_override",
                    config=RuleConfig(
                        function_type="EI",
                        thresholds={"det": [2, 8], "ftr": [1, 2]},
                    ),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.active_rules == 1

    def test_valid_weight_override(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="weight_override",
                    config=RuleConfig(function_type="EI", complexity="High", weight=5),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.active_rules == 1

    def test_valid_vaf_rule(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="vaf",
                    config=RuleConfig(
                        gsc={
                            "data_communications": 2,
                            "distributed_data_processing": 2,
                            "performance": 2,
                            "heavily_used_configuration": 2,
                            "transaction_rate": 2,
                            "online_data_entry": 2,
                            "end_user_efficiency": 2,
                            "online_update": 2,
                            "complex_processing": 2,
                            "reusability": 2,
                            "installation_ease": 2,
                            "operational_ease": 2,
                            "multiple_sites": 2,
                            "facilitate_change": 2,
                        },
                    ),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.active_rules == 1

    def test_valid_element_exclusion(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="element_exclusion",
                    config=RuleConfig(element_ids=["fp-001", "fp-042"]),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.active_rules == 1

    def test_unknown_rule_type_rejected_by_pydantic(self) -> None:
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Rule(id="r1", type="unknown_type", config=RuleConfig())

    def test_duplicate_rule_ids(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="dup", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="dup", type="exclusion", config=RuleConfig(function_types=["EO"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) == 1
        assert "Duplicate" in report.errors[0].message

    def test_unknown_function_type_in_exclusion(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="exclusion",
                    config=RuleConfig(function_types=["UNKNOWN"]),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) == 1
        assert "UNKNOWN" in report.errors[0].message

    def test_invalid_threshold_bounds(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="complexity_override",
                    config=RuleConfig(
                        function_type="EI",
                        thresholds={"det": [10, 5]},
                    ),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) >= 1

    def test_missing_function_type_in_override(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1",
                    type="complexity_override",
                    config=RuleConfig(thresholds={"det": [1, 5]}),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) >= 1

    def test_error_status_from_loader(self) -> None:
        load_result = _make_load_result(status="error", rule_pack_id="")
        load_result.error = "Invalid YAML: syntax error"
        pack = RulePack(id="dummy")
        report = self.validator.validate_pack(pack, load_result)
        assert len(report.errors) == 1
        assert "Invalid YAML" in report.errors[0].message
