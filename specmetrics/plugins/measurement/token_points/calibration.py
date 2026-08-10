"""Calibration loading for Token Points measurement."""

from __future__ import annotations

from pathlib import Path

from specmetrics.plugins.calibration.loader import discover_and_load_calibration
from specmetrics.plugins.calibration.models import (
    CalibrationProfile,
    CodeGenerationCostWeights,
    SpecificationCostWeights,
)


def get_default_calibration() -> CalibrationProfile:
    """Return the default Token Points calibration profile."""
    return CalibrationProfile(
        version="1.0",
        specification_cost=SpecificationCostWeights(),
        code_generation_cost=CodeGenerationCostWeights(),
    )


def load_calibration(calibration_dir: str | Path | None = None) -> CalibrationProfile:
    """Load a calibration profile, merging overrides from the given directory."""
    profile = get_default_calibration()
    if calibration_dir is not None:
        loaded = discover_and_load_calibration(calibration_dir, profile)
        if loaded is not None:
            profile = loaded
    return profile
