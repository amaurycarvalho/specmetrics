"""Mutation-killing tests for specmetrics.plugins.calibration.validator."""

from __future__ import annotations

from specmetrics.plugins.calibration.validator import validate_calibration_profile


def test_spec_cost_negative_value_reported() -> None:
    """Kills _validate_spec_cost__mutmut_14/15 (value replaced by None)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"decisions": -1}}
    )
    assert "specification_cost.decisions must be a non-negative number" in errors


def test_spec_cost_zero_value_is_valid() -> None:
    """Kills _validate_spec_cost__mutmut_22/23 (boundary 0 under < 0)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"decisions": 0}}
    )
    assert "specification_cost.decisions must be a non-negative number" not in errors


def test_spec_cost_non_numeric_value_reported() -> None:
    """Kills _validate_spec_cost__mutmut_18 (and instead of or on type check)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"decisions": "oops"}}
    )
    assert "specification_cost.decisions must be a non-negative number" in errors


def test_code_cost_zero_value_is_valid() -> None:
    """Kills _validate_code_cost__mutmut_20/21 (boundary 0 under < 0)."""
    errors = validate_calibration_profile(
        {"code_generation_cost": {"operations": 0}}
    )
    assert "code_generation_cost.operations must be a non-negative number" not in errors


def test_spec_cost_non_mapping_activities_reported() -> None:
    """Kills _validate_spec_cost__mutmut_30/31/33/34/35 (activities key + message)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"activities": "not-a-mapping"}}
    )
    assert "specification_cost.activities must be a mapping" in errors


def test_spec_cost_activities_non_numeric_value_reported() -> None:
    """Kills _validate_spec_cost__mutmut_36 (and instead of or on type check)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"activities": {"review": "oops"}}}
    )
    assert (
        "specification_cost.activities.review must be a non-negative number" in errors
    )


def test_spec_cost_activities_valid_number_not_reported() -> None:
    """Kills _validate_spec_cost__mutmut_37 (isinstance instead of not isinstance)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"activities": {"review": 1.5}}}
    )
    assert "specification_cost.activities.review must be a non-negative number" not in errors


def test_spec_cost_activities_zero_value_is_valid() -> None:
    """Kills _validate_spec_cost__mutmut_38/39 (boundary 0 under < 0)."""
    errors = validate_calibration_profile(
        {"specification_cost": {"activities": {"review": 0}}}
    )
    assert "specification_cost.activities.review must be a non-negative number" not in errors


def test_code_cost_negative_value_reported() -> None:
    """Kills _validate_code_cost__mutmut_22 (errors.append(None))."""
    errors = validate_calibration_profile(
        {"code_generation_cost": {"operations": -1}}
    )
    assert "code_generation_cost.operations must be a non-negative number" in errors


def test_code_cost_non_numeric_value_reported() -> None:
    """Kills _validate_code_cost__mutmut_18 (and instead of or on type check)."""
    errors = validate_calibration_profile(
        {"code_generation_cost": {"operations": "oops"}}
    )
    assert "code_generation_cost.operations must be a non-negative number" in errors
