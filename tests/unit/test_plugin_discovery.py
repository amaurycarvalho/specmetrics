import sys
from unittest.mock import patch

import pytest

from specmetrics.kernel import (
    EventType,
    PluginDiscovery,
    PluginMetadata,
    PluginStatus,
    PluginType,
    load_plugins,
)
from specmetrics.kernel.plugin_registry import PluginRegistry
from specmetrics.kernel.plugin_validation import PluginValidator


def _mock_entry_point(ep_name: str, metadata: PluginMetadata):
    class MockEntryPoint:
        name = ep_name
        group = "specmetrics.plugins"

        def load(self):
            return lambda: metadata

    return MockEntryPoint()


class TestPluginDiscovery:
    def test_scans_specmetrics_plugins_group(self) -> None:
        meta = PluginMetadata(
            id="test-plugin",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
        )
        mock_ep = _mock_entry_point("test-plugin", meta)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[mock_ep]):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        assert len(descriptors) == 1
        assert descriptors[0].metadata.id == "test-plugin"
        assert descriptors[0].status == PluginStatus.PENDING

    def test_handles_empty_discovery(self) -> None:
        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[]):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        assert descriptors == []

    def test_loads_factory_function_and_retrieves_metadata(self) -> None:
        meta = PluginMetadata(
            id="factory-plugin",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
            handled_event_types=(EventType.REPOSITORY_LOADED,),
        )
        mock_ep = _mock_entry_point("factory-plugin", meta)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[mock_ep]):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        assert descriptors[0].metadata.handled_event_types == (EventType.REPOSITORY_LOADED,)
        assert descriptors[0].metadata.api_version == "1.0.0"

    def test_discovers_multiple_plugins(self) -> None:
        meta_a = PluginMetadata(id="plugin-a", api_version="1.0.0", plugin_type=PluginType.ADAPTER)
        meta_b = PluginMetadata(id="plugin-b", api_version="1.0.0", plugin_type=PluginType.SEMANTIC)
        ep_a = _mock_entry_point("plugin-a", meta_a)
        ep_b = _mock_entry_point("plugin-b", meta_b)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[ep_a, ep_b]):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        assert len(descriptors) == 2
        ids = {d.metadata.id for d in descriptors}
        assert ids == {"plugin-a", "plugin-b"}

    def test_skips_plugin_when_factory_raises_exception(self) -> None:
        class FailingEntryPoint:
            name = "failing-plugin"
            group = "specmetrics.plugins"

            def load(self):
                raise ImportError("Module not found")

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[FailingEntryPoint()]):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        assert descriptors == []

    def test_skips_plugin_when_factory_returns_invalid_type(self) -> None:
        class BadEntryPoint:
            name = "bad-plugin"
            group = "specmetrics.plugins"

            def load(self):
                return lambda: "not a metadata object"

        meta = PluginMetadata(id="good-plugin", api_version="1.0.0", plugin_type=PluginType.ADAPTER)
        good_ep = _mock_entry_point("good-plugin", meta)

        with patch(
            "specmetrics.kernel.plugin_discovery.entry_points",
            return_value=[BadEntryPoint(), good_ep],
        ):
            discovery = PluginDiscovery()
            descriptors = discovery.scan()

        plugin_ids = [d.metadata.id for d in descriptors]
        assert "good-plugin" in plugin_ids
        assert len(descriptors) == 1

    def test_load_plugins_wires_discovery_validation_registry(self) -> None:
        meta = PluginMetadata(id="test-p", api_version="1.0.0", plugin_type=PluginType.ADAPTER)
        mock_ep = _mock_entry_point("test-p", meta)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[mock_ep]), \
             patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            registry = load_plugins(PluginRegistry(), PluginValidator())

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].status == PluginStatus.REGISTERED

    def test_load_plugins_rejects_incompatible_plugin(self) -> None:
        meta = PluginMetadata(id="bad-p", api_version="99.0.0", plugin_type=PluginType.ADAPTER)
        mock_ep = _mock_entry_point("bad-p", meta)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[mock_ep]):
            registry = load_plugins(PluginRegistry(), PluginValidator())

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].status == PluginStatus.REJECTED
