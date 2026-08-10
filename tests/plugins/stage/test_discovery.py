from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType
from specmetrics.plugins.stage.discovery import (
    AdapterDiscoveryHandler,
    create_adapter_discovery_metadata,
)


class TestAdapterDiscoveryHandlerInit:
    def test_handled_event_type(self) -> None:
        handler = AdapterDiscoveryHandler()
        assert handler.handled_event_type == EventType.REPOSITORY_LOADED

    def test_handler_id(self) -> None:
        handler = AdapterDiscoveryHandler()
        assert handler.handler_id == "adapter_discovery"

    def test_stage_name(self) -> None:
        handler = AdapterDiscoveryHandler()
        assert handler.stage_name == "discovery"


class TestCreateAdapterDiscoveryMetadata:
    def test_metadata_fields(self) -> None:
        meta = create_adapter_discovery_metadata()
        assert isinstance(meta, PluginMetadata)
        assert meta.id == "adapter_discovery"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.SEMANTIC
        assert meta.handled_event_types == (EventType.REPOSITORY_LOADED,)
        assert meta.name == "Adapter Discovery Stage"
        assert meta.version == "0.1.0"
        handler = meta.handler_factory()
        assert isinstance(handler, AdapterDiscoveryHandler)
