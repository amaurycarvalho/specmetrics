"""Metric metadata builders for the ``metrics.json`` serialization."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def fpa_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for FPA measurements."""
    meta: dict[str, Any] = {"method": "ifpug"}
    vaf = raw.get("fpa_vaf")
    if vaf is not None:
        meta["vaf"] = vaf
    return meta


def sfp_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for SFP measurements."""
    meta: dict[str, Any] = {"method": "simplified"}
    sfp_breakdown = raw.get("sfp_breakdown")
    if sfp_breakdown:
        fp = sfp_breakdown.get("functional_process", {})
        lf = sfp_breakdown.get("logical_function", {})
        meta["fp_contribution"] = fp.get("total_sfp", 0)
        meta["lf_contribution"] = lf.get("total_sfp", 0)
    return meta


def snap_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for SNAP measurements."""
    meta: dict[str, Any] = {"method": "snap"}
    snap_by_category = raw.get("snap_by_category")
    if snap_by_category:
        meta["categories"] = snap_by_category
    return meta


def bcp_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for BCP measurements."""
    return {
        "method": raw.get("bcp_method", "BCP"),
        "provider": raw.get("bcp_provider", ""),
        "sdk_version": raw.get("bcp_sdk_version", ""),
    }


def sp_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for story-point measurements."""
    return {
        "method": raw.get("storypoints_method", "fibonacci_factor_based"),
        "scale": raw.get("storypoints_scale", "fibonacci"),
    }


def tp_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for token-count measurements."""
    meta = {"calibration_version": raw.get("token_calibration_version", "1.0")}
    spec_cost = raw.get("token_specification_cost")
    code_cost = raw.get("token_code_generation_cost")
    if spec_cost is not None:
        meta["specification_cost"] = round(spec_cost, 1)
    if code_cost is not None:
        meta["code_generation_cost"] = round(code_cost, 1)
    return meta


def cp_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for cognitive-points measurements."""
    meta = {"calibration_version": raw.get("cognitive_calibration_version", "1.0")}
    raw_score = raw.get("cognitive_raw_score")
    if raw_score is not None:
        meta["raw_score"] = round(raw_score, 1)
    fib = raw.get("cognitive_fibonacci_normalization")
    if fib is not None:
        meta["fibonacci_normalization"] = {
            k: round(v, 1) if isinstance(v, float) else v for k, v in fib.items()
        }
    return meta


def tshirt_metadata(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for t-shirt-size measurements."""
    from specmetrics.plugins.measurement.tshirt.classifier import DEFAULT_MAPPING

    mapping = {size.label: size.story_point_range[1] for size in DEFAULT_MAPPING}
    return {"scale": raw.get("scale", "XS-S-M-L-XL-XXL"), "mapping": mapping}


_METADATA_BUILDERS: dict[
    str, Callable[[dict[str, Any]], dict[str, Any] | None]
] = {
    "fpa": fpa_metadata,
    "sfp": sfp_metadata,
    "snap": snap_metadata,
    "bcp": bcp_metadata,
    "sp": sp_metadata,
    "tp": tp_metadata,
    "cp": cp_metadata,
    "tshirt": tshirt_metadata,
}


def build_metric_metadata(cli_id: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    """Build the metadata block for a metric from its raw measurement output."""
    handler = _METADATA_BUILDERS.get(cli_id)
    return handler(raw) if handler else None