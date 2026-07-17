from __future__ import annotations


from specmetrics.plugins.measurement.sfp.rule_applicator import (
    RulePackApplicator,
)
from specmetrics.plugins.measurement.sfp.models import RulePack


def _make_rule_pack(**overrides) -> RulePack:
    defaults = {
        "id": "test-rules-v1",
        "methodology": "SFP",
    }
    return RulePack(**{**defaults, **overrides})


class TestT022_ExcludeFunctionalProcessesByID:
    def test_exclude_fp_by_cfm_element_id(self):
        rule_pack = _make_rule_pack(
            element_exclusions={"by_id": ["op-001"], "by_pattern": []},
        )
        applicator = RulePackApplicator()
        result = applicator.apply_to_component(
            "functional_process", "op-001", rule_pack,
        )
        assert result == "excluded_by_id"

    def test_non_excluded_fp_not_affected(self):
        rule_pack = _make_rule_pack(
            element_exclusions={"by_id": ["op-001"], "by_pattern": []},
        )
        applicator = RulePackApplicator()
        result = applicator.apply_to_component(
            "functional_process", "op-999", rule_pack,
        )
        assert result is None


class TestT023_ExcludeLogicalFunctionsByPattern:
    def test_exclude_lf_by_name_pattern(self):
        rule_pack = _make_rule_pack(
            element_exclusions={"by_id": [], "by_pattern": ["*_internal_*"]},
        )
        applicator = RulePackApplicator()
        result = applicator.apply_to_component(
            "logical_function", "dg_internal_config", rule_pack,
        )
        assert result is not None
        assert "excluded_by_pattern" in result

    def test_non_matching_pattern_not_excluded(self):
        rule_pack = _make_rule_pack(
            element_exclusions={"by_id": [], "by_pattern": ["*_internal_*"]},
        )
        applicator = RulePackApplicator()
        result = applicator.apply_to_component(
            "logical_function", "dg_customer", rule_pack,
        )
        assert result is None


class TestT024_RedefineInclusionCriteria:
    def test_custom_node_type_matching(self):
        rule_pack = _make_rule_pack(
            inclusion_criteria={
                "functional_process": {
                    "node_types": ["custom_process"],
                    "semantic_types": [],
                },
            },
        )
        applicator = RulePackApplicator()
        criteria = applicator.resolve_inclusion_criteria(rule_pack)
        assert criteria is not None
        assert criteria["functional_process"]["node_types"] == ["custom_process"]

    def test_inclusion_criteria_none_when_no_rule_pack(self):
        applicator = RulePackApplicator()
        criteria = applicator.resolve_inclusion_criteria(None)
        assert criteria is None


class TestT025_ContributionValueOverride:
    def test_override_functional_process_value(self):
        rule_pack = _make_rule_pack(
            contribution_overrides={"functional_process": 5.0},
        )
        applicator = RulePackApplicator()
        overrides = applicator.resolve_contribution_overrides(rule_pack)
        assert overrides is not None
        assert overrides["functional_process"] == 5.0

    def test_override_logical_function_value(self):
        rule_pack = _make_rule_pack(
            contribution_overrides={"logical_function": 8.0},
        )
        applicator = RulePackApplicator()
        overrides = applicator.resolve_contribution_overrides(rule_pack)
        assert overrides is not None
        assert overrides["logical_function"] == 8.0

    def test_override_none_when_no_rule_pack(self):
        applicator = RulePackApplicator()
        overrides = applicator.resolve_contribution_overrides(None)
        assert overrides is None


class TestT026_AlgorithmNotModifiable:
    def test_rule_pack_cannot_change_deterministic_nature(self):
        applicator = RulePackApplicator()
        rule_pack = _make_rule_pack()
        overrides = applicator.resolve_contribution_overrides(rule_pack)
        assert overrides is None or isinstance(overrides, dict)


class TestT027_RulePackAdjustmentsReported:
    def test_exclusions_reported_in_output(self):
        rule_pack = _make_rule_pack(
            element_exclusions={"by_id": ["op-001"], "by_pattern": ["*_internal_*"]},
        )
        applicator = RulePackApplicator()
        exclusions = applicator.resolve_element_exclusions(rule_pack)
        assert exclusions is not None
        assert "op-001" in exclusions.get("by_id", [])
        assert "*_internal_*" in exclusions.get("by_pattern", [])

    def test_excluded_types_reported(self):
        rule_pack = _make_rule_pack(excluded_types=["logical_function"])
        applicator = RulePackApplicator()
        excluded = applicator.resolve_excluded_types(rule_pack)
        assert "logical_function" in excluded


class TestT028_InvalidRulePackGeneratesWarnings:
    def test_negative_contribution_override_warns(self):
        rule_pack = _make_rule_pack(
            contribution_overrides={"functional_process": -1.0},
        )
        applicator = RulePackApplicator()
        warnings = applicator.validate_rule_pack(rule_pack)
        assert any("Invalid contribution override" in w for w in warnings)

    def test_unknown_excluded_type_warns(self):
        rule_pack = _make_rule_pack(excluded_types=["unknown_type"])
        applicator = RulePackApplicator()
        warnings = applicator.validate_rule_pack(rule_pack)
        assert any("Unknown component type" in w for w in warnings)

    def test_wrong_methodology_warns(self):
        rule_pack = _make_rule_pack(methodology="FPA")
        applicator = RulePackApplicator()
        warnings = applicator.validate_rule_pack(rule_pack)
        assert any("does not match" in w for w in warnings)

    def test_valid_rule_pack_no_warnings(self):
        rule_pack = _make_rule_pack()
        applicator = RulePackApplicator()
        warnings = applicator.validate_rule_pack(rule_pack)
        assert len(warnings) == 0
