from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from .bloom_classifier import _DEFAULT_BLOOM_MAPPINGS, _DEFAULT_BLOOM_WEIGHTS
from .fibonacci_normalizer import _DEFAULT_THRESHOLDS, _DEFAULT_OUTPUT_VALUES


class BloomClassification(BaseModel):
    bloom_level: str
    rationale: str = ""
    configured_weight: float = 1.0


class FibonacciNormalizationProfile(BaseModel):
    thresholds: list[float] = Field(default_factory=lambda: list(_DEFAULT_THRESHOLDS))
    output_values: list[int] = Field(default_factory=lambda: list(_DEFAULT_OUTPUT_VALUES))

    @model_validator(mode="after")
    def validate_lengths(self) -> FibonacciNormalizationProfile:
        if len(self.output_values) != len(self.thresholds) + 1:
            raise ValueError(
                f"len(output_values) ({len(self.output_values)}) must equal "
                f"len(thresholds) + 1 ({len(self.thresholds) + 1})"
            )
        return self


class CognitiveCalibrationProfile(BaseModel):
    version: str = "1.0"
    bloom_levels: dict[str, float] = Field(
        default_factory=lambda: dict(_DEFAULT_BLOOM_WEIGHTS)
    )
    bloom_mappings: dict[str, str] = Field(
        default_factory=lambda: dict(_DEFAULT_BLOOM_MAPPINGS)
    )
    default_bloom_level: str = "analyze"
    fibonacci_normalization: FibonacciNormalizationProfile = Field(
        default_factory=FibonacciNormalizationProfile
    )


def get_default_calibration() -> CognitiveCalibrationProfile:
    return CognitiveCalibrationProfile()


def load_calibration(
    calibration_dir: str | Path | None = None,
) -> CognitiveCalibrationProfile:
    profile = get_default_calibration()
    if calibration_dir is not None:
        calibration_path = Path(calibration_dir)
        if calibration_path.is_dir():
            yaml_files = sorted(calibration_path.glob("*.yml")) + sorted(
                calibration_path.glob("*.yaml")
            )
            for yaml_file in yaml_files:
                loaded = _load_calibration_file(yaml_file)
                if loaded is not None:
                    profile = _merge_calibration_data(profile, loaded)
    return profile


def _load_calibration_file(path: Path) -> dict | None:
    try:
        from ruamel.yaml import YAML

        yaml = YAML(typ="safe")
        with open(path) as f:
            data = yaml.load(f)
        if data is None:
            return None
        if not isinstance(data, dict):
            return None
        return dict(data)
    except Exception:
        return None


def _merge_calibration_data(
    base: CognitiveCalibrationProfile,
    overrides: dict,
) -> CognitiveCalibrationProfile:
    version = overrides.get("version", base.version)
    bloom_levels = dict(base.bloom_levels)
    if "bloom_levels" in overrides and isinstance(overrides["bloom_levels"], dict):
        bloom_levels.update(overrides["bloom_levels"])

    bloom_mappings = dict(base.bloom_mappings)
    if "bloom_mappings" in overrides and isinstance(overrides["bloom_mappings"], dict):
        bloom_mappings.update(overrides["bloom_mappings"])

    default_bloom = overrides.get(
        "default_bloom_level", base.default_bloom_level
    )

    fib_profile = base.fibonacci_normalization
    if "fibonacci_normalization" in overrides:
        fib_data = overrides["fibonacci_normalization"]
        if isinstance(fib_data, dict):
            thresholds = fib_data.get("thresholds", fib_profile.thresholds)
            output_values = fib_data.get(
                "output_values", fib_profile.output_values
            )
            fib_profile = FibonacciNormalizationProfile(
                thresholds=thresholds, output_values=output_values
            )

    return CognitiveCalibrationProfile(
        version=version,
        bloom_levels=bloom_levels,
        bloom_mappings=bloom_mappings,
        default_bloom_level=default_bloom,
        fibonacci_normalization=fib_profile,
    )
