from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from .models import CalibrationProfile

_yaml = YAML(typ="safe")


def discover_calibration_files(calibration_dir: str | Path) -> list[Path]:
    base = Path(calibration_dir)
    if not base.is_dir():
        return []
    return sorted(base.glob("*.yml"))


def load_calibration_file(file_path: str | Path) -> dict | None:
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
    spec_cost_override = override.get("specification_cost", {})
    code_cost_override = override.get("code_generation_cost", {})

    if isinstance(spec_cost_override, dict):
        for key, value in spec_cost_override.items():
            if key == "activities" and isinstance(value, dict):
                base.specification_cost.activities.update(value)
            elif hasattr(base.specification_cost, key) and isinstance(
                value, (int, float)
            ):
                setattr(base.specification_cost, key, float(value))

    if isinstance(code_cost_override, dict):
        for key, value in code_cost_override.items():
            if hasattr(base.code_generation_cost, key) and isinstance(
                value, (int, float)
            ):
                setattr(base.code_generation_cost, key, float(value))

    version = override.get("version")
    if version and isinstance(version, str):
        base.version = version

    return base


def discover_and_load_calibration(
    calibration_dir: str | Path,
    defaults: CalibrationProfile | None = None,
) -> CalibrationProfile | None:
    files = discover_calibration_files(calibration_dir)
    if not files:
        return defaults

    profile = defaults or CalibrationProfile()
    for file_path in files:
        data = load_calibration_file(file_path)
        if data is not None:
            merge_calibration_data(profile, data)

    return profile
