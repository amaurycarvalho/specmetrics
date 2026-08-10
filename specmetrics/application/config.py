"""Application configuration loaded from a project's ``.specmetrics`` folder."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from ruamel.yaml import YAML

_yaml = YAML(typ="safe")


class AppConfig:
    """Application configuration loaded from a project's ``.specmetrics`` folder."""

    def __init__(self: Self, config: dict[str, Any] | None = None) -> None:
        """Initialize the configuration from an optional raw mapping."""
        self._config = config or {}

    @classmethod
    def load(cls: type[Self], project_path: Path) -> AppConfig:
        """Load configuration from ``<project_path>/.specmetrics/config.yml``."""
        config_path = project_path / ".specmetrics" / "config.yml"
        if not config_path.exists():
            return cls()
        with open(config_path) as f:
            raw = _yaml.load(f)
        return cls(raw or {})

    @property
    def default_output_format(self: Self) -> str:
        """Return the default pipeline output format."""
        return self._config.get("pipeline", {}).get("default_output_format", "text")

    @property
    def verbose(self: Self) -> bool:
        """Return whether verbose pipeline output is enabled."""
        return bool(self._config.get("pipeline", {}).get("verbose", False))

    @property
    def verify_compatibility(self: Self) -> bool:
        """Return whether plugin compatibility verification is enabled."""
        return bool(self._config.get("plugins", {}).get("verify_compatibility", True))
