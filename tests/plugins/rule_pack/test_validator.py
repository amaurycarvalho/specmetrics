from __future__ import annotations

import pytest
from structlog.testing import capture_logs

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
                Rule(
                    id="r1", type="exclusion", config=RuleConfig(function_types=["EQ"])
                ),
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
                Rule(
                    id="dup", type="exclusion", config=RuleConfig(function_types=["EQ"])
                ),
                Rule(
                    id="dup", type="exclusion", config=RuleConfig(function_types=["EO"])
                ),
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

    def test_loaded_files_recorded(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="r1", type="exclusion", config=RuleConfig(function_types=["EQ"])
                ),
            ],
        )
        load_result = _make_load_result()
        report = self.validator.validate_pack(pack, load_result)
        assert len(report.loaded_files) == 1
        assert report.loaded_files[0] is load_result
        assert report.loaded_files[0].file_path == "test.yml"

    def test_error_status_does_not_record_loaded_file(self) -> None:
        load_result = _make_load_result(status="error", rule_pack_id="")
        load_result.error = "boom"
        report = self.validator.validate_pack(RulePack(id="dummy"), load_result)
        assert report.loaded_files == []
        assert report.total_rules == 0
        assert report.active_rules == 0

    def test_multiple_rules_counted(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="a", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="b", type="exclusion", config=RuleConfig(function_types=["EI"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert report.total_rules == 2
        assert report.active_rules == 2
        assert report.errors == []

    def test_missing_rule_id(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[Rule(id="", type="exclusion", config=RuleConfig(function_types=["EQ"]))],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) == 1
        error = report.errors[0]
        assert error.file_path == "test.yml"
        assert error.message == "Rule is missing required 'id' field"
        assert error.rule_id == ""
        assert error.field == "id"
        assert report.active_rules == 0

    def test_missing_id_skips_duplicate_check(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="", type="exclusion", config=RuleConfig(function_types=["EO"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) == 2
        assert all(e.field == "id" for e in report.errors)

    def test_duplicate_id_after_valid_rule(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="dup", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="dup", type="exclusion", config=RuleConfig(function_types=["EO"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) == 1
        error = report.errors[0]
        assert error.message == "Duplicate rule id 'dup'"
        assert error.rule_id == "dup"
        assert error.field == "id"
        assert report.active_rules == 1

    def test_invalid_weight_override(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="w",
                    type="weight_override",
                    config=RuleConfig(function_type="BOGUS", complexity="Nope", weight=0),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) >= 1
        assert report.active_rules == 0

    def test_invalid_vaf_missing_gsc(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[Rule(id="v", type="vaf", config=RuleConfig(gsc={}))],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) >= 1
        assert report.active_rules == 0

    def test_invalid_vaf_unknown_key(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(
                    id="v",
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
                            "bogus_key": 9,
                        }
                    ),
                ),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert any("unknown GSC" in e.message for e in report.errors)

    def test_invalid_element_exclusion(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[Rule(id="e", type="element_exclusion", config=RuleConfig(element_ids=[]))],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.errors) >= 1
        assert report.active_rules == 0

    def test_conflicting_exclusions_flagged(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="first", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="second", type="exclusion", config=RuleConfig(function_types=["EQ", "EI"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.warnings) == 1
        warning = report.warnings[0]
        assert warning.file_path == "test.yml"
        assert "'EQ'" in warning.message
        assert "'first'" in warning.message
        assert "'second'" in warning.message
        assert warning.rule_id == "second"

    def test_conflicting_exclusions_with_three_rules(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="a", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="b", type="exclusion", config=RuleConfig(function_types=["EQ"])),
                Rule(id="c", type="exclusion", config=RuleConfig(function_types=["EQ"])),
            ],
        )
        report = self.validator.validate_pack(pack, _make_load_result())
        assert len(report.warnings) == 2

    def test_logs_rule_pack_validated_with_details(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="r1", type="exclusion", config=RuleConfig(function_types=["EQ"])),
            ],
        )
        with capture_logs() as captured:
            report = self.validator.validate_pack(pack, _make_load_result())
        assert report.active_rules == 1
        assert captured, "expected a log entry"
        event = captured[-1]
        assert event["event"] == "rule_pack_validated"
        assert event["file"] == "test.yml"
        assert event["rules"] == 1
        assert event["active"] == 1
        assert event["errors"] == 0
        assert event["warnings"] == 0

    def test_no_log_when_no_active_rules(self) -> None:
        load_result = _make_load_result(status="error", rule_pack_id="")
        load_result.error = "boom"
        with capture_logs() as captured:
            self.validator.validate_pack(RulePack(id="dummy"), load_result)
        assert all(e["event"] != "rule_pack_validated" for e in captured)

    def test_no_log_when_rules_invalid(self) -> None:
        pack = RulePack(
            id="test-pack",
            rules=[
                Rule(id="", type="exclusion", config=RuleConfig(function_types=["EQ"])),
            ],
        )
        with capture_logs() as captured:
            self.validator.validate_pack(pack, _make_load_result())
        assert all(e["event"] != "rule_pack_validated" for e in captured)

    def test_unknown_rule_type_rejected_at_validation(self) -> None:
        rule = Rule.model_construct(
            id="r1",
            type="not_a_real_type",
            config=RuleConfig(function_types=["EQ"]),
        )
        errors = self.validator._validate_rule(rule, "test.yml", set())
        assert len(errors) == 1
        error = errors[0]
        assert error.file_path == "test.yml"
        assert error.message == (
            "Unknown rule type 'not_a_real_type'. Must be one of: "
            "complexity_override, element_exclusion, exclusion, vaf, weight_override"
        )
        assert error.rule_id == "r1"
        assert error.field == "type"
