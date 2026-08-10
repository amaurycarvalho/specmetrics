from __future__ import annotations

from specmetrics.kernel.cfm.models import Rule, RuleConfig, ValidationError
from specmetrics.plugins.rule_pack._validators import (
    validate_complexity_override_config,
    validate_element_exclusion_config,
    validate_exclusion_config,
    validate_gsc,
    validate_threshold,
    validate_vaf_config,
    validate_weight_override_config,
)

FP = "rules.yml"

GSC_KEYS = {
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
}

GSC_SET = set(GSC_KEYS)


def _rule(config: RuleConfig, rule_type: str = "exclusion") -> Rule:
    return Rule(id="r1", type=rule_type, config=config)


def _assert_error(
    errors: list[ValidationError], message: str, field: str
) -> None:
    assert len(errors) == 1
    err = errors[0]
    assert err.file_path == FP
    assert err.rule_id == "r1"
    assert err.message == message
    assert err.field == field


class TestExclusionConfig:
    def test_missing_function_types(self) -> None:
        _assert_error(
            validate_exclusion_config(_rule(RuleConfig()), FP),
            "Exclusion rule requires non-empty 'function_types' list",
            "config.function_types",
        )

    def test_non_list_function_types(self) -> None:
        config = RuleConfig.model_construct(function_types="EQ")
        _assert_error(
            validate_exclusion_config(_rule(config), FP),
            "Exclusion rule requires non-empty 'function_types' list",
            "config.function_types",
        )

    def test_empty_function_types(self) -> None:
        _assert_error(
            validate_exclusion_config(_rule(RuleConfig(function_types=[])), FP),
            "Exclusion rule requires non-empty 'function_types' list",
            "config.function_types",
        )

    def test_unknown_function_type(self) -> None:
        _assert_error(
            validate_exclusion_config(
                _rule(RuleConfig(function_types=["NOPE"])), FP
            ),
            "Unknown function type 'NOPE' in exclusion rule. Must be one of: "
            "EI, EIF, EO, EQ, ILF",
            "config.function_types",
        )

    def test_unknown_function_types_reported_per_item(self) -> None:
        errors = validate_exclusion_config(
            _rule(RuleConfig(function_types=["NOPE", "BAD"])), FP
        )
        assert len(errors) == 2
        assert all(e.rule_id == "r1" and e.file_path == FP for e in errors)

    def test_valid_function_types(self) -> None:
        assert (
            validate_exclusion_config(
                _rule(RuleConfig(function_types=["EI", "EQ", "ILF"])), FP
            )
            == []
        )


class TestComplexityOverrideConfig:
    def test_missing_function_type(self) -> None:
        _assert_error(
            validate_complexity_override_config(
                _rule(RuleConfig(thresholds={"det": [1, 5]}), "complexity_override"),
                FP,
            ),
            "Complexity override requires valid 'function_type'. Got 'None'",
            "config.function_type",
        )

    def test_invalid_function_type(self) -> None:
        _assert_error(
            validate_complexity_override_config(
                _rule(
                    RuleConfig(function_type="BOGUS", thresholds={"det": [1, 5]}),
                    "complexity_override",
                ),
                FP,
            ),
            "Complexity override requires valid 'function_type'. Got 'BOGUS'",
            "config.function_type",
        )

    def test_missing_thresholds(self) -> None:
        _assert_error(
            validate_complexity_override_config(
                _rule(RuleConfig(function_type="EI"), "complexity_override"), FP
            ),
            "Complexity override requires 'thresholds' with det/ftr or ret bounds",
            "config.thresholds",
        )

    def test_thresholds_not_dict(self) -> None:
        config = RuleConfig.model_construct(
            function_type="EI", thresholds="det:[1,5]"
        )
        _assert_error(
            validate_complexity_override_config(
                _rule(config, "complexity_override"), FP
            ),
            "Complexity override requires 'thresholds' with det/ftr or ret bounds",
            "config.thresholds",
        )

    def test_each_threshold_key_validated(self) -> None:
        errors = validate_complexity_override_config(
            _rule(
                RuleConfig(
                    function_type="EI",
                    thresholds={"det": [9, 5], "ret": [9, 5], "ftr": [9, 5]},
                ),
                "complexity_override",
            ),
            FP,
        )
        assert len(errors) == 3
        assert all(e.rule_id == "r1" and e.file_path == FP for e in errors)

    def test_valid_thresholds(self) -> None:
        assert (
            validate_complexity_override_config(
                _rule(
                    RuleConfig(
                        function_type="EI",
                        thresholds={"det": [1, 5], "ret": [2, 6], "ftr": [3, 7]},
                    ),
                    "complexity_override",
                ),
                FP,
            )
            == []
        )


