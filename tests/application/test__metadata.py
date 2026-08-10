from __future__ import annotations

from specmetrics.application._metadata import (
    bcp_metadata,
    build_metric_metadata,
    cp_metadata,
    fpa_metadata,
    sfp_metadata,
    snap_metadata,
    sp_metadata,
    tp_metadata,
    tshirt_metadata,
)


def test_fpa_metadata_default():
    """Kills fpa_metadata method literal and vaf getattr mutants."""
    assert fpa_metadata({}) == {"method": "ifpug"}


def test_fpa_metadata_with_vaf():
    """Kills the vaf presence branch in fpa_metadata."""
    assert fpa_metadata({"fpa_vaf": 1.1}) == {"method": "ifpug", "vaf": 1.1}


def test_sfp_metadata_default():
    """Kills sfp_metadata method literal and sfp_breakdown get mutants."""
    assert sfp_metadata({}) == {"method": "simplified"}


def test_sfp_metadata_with_breakdown():
    """Kills sfp_metadata breakdown get, fp/lf key, and contribution mutants."""
    result = sfp_metadata(
        {
            "sfp_breakdown": {
                "functional_process": {"total_sfp": 5},
                "logical_function": {"total_sfp": 3},
            }
        }
    )
    assert result == {"method": "simplified", "fp_contribution": 5, "lf_contribution": 3}


def test_sfp_metadata_empty_breakdown():
    """Kills the empty-breakdown truthiness branch."""
    assert sfp_metadata({"sfp_breakdown": {}}) == {"method": "simplified"}


def test_sfp_metadata_contribution_defaults():
    """Kills sfp_metadata contribution default-value mutants."""
    result = sfp_metadata(
        {"sfp_breakdown": {"functional_process": {}, "logical_function": {}}}
    )
    assert result == {"method": "simplified", "fp_contribution": 0, "lf_contribution": 0}


def test_snap_metadata_default():
    """Kills snap_metadata method literal and snap_by_category get mutants."""
    assert snap_metadata({}) == {"method": "snap"}


def test_snap_metadata_with_categories():
    """Kills the snap_by_category presence branch."""
    result = snap_metadata({"snap_by_category": {"presentation": 4}})
    assert result == {"method": "snap", "categories": {"presentation": 4}}


def test_bcp_metadata_defaults():
    """Kills bcp_metadata method/provider/sdk_version default mutants."""
    assert bcp_metadata({}) == {
        "method": "BCP",
        "provider": "",
        "sdk_version": "",
    }


def test_bcp_metadata_preserves_values():
    """Kills bcp_metadata key-rename mutants."""
    result = bcp_metadata({"bcp_method": "llm", "bcp_provider": "x", "bcp_sdk_version": "1.2"})
    assert result == {"method": "llm", "provider": "x", "sdk_version": "1.2"}


def test_sp_metadata_defaults():
    """Kills sp_metadata method/scale default mutants."""
    assert sp_metadata({}) == {"method": "fibonacci_factor_based", "scale": "fibonacci"}


def test_sp_metadata_preserves_values():
    """Kills sp_metadata key-rename mutants."""
    result = sp_metadata({"storypoints_method": "linear", "storypoints_scale": "s"})
    assert result == {"method": "linear", "scale": "s"}


def test_tp_metadata_defaults():
    """Kills tp_metadata calibration_version default and cost get mutants."""
    assert tp_metadata({}) == {"calibration_version": "1.0"}


def test_tp_metadata_with_costs():
    """Kills tp_metadata specification/code cost branches and rounding."""
    result = tp_metadata(
        {
            "token_calibration_version": "2.0",
            "token_specification_cost": 1.23,
            "token_code_generation_cost": 4.56,
        }
    )
    assert result == {
        "calibration_version": "2.0",
        "specification_cost": 1.2,
        "code_generation_cost": 4.6,
    }


def test_cp_metadata_defaults():
    """Kills cp_metadata calibration_version default and score/fib get mutants."""
    assert cp_metadata({}) == {"calibration_version": "1.0"}


def test_cp_metadata_with_score():
    """Kills cp_metadata raw_score branch and rounding."""
    result = cp_metadata({"cognitive_raw_score": 5.67})
    assert result == {"calibration_version": "1.0", "raw_score": 5.7}


def test_cp_metadata_with_fib():
    """Kills cp_metadata fibonacci_normalization branch and float rounding."""
    result = cp_metadata(
        {"cognitive_fibonacci_normalization": {"L1": 2.5, "L2": 3}}
    )
    assert result == {
        "calibration_version": "1.0",
        "fibonacci_normalization": {"L1": 2.5, "L2": 3},
    }


def test_tshirt_metadata_scale_default():
    """Kills tshirt_metadata scale default mutant."""
    result = tshirt_metadata({})
    assert result["scale"] == "XS-S-M-L-XL-XXL"
    assert isinstance(result["mapping"], dict)


def test_tshirt_metadata_preserves_scale():
    """Kills tshirt_metadata scale key-rename mutant."""
    result = tshirt_metadata({"scale": "custom"})
    assert result["scale"] == "custom"


def test_build_metric_metadata_known():
    """Kills the handler lookup branch."""
    assert build_metric_metadata("fpa", {}) == {"method": "ifpug"}


def test_build_metric_metadata_unknown():
    """Kills the unknown cli_id None branch."""
    assert build_metric_metadata("unknown_metric", {}) is None
