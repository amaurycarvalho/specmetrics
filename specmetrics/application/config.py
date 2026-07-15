from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

_yaml = YAML(typ="safe")


class AppConfig:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or {}

    @classmethod
    def load(cls, project_path: Path) -> AppConfig:
        config_path = project_path / ".specify" / "config.yml"
        if not config_path.exists():
            return cls()
        with open(config_path) as f:
            raw = _yaml.load(f)
        return cls(raw or {})

    @property
    def default_output_format(self) -> str:
        return (
            self._config.get("pipeline", {}).get("default_output_format", "text")
        )

    @property
    def verbose(self) -> bool:
        return bool(self._config.get("pipeline", {}).get("verbose", False))

    @property
    def verify_compatibility(self) -> bool:
        return bool(
            self._config.get("plugins", {}).get("verify_compatibility", True)
        )