class TestWeightOverrideConfig:
    def test_missing_function_type(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(
                    RuleConfig(complexity="High", weight=5), "weight_override"
                ),
                FP,
            ),
            "Weight override requires valid 'function_type'. Got 'None'",
            "config.function_type",
        )

    def test_invalid_function_type(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(
                    RuleConfig(function_type="X", complexity="High", weight=5),
                    "weight_override",
                ),
                FP,
            ),
            "Weight override requires valid 'function_type'. Got 'X'",
            "config.function_type",
        )

    def test_missing_complexity(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(RuleConfig(function_type="EI", weight=5), "weight_override"), FP
            ),
            "Weight override requires valid 'complexity' (Low/Average/High). Got 'None'",
            "config.complexity",
        )

    def test_invalid_complexity(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(
                    RuleConfig(function_type="EI", complexity="Huge", weight=5),
                    "weight_override",
                ),
                FP,
            ),
            "Weight override requires valid 'complexity' (Low/Average/High). Got 'Huge'",
            "config.complexity",
        )

    def test_missing_weight(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(
                    RuleConfig(function_type="EI", complexity="High"),
                    "weight_override",
                ),
                FP,
            ),
            "Weight override requires positive integer 'weight'. Got None",
            "config.weight",
        )

    def test_zero_weight(self) -> None:
        _assert_error(
            validate_weight_override_config(
                _rule(
                    RuleConfig(function_type="EI", complexity="High", weight=0),
                    "weight_override",
                ),
                FP,
            ),
            "Weight override requires positive integer 'weight'. Got 0",
            "config.weight",
        )

    def test_weight_of_one_is_valid(self) -> None:
        assert (
            validate_weight_override_config(
                _rule(
                    RuleConfig(function_type="EI", complexity="High", weight=1),
                    "weight_override",
                ),
                FP,
            )
            == []
        )

    def test_float_weight_rejected(self) -> None:
        config = RuleConfig.model_construct(
            function_type="EI", complexity="High", weight=2.5
        )
        _assert_error(
            validate_weight_override_config(_rule(config, "weight_override"), FP),
            "Weight override requires positive integer 'weight'. Got 2.5",
            "config.weight",
        )


class TestVafConfig:
    def test_missing_gsc(self) -> None:
        _assert_error(
            validate_vaf_config(_rule(RuleConfig(), "vaf"), FP),
            "VAF rule requires 'gsc' dictionary with all 14 GSC keys",
            "config.gsc",
        )

    def test_gsc_not_dict(self) -> None:
        config = RuleConfig.model_construct(gsc="gsc")
        _assert_error(
            validate_vaf_config(_rule(config, "vaf"), FP),
            "VAF rule requires 'gsc' dictionary with all 14 GSC keys",
            "config.gsc",
        )

    def test_empty_gsc_forwards_errors(self) -> None:
        errors = validate_vaf_config(_rule(RuleConfig(gsc={}), "vaf"), FP)
        assert len(errors) == 1
        assert errors[0].rule_id == "r1"
        assert errors[0].field == "config.gsc"


