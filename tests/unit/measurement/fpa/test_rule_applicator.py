import pytest

from specmetrics.plugins.measurement.fpa.models import RulePack
from specmetrics.plugins.measurement.fpa.rule_applicator import RulePackApplicator


@pytest.fixture
def applicator():
    return RulePackApplicator()


class TestRulePackParsingDefaults:
    def test_none_rule_pack_returns_defaults(self, applicator):
        assert applicator.resolve_weights(None) is None
        assert applicator.resolve_excluded_types(None) == []
        assert applicator.resolve_complexity_overrides(None) is None
        assert applicator.compute_vaf(None) is None

    def test_empty_rule_pack_returns_defaults(self, applicator):
        rp = RulePack(id="empty")
        assert applicator.resolve_weights(rp) is None
        assert applicator.resolve_excluded_types(rp) == []


class TestFunctionTypeExclusion:
    def test_exclude_eq(self, applicator):
        rp = RulePack(id="no-eq", excluded_types=["EQ"])
        excluded = applicator.resolve_excluded_types(rp)
        assert "EQ" in excluded
        assert "ILF" not in excluded

    def test_exclude_multiple_types(self, applicator):
        rp = RulePack(id="no-eq-eif", excluded_types=["EQ", "EIF"])
        excluded = applicator.resolve_excluded_types(rp)
        assert set(excluded) == {"EQ", "EIF"}


class TestWeightOverrides:
    def test_partial_weight_override(self, applicator):
        rp = RulePack(
            id="custom-weight",
            weight_overrides={"ILF": {"Low": 99}},
        )
        weights = applicator.resolve_weights(rp)
        assert weights is not None
        assert weights["ILF"]["Low"] == 99  # overridden
        assert weights["ILF"]["Average"] == 10  # default preserved

    def test_weight_override_all_types(self, applicator):
        rp = RulePack(
            id="all-weights",
            weight_overrides={
                "ILF": {"Low": 1, "Average": 2, "High": 3},
                "EI": {"Low": 4, "Average": 5, "High": 6},
            },
        )
        weights = applicator.resolve_weights(rp)
        assert weights["ILF"]["Low"] == 1
        assert weights["EI"]["High"] == 6
        assert weights["EIF"]["Low"] == 5  # unchanged default

    def test_weight_override_preserves_other_types(self, applicator):
        rp = RulePack(id="single-type", weight_overrides={"EO": {"Low": 99}})
        weights = applicator.resolve_weights(rp)
        assert weights["EQ"]["Low"] == 3  # default
        assert weights["EO"]["Low"] == 99  # overridden


class TestVAF:
    def test_compute_vaf_minimum(self, applicator):
        rp = RulePack(id="min-vaf", vaf={})
        vaf = applicator.compute_vaf(rp)
        assert vaf == 0.65

    def test_compute_vaf_mid_range(self, applicator):
        rp = RulePack(
            id="mid-vaf",
            vaf={"data_communications": 3, "performance": 2, "online_data": 3},
        )
        vaf = applicator.compute_vaf(rp)
        total = 3 + 2 + 3
        assert vaf == 0.65 + (0.01 * total)

    def test_compute_vaf_maximum(self, applicator):
        all_5 = {f"gsc_{i}": 5 for i in range(14)}
        total = 14 * 5
        rp = RulePack(id="max-vaf", vaf=all_5)
        vaf = applicator.compute_vaf(rp)
        assert vaf == 0.65 + (0.01 * total)


class TestElementExclusions:
    def test_exclude_by_id(self, applicator):
        rp = RulePack(
            id="exclude-element",
            element_exclusions={"by_id": ["dg_17"], "by_pattern": []},
        )
        result = applicator.apply_to_function("ILF", "dg_17", rp)
        assert result == "excluded_by_id"

    def test_no_exclusion_for_non_matching(self, applicator):
        rp = RulePack(
            id="exclude-element",
            element_exclusions={"by_id": ["dg_17"], "by_pattern": []},
        )
        result = applicator.apply_to_function("ILF", "dg_99", rp)
        assert result is None
