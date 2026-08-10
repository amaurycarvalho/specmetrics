"""Registry for named plugin capabilities."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Self


class CapabilityRegistry:
    """Registry that maps capability names to handler functions."""

    def __init__(self: Self) -> None:
        """Initialize an empty capability registry."""
        self._capabilities: dict[str, dict[str, Any]] = {}

    def register(
        self: Self,
        name: str,
        description: str,
        handler: Callable,
        metadata: dict | None = None,
    ) -> None:
        """Register a capability with the given name and handler."""
        self._capabilities[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "metadata": metadata or {},
        }

    def get_capability(self: Self, name: str) -> dict | None:
        """Return the capability metadata for the given name."""
        return self._capabilities.get(name)

    def list_capabilities(self: Self) -> list[dict]:
        """Return all registered capabilities."""
        return list(self._capabilities.values())

    def remove(self: Self, name: str) -> None:
        """Remove the capability with the given name."""
        self._capabilities.pop(name, None)


_capability_registry: CapabilityRegistry | None = None


def get_capability_registry() -> CapabilityRegistry:
    """Return the process-wide capability registry singleton."""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()
    return _capability_registry