class TestGsc:
    def test_full_valid_gsc(self) -> None:
        assert validate_gsc(dict(GSC_KEYS), _rule(RuleConfig(), "vaf"), FP) == []

    def test_zero_value_is_valid(self) -> None:
        gsc = dict(GSC_KEYS)
        gsc["data_communications"] = 0
        assert validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP) == []

    def test_value_of_five_is_valid(self) -> None:
        gsc = dict(GSC_KEYS)
        gsc["performance"] = 5
        assert validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP) == []

    def test_value_of_six_is_invalid(self) -> None:
        gsc = dict(GSC_KEYS)
        gsc["performance"] = 6
        errors = validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP)
        err = next(e for e in errors if e.field == "config.gsc.performance")
        assert err.rule_id == "r1"
        assert err.message == "GSC 'performance' value must be integer 0-5, got 6"

    def test_non_integer_gsc_value_is_invalid(self) -> None:
        gsc = dict(GSC_KEYS)
        gsc["performance"] = 2.5
        errors = validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP)
        err = next(e for e in errors if e.field == "config.gsc.performance")
        assert err.message == "GSC 'performance' value must be integer 0-5, got 2.5"
        assert err.rule_id == "r1"

    def test_missing_keys(self) -> None:
        errors = validate_gsc({}, _rule(RuleConfig(), "vaf"), FP)
        assert len(errors) == 1
        assert errors[0].message == (
            "VAF rule missing GSC keys: " + ", ".join(sorted(GSC_SET))
        )
        assert errors[0].field == "config.gsc"
        assert errors[0].rule_id == "r1"

    def test_unknown_keys(self) -> None:
        gsc = dict(GSC_KEYS)
        gsc["bogus_key"] = 3
        errors = validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP)
        assert errors[0].message == "VAF rule has unknown GSC keys: bogus_key"
        assert errors[0].field == "config.gsc"
        assert errors[0].rule_id == "r1"

    def test_unknown_keys_many_joined(self) -> None:
        gsc = {"data_communications": 2, "b1": 1, "b2": 1}
        errors = validate_gsc(gsc, _rule(RuleConfig(), "vaf"), FP)
        msg = next(e.message for e in errors if "unknown GSC" in e.message)
        assert msg == "VAF rule has unknown GSC keys: b1, b2"


class TestThreshold:
    def test_missing_key_empty(self) -> None:
        assert validate_threshold({}, "det", _rule(RuleConfig(), "complexity_override"), FP) == []

    def test_wrong_length(self) -> None:
        _assert_error(
            validate_threshold(
                {"det": [1]}, "det", _rule(RuleConfig(), "complexity_override"), FP
            ),
            "Threshold 'det' must be a list of exactly 2 integers",
            "config.thresholds.det",
        )

    def test_not_a_list(self) -> None:
        _assert_error(
            validate_threshold(
                {"det": "15"}, "det", _rule(RuleConfig(), "complexity_override"), FP
            ),
            "Threshold 'det' must be a list of exactly 2 integers",
            "config.thresholds.det",
        )

    def test_non_positive_values(self) -> None:
        _assert_error(
            validate_threshold(
                {"det": [0, -3]}, "det", _rule(RuleConfig(), "complexity_override"), FP
            ),
            "Threshold 'det' values must be positive integers, got [0, -3]",
            "config.thresholds.det",
        )

    def test_first_not_less_than_second(self) -> None:
        _assert_error(
            validate_threshold(
                {"det": [8, 8]}, "det", _rule(RuleConfig(), "complexity_override"), FP
            ),
            "Threshold 'det' first value must be less than second, got [8, 8]",
            "config.thresholds.det",
        )

    def test_valid_bounds(self) -> None:
        assert (
            validate_threshold(
                {"det": [1, 5]}, "det", _rule(RuleConfig(), "complexity_override"), FP
            )
            == []
        )

    def test_zero_first_bound_is_invalid(self) -> None:
        errors = validate_threshold(
            {"det": [0, 5]}, "det", _rule(RuleConfig(), "complexity_override"), FP
        )
        assert len(errors) == 1
        assert errors[0].rule_id == "r1"
        assert errors[0].file_path == FP


class TestElementExclusion:
    def test_missing_element_ids(self) -> None:
        _assert_error(
            validate_element_exclusion_config(
                _rule(RuleConfig(), "element_exclusion"), FP
            ),
            "Element exclusion rule requires non-empty 'element_ids' list",
            "config.element_ids",
        )

    def test_empty_element_ids(self) -> None:
        _assert_error(
            validate_element_exclusion_config(
                _rule(RuleConfig(element_ids=[]), "element_exclusion"), FP
            ),
            "Element exclusion rule requires non-empty 'element_ids' list",
            "config.element_ids",
        )

    def test_non_list_element_ids(self) -> None:
        config = RuleConfig.model_construct(element_ids="fp-001")
        _assert_error(
            validate_element_exclusion_config(
                _rule(config, "element_exclusion"), FP
            ),
            "Element exclusion rule requires non-empty 'element_ids' list",
            "config.element_ids",
        )

    def test_valid_element_ids(self) -> None:
        assert (
            validate_element_exclusion_config(
                _rule(RuleConfig(element_ids=["fp-001"]), "element_exclusion"), FP
            )
            == []
        )