"""Calibration profiles for Story Points measurement."""

from __future__ import annotations

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, Field, model_validator

DEFAULT_FACTOR_COEFFICIENTS: dict[str, float] = {
    "business_interactions": 1.0,
    "logical_information": 1.0,
    "external_integrations": 2.0,
    "business_rule_density": 1.5,
    "workflow_breadth": 1.0,
    "exception_handling": 3.0,
}

DEFAULT_CSM_BASE_WEIGHTS: dict[str, float] = {
    "exploration": 4.0,
    "clarification": 5.0,
    "refinement": 5.0,
    "review": 3.0,
    "validation": 3.0,
    "decision": 5.0,
    "assumption": 2.0,
    "constraint": 3.0,
    "risk": 4.0,
    "open_question": 2.0,
    "acceptance_criterion": 3.0,
    "glossary_term": 1.0,
    "reference": 0.5,
}

DEFAULT_CFM_BASE_WEIGHTS: dict[str, float] = {
    "business_rule": 4.0,
    "operation": 3.0,
    "data_group": 3.0,
    "relationship": 1.0,
    "actor": 1.0,
}

DEFAULT_FIBONACCI_SCALE: list[int] = [1, 2, 3, 5, 8, 13, 20, 40, 100]


class StoryPointsCalibrationProfile(BaseModel):
    """Configurable calibration profile for Story Points estimation."""

    version: str = "1.0"
    content_multiplier: float = 0.1
    factor_coefficients: dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_FACTOR_COEFFICIENTS)
    )
    csm_base_weights: dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_CSM_BASE_WEIGHTS)
    )
    cfm_base_weights: dict[str, float] = Field(
        default_factory=lambda: dict(DEFAULT_CFM_BASE_WEIGHTS)
    )
    default_fallback_weight: float = 1.0
    fibonacci_scale: list[int] = Field(
        default_factory=lambda: list(DEFAULT_FIBONACCI_SCALE)
    )
    ranking_strategy: str = "percentile"

    @model_validator(mode="after")
    def validate_weights(self: Self) -> StoryPointsCalibrationProfile:
        """Validate weights, scales, and ranking strategy configuration."""
        if self.content_multiplier < 0.0:
            raise ValueError(
                f"content_multiplier must be >= 0.0, got {self.content_multiplier}"
            )
        _validate_weight_entries(
            self.factor_coefficients,
            self.csm_base_weights,
            self.cfm_base_weights,
        )
        if self.default_fallback_weight < 0.0:
            raise ValueError(
                f"default_fallback_weight must be >= 0.0, "
                f"got {self.default_fallback_weight}"
            )
        _validate_fibonacci_scale(self.fibonacci_scale)
        if self.ranking_strategy not in ("percentile",):
            raise ValueError(
                f"ranking_strategy must be 'percentile', got {self.ranking_strategy}"
            )
        return self


def _validate_weight_entries(
    factor_coefficients: dict[str, float],
    csm_base_weights: dict[str, float],
    cfm_base_weights: dict[str, float],
) -> None:
    for name, weights in [
        ("factor_coefficients", factor_coefficients),
        ("csm_base_weights", csm_base_weights),
        ("cfm_base_weights", cfm_base_weights),
    ]:
        for key, val in weights.items():
            if val < 0.0:
                raise ValueError(
                    f"{name}.{key} must be >= 0.0, got {val}"
                )


def _validate_fibonacci_scale(scale: list[int]) -> None:
    if len(scale) < 2:
        raise ValueError(
            f"fibonacci_scale must contain at least 2 values, "
            f"got {len(scale)}"
        )
    for i in range(1, len(scale)):
        if scale[i] <= scale[i - 1]:
            raise ValueError(
                f"fibonacci_scale must be sorted ascending, "
                f"got {scale}"
            )


def get_default_calibration() -> StoryPointsCalibrationProfile:
    """Return the default Story Points calibration profile."""
    return StoryPointsCalibrationProfile()


def load_calibration(
    calibration_dir: str | Path | None = None,
) -> StoryPointsCalibrationProfile:
    """Load a calibration profile, merging overrides from the given directory."""
    profile = get_default_calibration()

    if calibration_dir is None:
        return profile

    cal_path = Path(calibration_dir)
    if not cal_path.is_dir():
        return profile

    yaml_files = sorted(cal_path.glob("*.yaml")) + sorted(cal_path.glob("*.yml"))
    if not yaml_files:
        return profile

    merged: dict = {}
    for yf in yaml_files:
        with open(yf) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            merged.update(data)

    if not merged:
        return profile

    return StoryPointsCalibrationProfile(**merged)
