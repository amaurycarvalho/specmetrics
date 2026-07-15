from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import structlog

from .events import EventType
from .handler_registry import EventHandler, HandlerRegistry
from .plugin_metadata import PluginMetadata, PluginStatus

logger = structlog.get_logger(__name__)


@dataclass
class PluginDescriptor:
    metadata: PluginMetadata
    entry_point_name: str
    status: PluginStatus = PluginStatus.PENDING
    validation_errors: list[str] = field(default_factory=list)


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginDescriptor] = {}
        self._by_event_type: dict[EventType, list[PluginDescriptor]] = {}
        self._by_plugin_type: dict[str, list[PluginDescriptor]] = {}

    def register(self, descriptor: PluginDescriptor) -> None:
        existing = self._plugins.get(descriptor.metadata.id)
        if existing is not None:
            logger.warning(
                "duplicate_plugin_id",
                plugin_id=descriptor.metadata.id,
                previous_status=existing.status.value,
            )

        self._plugins[descriptor.metadata.id] = descriptor

        for et in descriptor.metadata.handled_event_types:
            if et not in self._by_event_type:
                self._by_event_type[et] = []
            self._by_event_type[et].append(descriptor)

        pt_key = descriptor.metadata.plugin_type.value
        if pt_key not in self._by_plugin_type:
            self._by_plugin_type[pt_key] = []
        self._by_plugin_type[pt_key].append(descriptor)

    def get_handler(self, event_type: EventType) -> Optional[EventHandler]:
        descriptors = self._by_event_type.get(event_type)
        if not descriptors:
            return None
        for d in descriptors:
            if d.status == PluginStatus.REGISTERED and d.metadata.handler_factory is not None:
                return d.metadata.handler_factory()
        return None

    def get_handlers(self, event_type: EventType) -> list[EventHandler]:
        descriptors = self._by_event_type.get(event_type, [])
        result: list[EventHandler] = []
        for d in descriptors:
            if d.status == PluginStatus.REGISTERED and d.metadata.handler_factory is not None:
                result.append(d.metadata.handler_factory())
        return result

    def list_plugins(self) -> list[PluginDescriptor]:
        return list(self._plugins.values())

    def get_by_type(self, plugin_type: str) -> list[PluginDescriptor]:
        return list(self._by_plugin_type.get(plugin_type, []))

    def install_handlers(self, handler_registry: HandlerRegistry) -> None:
        for descriptor in self._plugins.values():
            if descriptor.status != PluginStatus.REGISTERED:
                continue
            for et in descriptor.metadata.handled_event_types:
                handler = descriptor.metadata.handler_factory
                if handler is not None:
                    handler_registry.register(handler())
