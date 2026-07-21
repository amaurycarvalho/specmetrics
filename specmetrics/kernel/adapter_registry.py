from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog

from .adapter_interface import Document, SpecificationAdapter
from .plugin_metadata import PluginType
from .plugin_registry import PluginRegistry

logger = structlog.get_logger(__name__)


def _is_adapter(obj: object) -> bool:
    return hasattr(obj, "scan") and hasattr(obj, "supports")


class AdapterRegistry:
    """Convenience wrapper around F02 PluginRegistry for adapter-specific lookups.

    Provides methods to find, list, and execute scans across all registered
    specification adapters.
    """

    def __init__(self, plugin_registry: PluginRegistry) -> None:
        self._plugin_registry = plugin_registry

    def list_adapters(self) -> list[SpecificationAdapter]:
        """Return all registered adapter instances."""
        descriptors = self._plugin_registry.get_by_type(PluginType.ADAPTER.value)
        adapters: list[SpecificationAdapter] = []
        for d in descriptors:
            if (
                d.status.value == "registered"
                and d.metadata.handler_factory is not None
            ):
                handler = d.metadata.handler_factory()
                if _is_adapter(handler):
                    adapters.append(handler)
        return adapters

    def find_adapter(self, path: Path) -> Optional[SpecificationAdapter]:
        """Find the first adapter that supports the given path."""
        for adapter in self.list_adapters():
            try:
                if adapter.supports(path):
                    return adapter
            except Exception:
                logger.warning("adapter_supports_failed", path=str(path))
        return None

    def scan_all(self, path: Path) -> dict[str, list[Document]]:
        """Run scan() on all adapters that support the given path.

        Returns a dict mapping adapter IDs to their scan results.
        """
        result: dict[str, list[Document]] = {}
        for descriptor in self._plugin_registry.get_by_type(PluginType.ADAPTER.value):
            if descriptor.status.value != "registered":
                continue
            factory = descriptor.metadata.handler_factory
            if factory is None:
                continue
            adapter = factory()
            if not _is_adapter(adapter):
                continue
            try:
                if adapter.supports(path):
                    result[descriptor.metadata.id] = adapter.scan(path)
            except Exception:
                logger.warning(
                    "adapter_scan_all_supports_failed",
                    adapter_id=descriptor.metadata.id,
                    path=str(path),
                )
        return result
