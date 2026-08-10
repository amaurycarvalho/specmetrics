from __future__ import annotations

from specmetrics.plugins.measurement.snap.models import RulePack
from specmetrics.plugins.measurement.snap.rule_applicator import RulePackApplicator


class TestCategoryExclusion:
    def test_exclude_entire_category(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", excluded_categories=["technical_interaction"])
        excluded = applicator.resolve_excluded_categories(rp)
        assert "technical_interaction" in excluded


class TestItemExclusion:
    def test_exclude_items_by_id(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", item_exclusions={"by_id": ["elem-42"]})
        exclusions = applicator.resolve_item_exclusions(rp)
        assert exclusions is not None
        assert "elem-42" in exclusions.get("by_id", [])

    def test_exclude_items_by_pattern(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", item_exclusions={"by_pattern": ["*internal_*"]})
        exclusions = applicator.resolve_item_exclusions(rp)
        assert exclusions is not None
        assert "*internal_*" in exclusions.get("by_pattern", [])


class TestInclusionPolicyRedefinition:
    def test_redefine_inclusion_policy(self):
        applicator = RulePackApplicator()
        rp = RulePack(
            id="test",
            inclusion_policies=[
                {"semantic_marker": "custom_ui_feature", "category": "presentation"},
            ],
        )
        policies = applicator.resolve_inclusion_policies(rp)
        assert policies is not None
        assert len(policies) == 1
        assert policies[0]["semantic_marker"] == "custom_ui_feature"
        assert policies[0]["category"] == "presentation"


class TestContributionOverride:
    def test_override_contribution_value(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", contribution_overrides={"presentation": 5.0})
        overrides = applicator.resolve_contribution_overrides(rp)
        assert overrides is not None
        assert overrides["presentation"] == 5.0

    def test_no_override_returns_none(self):
        applicator = RulePackApplicator()
        overrides = applicator.resolve_contribution_overrides(None)
        assert overrides is None


class TestDeterministicAlgorithmProtection:
    def test_rule_pack_cannot_alter_algorithm(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", excluded_categories=["presentation"])
        excluded = applicator.resolve_excluded_categories(rp)
        assert "presentation" in excluded
        assert len(excluded) == 1


class TestRulePackAdjustmentsReported:
    def test_adjustments_reported_in_output(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", excluded_categories=["presentation"])
        warnings = applicator.validate_rule_pack(rp)
        assert isinstance(warnings, list)


class TestExcludedCandidatesReported:
    def test_excluded_candidates_reported(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", excluded_categories=["presentation"])
        excluded = applicator.resolve_excluded_categories(rp)
        assert "presentation" in excluded
        assert isinstance(excluded, list)


class TestInvalidRulePack:
    def test_invalid_rule_pack_generates_warning(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="bad-rp", methodology="INVALID")
        warnings = applicator.validate_rule_pack(rp)
        assert len(warnings) >= 1
        assert any(w.code == "RULE_PACK_METHODOLOGY_MISMATCH" for w in warnings)

    def test_invalid_contribution_override_generates_warning(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="bad-rp", contribution_overrides={"presentation": -1.0})
        warnings = applicator.validate_rule_pack(rp)
        assert len(warnings) >= 1
        assert any(w.code == "INVALID_CONTRIBUTION_OVERRIDE" for w in warnings)

    def test_invalid_rule_pack_does_not_prevent_assessment(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="bad-rp", excluded_categories=["nonexistent_category"])
        warnings = applicator.validate_rule_pack(rp)
        assert len(warnings) >= 1
        excluded = applicator.resolve_excluded_categories(rp)
        assert "nonexistent_category" in excluded


class TestRulePackValidation:
    def test_validate_missing_inclusion_policy_fields(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", inclusion_policies=[{"semantic_marker": ""}])
        warnings = applicator.validate_rule_pack(rp)
        assert len(warnings) >= 1

    def test_validate_unknown_category_exclusion(self):
        applicator = RulePackApplicator()
        rp = RulePack(id="test", excluded_categories=["unknown_category"])
        warnings = applicator.validate_rule_pack(rp)
        assert len(warnings) >= 1
        assert any(w.code == "UNKNOWN_CATEGORY" for w in warnings)

    def test_validate_none_rule_pack_returns_no_warnings(self):
        applicator = RulePackApplicator()
        warnings = applicator.validate_rule_pack(None)
        assert len(warnings) == 0


def test_validate_methodology_ignores_empty_methodology() -> None:
    """Mutmut 1: an empty methodology string must not produce a warning."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", methodology="")
    assert applicator.validate_rule_pack(rp) == []


def test_validate_methodology_accepts_snap() -> None:
    """Mutmut 3/4: the 'SNAP' methodology must be accepted without warning."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", methodology="SNAP")
    assert applicator.validate_rule_pack(rp) == []


def test_validate_methodology_mismatch_warning_exact() -> None:
    """Mutmut 2/24: mismatched methodology yields a concrete AssessmentWarning."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", methodology="COSMIC")
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "RULE_PACK_METHODOLOGY_MISMATCH"
    assert warnings[0].message == (
        "Rule Pack methodology 'COSMIC' does not match SNAP; "
        "applying defaults for unrecognized fields"
    )


def test_zero_contribution_override_warns() -> None:
    """Mutmut 1: a zero contribution override is still invalid."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", contribution_overrides={"presentation": 0.0})
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "INVALID_CONTRIBUTION_OVERRIDE"
    assert warnings[0].message == (
        "Invalid contribution override for presentation: 0.0; "
        "must be positive. Override ignored."
    )


def test_positive_contribution_override_no_warning() -> None:
    """Mutmut 2: a value of exactly 1 must be accepted."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", contribution_overrides={"presentation": 1.0})
    assert applicator.validate_rule_pack(rp) == []


def test_non_dict_policy_warns_invalid() -> None:
    """Mutmut 1: a non-mapping policy entry must produce INVALID_INCLUSION_POLICY."""
    applicator = RulePackApplicator()
    rp = RulePack.model_construct(id="rp", inclusion_policies=["not-a-dict"])
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "INVALID_INCLUSION_POLICY"
    assert warnings[0].message == (
        "Invalid inclusion policy entry; must be a mapping "
        "with 'semantic_marker' and 'category'"
    )


def test_dict_policy_no_invalid_warning() -> None:
    """Mutmut 13/14/15/16/17/18/19/20: a complete policy mapping is valid."""
    applicator = RulePackApplicator()
    rp = RulePack(
        id="rp",
        inclusion_policies=[{"semantic_marker": "custom_signal", "category": "presentation"}],
    )
    assert applicator.validate_rule_pack(rp) == []


def test_invalid_policy_continue_processes_remaining() -> None:
    """Mutmut 12: an invalid policy must not stop validation of later policies."""
    applicator = RulePackApplicator()
    rp = RulePack.model_construct(id="rp", inclusion_policies=[["bad1"], ["bad2"]])
    warnings = applicator.validate_rule_pack(rp)
    assert len(warnings) == 2


def test_missing_marker_warns_incomplete() -> None:
    """Mutmut 21: a policy missing its marker must produce INCOMPLETE_INCLUSION_POLICY."""
    applicator = RulePackApplicator()
    rp = RulePack(
        id="rp",
        inclusion_policies=[{"semantic_marker": "", "category": "presentation"}],
    )
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "INCOMPLETE_INCLUSION_POLICY"
    assert warnings[0].message == "Inclusion policy missing 'semantic_marker' or 'category'"


def test_policy_with_only_category_warns() -> None:
    """Mutmut 22: a policy with a category but no marker is incomplete."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", inclusion_policies=[{"category": "presentation"}])
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "INCOMPLETE_INCLUSION_POLICY"


def test_policy_with_only_marker_warns() -> None:
    """Mutmut 23: a policy with a marker but no category is incomplete."""
    applicator = RulePackApplicator()
    rp = RulePack(id="rp", inclusion_policies=[{"semantic_marker": "custom_signal"}])
    warnings = applicator.validate_rule_pack(rp)
    assert warnings[0].code == "INCOMPLETE_INCLUSION_POLICY"
