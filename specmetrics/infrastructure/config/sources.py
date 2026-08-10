"""Configuration sources: files, environment variables, and CLI arguments."""

from __future__ import annotations

import abc
import os
from enum import IntEnum
from pathlib import Path
from typing import Any, Self

import ruamel.yaml


class SourceLevel(IntEnum):
    """Precedence level of a configuration source."""

    SYSTEM = 0
    USER = 1
    PROJECT = 2
    ENVIRONMENT = 3
    CLI = 4


class ConfigurationSource(abc.ABC):
    """Abstract base for a configuration source."""

    def __init__(self: Self, name: str, precedence: SourceLevel) -> None:
        """Initialize the source with a name and precedence level."""
        self.name = name
        self.precedence = precedence

    @abc.abstractmethod
    def load(self: Self) -> dict[str, Any]:
        """Load configuration data as a flat dotted-key mapping."""
        ...


class FileSource(ConfigurationSource):
    """Configuration source backed by a YAML or JSON file."""

    def __init__(self: Self, path: Path, precedence: SourceLevel) -> None:
        """Initialize the file source with its path and precedence."""
        name = f"{precedence.name.lower()} config ({path})"
        super().__init__(name, precedence)
        self.path = path

    def load(self: Self) -> dict[str, Any]:
        """Load and flatten configuration data from the file."""
        if not self.path.exists():
            return {}
        text = self.path.read_text(encoding="utf-8")
        yaml = ruamel.yaml.YAML(typ="safe")
        data = yaml.load(text)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise TypeError(
                f"Config file {self.path} must contain a mapping, got {type(data).__name__}"
            )
        return _flatten_dict(data, prefix="")


class EnvironmentSource(ConfigurationSource):
    """Configuration source backed by ``SPECMETRICS_*`` environment variables."""

    def __init__(self: Self, prefix: str = "SPECMETRICS_") -> None:
        """Initialize the environment source with a variable prefix."""
        super().__init__(f"environment variables ({prefix}*)", SourceLevel.ENVIRONMENT)
        self.prefix = prefix

    def load(self: Self) -> dict[str, Any]:
        """Load configuration from environment variables under the prefix."""
        result: dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                suffix = key[len(self.prefix) :].lower()
                parts = suffix.split("_")
                config_key = ".".join(parts) if len(parts) > 1 else suffix
                result[config_key] = value
        return result


class CliSource(ConfigurationSource):
    """Configuration source backed by CLI arguments."""

    def __init__(self: Self, args: dict[str, Any] | None = None) -> None:
        """Initialize the CLI source with optional argument values."""
        super().__init__("CLI arguments", SourceLevel.CLI)
        self.args = args or {}

    def load(self: Self) -> dict[str, Any]:
        """Load and flatten configuration from CLI arguments."""
        return _flatten_dict(self.args, prefix="")


def _flatten_dict(d: dict[str, Any], prefix: str) -> dict[str, Any]:
    """Flatten a nested mapping into dotted keys."""
    result: dict[str, Any] = {}
    for key, value in d.items():
        flat_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(_flatten_dict(value, flat_key))
        else:
            result[flat_key] = value
    return result
