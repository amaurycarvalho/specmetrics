from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass
class PluginConfigDeclaration:
    plugin_id: str
    schema_model: type[BaseModel]


class PluginConfigCollector:
    def __init__(self) -> None:
        self._declarations: dict[str, PluginConfigDeclaration] = {}

    def register(self, plugin_id: str, schema_model: type[BaseModel]) -> None:
        self._declarations[plugin_id] = PluginConfigDeclaration(
            plugin_id=plugin_id,
            schema_model=schema_model,
        )

    @property
    def declarations(self) -> dict[str, PluginConfigDeclaration]:
        return dict(self._declarations)

    def build_merged_schemas(self) -> dict[str, type[BaseModel]]:
        return {pid: decl.schema_model for pid, decl in self._declarations.items()}

    def validate_plugin_config(
        self, plugin_id: str, config_data: dict[str, Any]
    ) -> BaseModel:
        decl = self._declarations.get(plugin_id)
        if decl is None:
            raise KeyError(f"No configuration schema registered for plugin: {plugin_id}")
        return decl.schema_model.model_validate(config_data)
