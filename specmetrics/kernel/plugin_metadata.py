"""Metadata models describing installed specmetrics plugins."""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass

from .events import EventType
from .handler_registry import EventHandler


class PluginType(enum.Enum):
    """Categorizes the kind of functionality a plugin provides."""

    ADAPTER = "adapter"
    SEMANTIC = "semantic"
    MEASUREMENT = "measurement"
    EXPORTER = "exporter"
    PUBLISHER = "publisher"
    UNSPECIFIED = "unspecified"


class PluginStatus(enum.Enum):
    """Lifecycle status of a discovered plugin."""

    PENDING = "pending"
    REGISTERED = "registered"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PluginMetadata:
    """Describes a plugin's identity, capabilities, and entry point factory."""

    id: str
    api_version: str
    plugin_type: PluginType
    handled_event_types: tuple[EventType, ...] = ()
    handler_factory: Callable[[], EventHandler] | None = None
    name: str | None = None
    description: str | None = None
    author: str | None = None
    version: str | None = None
    dependencies: tuple[str, ...] = ()
