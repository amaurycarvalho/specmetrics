"""Config file persistence helpers for the CLI config commands."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import ruamel.yaml

LLM_NAMESPACE = ("plugins", "extraction_stage", "llm")


def get_user_config_dir() -> Path:
    """Return the user-level SpecMetrics config directory."""
    xdg_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(xdg_home) / "specmetrics"


def get_user_config_path() -> Path:
    """Return the user config file path, preferring an existing file."""
    for filename in ["config.yml", "config.yaml", "config.json"]:
        path = get_user_config_dir() / filename
        if path.exists():
            return path
    return get_user_config_dir() / "config.yml"


def read_config_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML config file into a mapping, or an empty mapping."""
    if not path.exists():
        return {}
    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_config_yaml(path: Path, data: dict[str, Any]) -> None:
    """Write a mapping to a YAML config file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def set_nested(data: dict[str, Any], keys: tuple[str, ...], value: object) -> None:
    """Set a value at a nested dotted key path inside a mapping."""
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def get_nested(data: dict[str, Any], keys: tuple[str, ...]) -> object:
    """Return the value at a nested dotted key path, or None when missing."""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def write_llm_config(**kwargs: str | None) -> None:
    """Persist non-None LLM settings to the user config file."""
    path = get_user_config_path()
    data = read_config_yaml(path)
    for key, value in kwargs.items():
        if value is not None:
            set_nested(data, LLM_NAMESPACE + (key,), value)
    write_config_yaml(path, data)
    print(f"Updated {path}")


def set_provider_none() -> None:
    """Persist 'none' as the LLM provider after clearing previous settings."""
    path = get_user_config_path()
    data = read_config_yaml(path)
    llm_data = get_nested(data, LLM_NAMESPACE)
    if llm_data:
        for key in ("api_url", "model", "api_key"):
            llm_data.pop(key, None)
    set_nested(data, LLM_NAMESPACE + ("provider",), "none")
    write_config_yaml(path, data)
    print(f"Updated {path}")
    print("LLM provider set to 'none' \u2014 using deterministic structural extraction")
    print("  (no API key required, fully offline)")