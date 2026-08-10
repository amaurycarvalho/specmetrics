"""Plugin configuration schema registration and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from pydantic import BaseModel


@dataclass
class PluginConfigDeclaration:
    """Declares the configuration schema for a plugin."""

    plugin_id: str
    schema_model: type[BaseModel]


class PluginConfigCollector:
    """Collects and validates configuration schemas registered by plugins."""

    def __init__(self: Self) -> None:
        """Initialize the collector with an empty declaration registry."""
        self._declarations: dict[str, PluginConfigDeclaration] = {}

    def register(self: Self, plugin_id: str, schema_model: type[BaseModel]) -> None:
        """Register a plugin configuration schema under a plugin id."""
        self._declarations[plugin_id] = PluginConfigDeclaration(
            plugin_id=plugin_id,
            schema_model=schema_model,
        )

    @property
    def declarations(self: Self) -> dict[str, PluginConfigDeclaration]:
        """Return a copy of the registered declarations."""
        return dict(self._declarations)

    def build_merged_schemas(self: Self) -> dict[str, type[BaseModel]]:
        """Return a mapping of plugin ids to their schema models."""
        return {pid: decl.schema_model for pid, decl in self._declarations.items()}

    def validate_plugin_config(
        self: Self, plugin_id: str, config_data: dict[str, Any]
    ) -> BaseModel:
        """Validate config data against the schema registered for a plugin."""
        decl = self._declarations.get(plugin_id)
        if decl is None:
            raise KeyError(
                f"No configuration schema registered for plugin: {plugin_id}"
            )
        return decl.schema_model.model_validate(config_data)
