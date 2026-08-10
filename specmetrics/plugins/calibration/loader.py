"""Loading and merging of calibration profiles from YAML files."""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from .models import CalibrationProfile

_yaml = YAML(typ="safe")


def discover_calibration_files(calibration_dir: str | Path) -> list[Path]:
    """Return the YAML calibration files in the given directory."""
    base = Path(calibration_dir)
    if not base.is_dir():
        return []
    return sorted(base.glob("*.yml"))


def load_calibration_file(file_path: str | Path) -> dict | None:
    """Load a single calibration YAML file into a dict, or None on failure."""
    try:
        with open(file_path) as f:
            data = _yaml.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None


def merge_calibration_data(
    base: CalibrationProfile,
    override: dict,
) -> CalibrationProfile:
    """Merge override data into the base calibration profile."""
    _merge_specification_cost(base, override)
    _merge_code_generation_cost(base, override)
    _merge_version(base, override)
    return base


def _merge_specification_cost(
    base: CalibrationProfile, override: dict
) -> None:
    spec_cost_override = override.get("specification_cost", {})
    if isinstance(spec_cost_override, dict):
        for key, value in spec_cost_override.items():
            if key == "activities" and isinstance(value, dict):
                base.specification_cost.activities.update(value)
            elif hasattr(base.specification_cost, key) and isinstance(
                value, (int, float)
            ):
                setattr(base.specification_cost, key, float(value))


def _merge_code_generation_cost(
    base: CalibrationProfile, override: dict
) -> None:
    code_cost_override = override.get("code_generation_cost", {})
    if isinstance(code_cost_override, dict):
        for key, value in code_cost_override.items():
            if hasattr(base.code_generation_cost, key) and isinstance(
                value, (int, float)
            ):
                setattr(base.code_generation_cost, key, float(value))


def _merge_version(base: CalibrationProfile, override: dict) -> None:
    version = override.get("version")
    if version and isinstance(version, str):
        base.version = version


def discover_and_load_calibration(
    calibration_dir: str | Path,
    defaults: CalibrationProfile | None = None,
) -> CalibrationProfile | None:
    """Discover and load calibration profiles, merging them in file order."""
    files = discover_calibration_files(calibration_dir)
    if not files:
        return defaults

    profile = defaults or CalibrationProfile()
    for file_path in files:
        data = load_calibration_file(file_path)
        if data is not None:
            merge_calibration_data(profile, data)

    return profile
