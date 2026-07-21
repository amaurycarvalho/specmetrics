from __future__ import annotations

import abc
import os
from enum import IntEnum
from pathlib import Path
from typing import Any

import ruamel.yaml


class SourceLevel(IntEnum):
    SYSTEM = 0
    USER = 1
    PROJECT = 2
    ENVIRONMENT = 3
    CLI = 4


class ConfigurationSource(abc.ABC):
    def __init__(self, name: str, precedence: SourceLevel) -> None:
        self.name = name
        self.precedence = precedence

    @abc.abstractmethod
    def load(self) -> dict[str, Any]: ...


class FileSource(ConfigurationSource):
    def __init__(self, path: Path, precedence: SourceLevel) -> None:
        name = f"{precedence.name.lower()} config ({path})"
        super().__init__(name, precedence)
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        text = self.path.read_text(encoding="utf-8")
        yaml = ruamel.yaml.YAML(typ="safe")
        data = yaml.load(text)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError(
                f"Config file {self.path} must contain a mapping, got {type(data).__name__}"
            )
        return _flatten_dict(data, prefix="")


class EnvironmentSource(ConfigurationSource):
    def __init__(self, prefix: str = "SPECMETRICS_") -> None:
        super().__init__(f"environment variables ({prefix}*)", SourceLevel.ENVIRONMENT)
        self.prefix = prefix

    def load(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                suffix = key[len(self.prefix) :].lower()
                parts = suffix.split("_")
                config_key = ".".join(parts) if len(parts) > 1 else suffix
                result[config_key] = value
        return result


class CliSource(ConfigurationSource):
    def __init__(self, args: dict[str, Any] | None = None) -> None:
        super().__init__("CLI arguments", SourceLevel.CLI)
        self.args = args or {}

    def load(self) -> dict[str, Any]:
        return _flatten_dict(self.args, prefix="")


def _flatten_dict(d: dict[str, Any], prefix: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in d.items():
        flat_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, flat_key))
        else:
            result[flat_key] = value
    return result
