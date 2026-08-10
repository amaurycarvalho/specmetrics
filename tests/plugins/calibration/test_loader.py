"""Mutation-killing tests for specmetrics.plugins.calibration.loader."""

from __future__ import annotations

from specmetrics.plugins.calibration.loader import (
    merge_calibration_data,
)
from specmetrics.plugins.calibration.models import CalibrationProfile


def _profile(**kwargs) -> CalibrationProfile:
    return CalibrationProfile(**kwargs)


def test_merge_without_specification_cost_leaves_profile_unchanged() -> None:
    """Kills _merge_specification_cost__mutmut_5 (removed default {})."""
    base = _profile()
    merged = merge_calibration_data(base, {"code_generation_cost": {"operations": 3.0}})
    assert merged.specification_cost.activities["exploration"] == 2.0
    assert merged.specification_cost.decisions == 1.5


def test_merge_activities_updates_under_exact_activities_key() -> None:
    """Kills _merge_specification_cost__mutmut_8/9/10/11 (activities key logic)."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"specification_cost": {"activities": {"exploration": 5.0}}}
    )
    assert merged.specification_cost.activities["exploration"] == 5.0
    assert merged.specification_cost.activities["review"] == 1.5


def test_merge_dict_value_under_non_activities_key_not_merged_into_activities() -> None:
    """Kills _merge_specification_cost__mutmut_8 (and/or operator on activities check)."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"specification_cost": {"decisions": {"custom": 1.0}}}
    )
    assert "custom" not in merged.specification_cost.activities


def test_merge_activities_calls_update_with_mapping() -> None:
    """Kills _merge_specification_cost__mutmut_12 (update(None))."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"specification_cost": {"activities": {"review": 3.0}}}
    )
    assert merged.specification_cost.activities["review"] == 3.0


def test_merge_non_numeric_spec_cost_field_ignored() -> None:
    """Kills _merge_specification_cost__mutmut_13 (and/or in hasattr branch)."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"specification_cost": {"decisions": "not-a-number"}}
    )
    assert merged.specification_cost.decisions == 1.5


def test_merge_numeric_spec_cost_field_updated() -> None:
    """Kills _merge_specification_cost__mutmut_13 (or-variant skips float setattr)."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"specification_cost": {"decisions": 3.5}}
    )
    assert merged.specification_cost.decisions == 3.5


def test_merge_without_code_generation_cost_leaves_profile_unchanged() -> None:
    """Kills _merge_code_generation_cost__mutmut_5 (removed default {})."""
    base = _profile()
    merged = merge_calibration_data(base, {"specification_cost": {"risks": 2.0}})
    assert merged.code_generation_cost.operations == 2.0
    assert merged.code_generation_cost.functional_processes == 5.0


def test_merge_non_numeric_code_cost_field_ignored() -> None:
    """Kills _merge_code_generation_cost__mutmut_8 (and/or in hasattr branch)."""
    base = _profile()
    merged = merge_calibration_data(
        base, {"code_generation_cost": {"operations": "not-a-number"}}
    )
    assert merged.code_generation_cost.operations == 2.0


def test_merge_version_applies_string_override() -> None:
    """Kills _merge_version__mutmut_1/2/3/4/5/6 (version override logic)."""
    base = _profile()
    merged = merge_calibration_data(base, {"version": "2.1"})
    assert merged.version == "2.1"


def test_merge_version_ignores_empty_string() -> None:
    """Kills _merge_version__mutmut_5 (or instead of and on version truthiness)."""
    base = _profile()
    merged = merge_calibration_data(base, {"version": ""})
    assert merged.version == "1.0"


def test_merge_version_ignores_non_string_value() -> None:
    """Kills _merge_version__mutmut_5 (or variant accepts non-string truthy values)."""
    base = _profile()
    merged = merge_calibration_data(base, {"version": 5})
    assert merged.version == "1.0"
