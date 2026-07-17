from __future__ import annotations

from pathlib import Path

from specmetrics.plugins.calibration.models import (
    CalibrationProfile,
    CodeGenerationCostWeights,
    SpecificationCostWeights,
)
from specmetrics.plugins.calibration.loader import discover_and_load_calibration


def get_default_calibration() -> CalibrationProfile:
    return CalibrationProfile(
        version="1.0",
        specification_cost=SpecificationCostWeights(),
        code_generation_cost=CodeGenerationCostWeights(),
    )


def load_calibration(calibration_dir: str | Path | None = None) -> CalibrationProfile:
    profile = get_default_calibration()
    if calibration_dir is not None:
        loaded = discover_and_load_calibration(calibration_dir, profile)
        if loaded is not None:
            profile = loaded
    return profile
