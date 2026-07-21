from __future__ import annotations

import re
from typing import Any

from .models import CalibrationProfile

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def validate_calibration_profile(
    data: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    version = data.get("version", "1.0")
    if not isinstance(version, str) or not SEMVER_RE.match(version):
        errors.append(f"version '{version}' is not a valid semver string")

    spec_cost = data.get("specification_cost", {})
    if not isinstance(spec_cost, dict):
        errors.append("specification_cost must be a mapping")
    else:
        _validate_spec_cost(spec_cost, errors)

    code_cost = data.get("code_generation_cost", {})
    if not isinstance(code_cost, dict):
        errors.append("code_generation_cost must be a mapping")
    else:
        _validate_code_cost(code_cost, errors)

    content_multiplier = data.get("content_multiplier", 0.1)
    if content_multiplier is not None and (
        not isinstance(content_multiplier, (int, float)) or content_multiplier < 0
    ):
        errors.append("content_multiplier must be a non-negative number")

    return errors


def _validate_spec_cost(data: dict[str, Any], errors: list[str]) -> None:
    numeric_fields = [
        "decisions",
        "assumptions",
        "constraints",
        "risks",
        "open_questions",
        "acceptance_criteria",
        "glossary_terms",
    ]
    for field in numeric_fields:
        value = data.get(field)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            errors.append(f"specification_cost.{field} must be a non-negative number")

    activities = data.get("activities", {})
    if not isinstance(activities, dict):
        errors.append("specification_cost.activities must be a mapping")
    else:
        for key, value in activities.items():
            if not isinstance(value, (int, float)) or value < 0:
                errors.append(
                    f"specification_cost.activities.{key} must be a non-negative number"
                )


def _validate_code_cost(data: dict[str, Any], errors: list[str]) -> None:
    numeric_fields = [
        "functional_processes",
        "business_rules",
        "operations",
        "data_groups",
        "relationships",
        "actors",
    ]
    for field in numeric_fields:
        value = data.get(field)
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            errors.append(f"code_generation_cost.{field} must be a non-negative number")


def validate_profile_object(profile: CalibrationProfile) -> list[str]:
    errors: list[str] = []
    if not SEMVER_RE.match(profile.version):
        errors.append(f"version '{profile.version}' is not a valid semver string")
    return errors
