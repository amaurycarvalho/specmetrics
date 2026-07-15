from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable, Optional

from .events import EventType
from .handler_registry import EventHandler


class PluginType(enum.Enum):
    ADAPTER = "adapter"
    SEMANTIC = "semantic"
    MEASUREMENT = "measurement"
    EXPORTER = "exporter"
    PUBLISHER = "publisher"
    UNSPECIFIED = "unspecified"


class PluginStatus(enum.Enum):
    PENDING = "pending"
    REGISTERED = "registered"
    REJECTED = "rejected"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class PluginMetadata:
    id: str
    api_version: str
    plugin_type: PluginType
    handled_event_types: tuple[EventType, ...] = ()
    handler_factory: Optional[Callable[[], EventHandler]] = None
    name: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
