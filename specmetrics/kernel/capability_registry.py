from __future__ import annotations

from typing import Any, Callable


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable,
        metadata: dict | None = None,
    ) -> None:
        self._capabilities[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "metadata": metadata or {},
        }

    def get_capability(self, name: str) -> dict | None:
        return self._capabilities.get(name)

    def list_capabilities(self) -> list[dict]:
        return list(self._capabilities.values())

    def remove(self, name: str) -> None:
        self._capabilities.pop(name, None)


_capability_registry: CapabilityRegistry | None = None


def get_capability_registry() -> CapabilityRegistry:
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()
    return _capability_registry
