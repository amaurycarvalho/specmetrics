from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from specmetrics.kernel.adapter_interface import Document, SpecificationAdapter
from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginStatus, PluginType
from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry


class _MockAdapter:
    def __init__(self, adapter_id: str, supported_paths: Optional[list[str]] = None) -> None:
        self._adapter_id = adapter_id
        self._supported_paths = supported_paths or []

    def supports(self, path: Path) -> bool:
        return str(path) in self._supported_paths

    def scan(self, repository_path: Path) -> list[Document]:
        return [
            Document(
                id=f"{self._adapter_id}-doc",
                path="specs/doc.md",
                document_type="section",
                content=f"# Doc from {self._adapter_id}",
            )
        ]


def _make_descriptor(adapter_id: str, supported_paths: Optional[list[str]] = None) -> PluginDescriptor:
    adapter = _MockAdapter(adapter_id, supported_paths)
    metadata = PluginMetadata(
        id=adapter_id,
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        handler_factory=lambda a=adapter: a,
    )
    return PluginDescriptor(metadata=metadata, entry_point_name=adapter_id, status=PluginStatus.REGISTERED)


@pytest.fixture
def registry() -> tuple[PluginRegistry, AdapterRegistry]:
    plugin_reg = PluginRegistry()
    adapter_reg = AdapterRegistry(plugin_reg)
    return plugin_reg, adapter_reg


class TestAdapterRegistry:
    def test_list_adapters_returns_all_registered(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a"))
        plugin_reg.register(_make_descriptor("adapter-b"))
        adapters = adapter_reg.list_adapters()
        assert len(adapters) == 2

    def test_find_adapter_returns_correct_adapter_for_path(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a", supported_paths=["/repo/a"]))
        plugin_reg.register(_make_descriptor("adapter-b", supported_paths=["/repo/b"]))
        found = adapter_reg.find_adapter(Path("/repo/a"))
        assert found is not None

    def test_find_adapter_returns_none_when_no_adapter_supports_path(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a", supported_paths=["/repo/a"]))
        found = adapter_reg.find_adapter(Path("/repo/unknown"))
        assert found is None

    def test_scan_all_returns_results_from_multiple_adapters(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a", supported_paths=["/repo/multi"]))
        plugin_reg.register(_make_descriptor("adapter-b", supported_paths=["/repo/multi"]))
        results = adapter_reg.scan_all(Path("/repo/multi"))
        assert len(results) == 2
        assert "adapter-a" in results
        assert "adapter-b" in results

    def test_two_adapters_find_adapter_returns_correct_one_for_each_path(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a", supported_paths=["/repo/a"]))
        plugin_reg.register(_make_descriptor("adapter-b", supported_paths=["/repo/b"]))
        found_a = adapter_reg.find_adapter(Path("/repo/a"))
        found_b = adapter_reg.find_adapter(Path("/repo/b"))
        assert found_a is not None
        assert found_b is not None

    def test_scan_all_with_two_adapters_returns_combined_results(self, registry: tuple[PluginRegistry, AdapterRegistry]):
        plugin_reg, adapter_reg = registry
        plugin_reg.register(_make_descriptor("adapter-a", supported_paths=["/repo/combo"]))
        plugin_reg.register(_make_descriptor("adapter-b", supported_paths=["/repo/combo"]))
        results = adapter_reg.scan_all(Path("/repo/combo"))
        assert len(results["adapter-a"]) == 1
        assert len(results["adapter-b"]) == 1
