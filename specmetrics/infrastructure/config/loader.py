"""Configuration loading and resolution.

Discovers configuration sources (system, user, project, environment), merges
them by precedence, validates the result against the core schema, and exposes
a ``ConfigProvider`` to the rest of the application.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel

from .plugin import PluginConfigCollector
from .resolver import Resolver
from .schema import (
    ConfigProvider,
    ConfigurationDump,
    ConfigWarning,
    CoreConfig,
    ResolvedConfiguration,
)
from .sources import ConfigurationSource, EnvironmentSource, FileSource, SourceLevel
from .validator import ConfigValidationError, Validator

logger = logging.getLogger(__name__)


class Loader:
    """Discovers and loads configuration sources for a project."""

    def _get_xdg_config_home(self: Self) -> Path:
        """Return the XDG config home directory path."""
        return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    def discover_sources(
        self: Self, project_root: Path, cli_config_path: Path | None = None
    ) -> list[ConfigurationSource]:
        """Discover configuration files at system, user, and project levels."""
        sources: list[ConfigurationSource] = []
        config_files = ["config.yml", "config.yaml", "config.json"]

        for filename in config_files:
            path = Path("/etc/specmetrics") / filename
            if path.exists():
                sources.append(FileSource(path, SourceLevel.SYSTEM))
                break

        for filename in config_files:
            path = self._get_xdg_config_home() / "specmetrics" / filename
            if path.exists():
                sources.append(FileSource(path, SourceLevel.USER))
                break

        for basename in [
            "specmetrics.yml",
            "specmetrics.yaml",
            "specmetrics.json",
            ".specmetrics.yml",
            ".specmetrics.yaml",
            ".specmetrics.json",
        ]:
            path = project_root / basename
            if path.exists():
                sources.append(FileSource(path, SourceLevel.PROJECT))
                break

        if cli_config_path is not None:
            resolved = self._expand_env_vars(str(cli_config_path))
            path = Path(resolved)
            if path.exists():
                sources.append(FileSource(path.resolve(), SourceLevel.PROJECT))

        return sources

    def load_sources(self: Self, sources: list[ConfigurationSource]) -> dict[str, Any]:
        """Load and merge all sources, later-precedence sources win."""
        merged: dict[str, Any] = {}
        for source in sorted(sources, key=lambda s: s.precedence):
            try:
                data = source.load()
                merged.update(data)
            except Exception as exc:
                logger.warning("Failed to load source %s: %s", source.name, exc)
        return merged

    def _expand_env_vars(self: Self, value: str) -> str:
        """Expand environment variables inside a string."""
        return os.path.expandvars(value)


class ConfigurationSystem:
    """Facade that discovers, resolves, and validates project configuration."""

    def __init__(
        self: Self, project_root: Path | None = None, config_path: Path | None = None
    ) -> None:
        """Initialize the configuration system for a project root."""
        self._project_root = project_root or Path.cwd()
        self._config_path = config_path or self._resolve_env_config_path()
        self._loader = Loader()
        self._resolver = Resolver()
        self._plugin_collector = PluginConfigCollector()
        self._config: ResolvedConfiguration | None = None

    @staticmethod
    def _resolve_env_config_path() -> Path | None:
        """Resolve the config path from the ``SPECMETRICS_CONFIG_PATH`` env var."""
        env_path = os.environ.get("SPECMETRICS_CONFIG_PATH")
        if env_path:
            expanded = os.path.expandvars(env_path)
            resolved = Path(expanded)
            if resolved.exists():
                return resolved
        return None

    def register_plugin_schema(self: Self, plugin_id: str, schema: type) -> None:
        """Register a plugin configuration schema by plugin id."""
        self._plugin_collector.register(plugin_id, schema)

    def load(self: Self) -> ConfigProvider:
        """Load, resolve, and validate configuration; return a provider."""
        sources = self._loader.discover_sources(self._project_root, self._config_path)

        env_source = EnvironmentSource()
        sources.append(env_source)

        self._resolver = Resolver()
        for source in sources:
            data = source.load()
            self._resolver.add_source(source, data)

        resolved_dict, provenance, warnings_raw = self._resolver.resolve()

        known_prefixes = ["plugins"]
        known_prefixes.extend(self._plugin_collector.declarations.keys())

        validator = Validator(CoreConfig)
        unrecognized_warnings = validator.check_unrecognized_keys(
            resolved_dict, known_prefixes=known_prefixes
        )
        warnings = list(warnings_raw) + unrecognized_warnings

        try:
            validator.validate(resolved_dict)
        except ConfigValidationError as exc:
            logger.error(
                "config_validation_failed",
                field=exc.field,
                value=exc.value,
                expected=exc.expected_type,
            )
            warnings.append(
                ConfigWarning(
                    message=exc.message,
                    key=exc.field,
                )
            )

        config = CoreConfig()
        for key, value in resolved_dict.items():
            if key.startswith("plugins."):
                plugin_id = key.split(".")[1]
                try:
                    self._plugin_collector.validate_plugin_config(
                        plugin_id, {key.split(".", 2)[2]: value}
                    )
                except Exception:
                    pass
            else:
                self._apply_value(config, key, value)

        self._config = ResolvedConfiguration(
            values=config,
            provenance=provenance,
            warnings=warnings,
            schema=CoreConfig,
        )

        source_names = [s.name for s in sources]
        logger.info(
            "Configuration loaded from %d source(s): %s",
            len(sources),
            ", ".join(source_names),
        )

        return _ConfigProviderImpl(self._config)

    def _apply_value(self: Self, obj: BaseModel, key: str, value: object) -> None:
        """Apply a flattened config value onto a pydantic model by dotted key."""
        parts = key.split(".")
        current: object = obj
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return
        last = parts[-1]
        if hasattr(current, last):
            field_type = type(getattr(current, last))
            try:
                coerced = (
                    field_type(value) if not isinstance(value, field_type) else value
                )
            except (ValueError, TypeError):
                coerced = value
            setattr(current, last, coerced)


class _ConfigProviderImpl:
    """Concrete ``ConfigProvider`` backed by a resolved configuration."""

    def __init__(self: Self, config: ResolvedConfiguration) -> None:
        """Initialize the provider with the resolved configuration."""
        self._config = config

    def get(self: Self, key: str, default: object = ...) -> object:
        """Return the value for a dotted key, or ``default`` when missing."""
        parts = key.split(".")
        current: object = self._config.values
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                if default is not ...:
                    return default
                raise KeyError(f"Configuration key not found: {key}")
        return current

    def get_model(self: Self, model_type: type) -> BaseModel:
        """Return the resolved config as the given model type."""
        if isinstance(self._config.values, model_type):
            return self._config.values
        return model_type.model_validate(self._config.values.model_dump())

    @property
    def dump(self: Self) -> ConfigurationDump:
        """Return an introspectable dump of the resolved configuration."""
        from .introspection import build_dump

        return build_dump(self._config)

    @property
    def warnings(self: Self) -> list[ConfigWarning]:
        """Return warnings collected during loading and validation."""
        return self._config.warnings
