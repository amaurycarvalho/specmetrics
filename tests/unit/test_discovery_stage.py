from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType
from specmetrics.plugins.stage.discovery import (
    AdapterDiscoveryHandler,
    create_adapter_discovery_metadata,
)


def _make_event(repository: str | None = None, metadata: dict | None = None):
    context = PipelineContext(
        execution_id=uuid4(), repository=repository, metadata=metadata or {}
    )
    return PipelineEvent(
        event_type=EventType.REPOSITORY_LOADED,
        publisher="test",
        payload={},
        context=context,
    )


class TestAdapterDiscoveryHandler:
    def test_identity_fields(self):
        handler = AdapterDiscoveryHandler()
        assert handler.handled_event_type == EventType.REPOSITORY_LOADED
        assert handler.handler_id == "adapter_discovery"
        assert handler.stage_name == "discovery"

    def test_handle_without_repository_returns_empty_documents(self):
        context = AdapterDiscoveryHandler().handle(_make_event(repository=None))
        output = context.adapter_result
        assert output == {"documents": []}

    def test_handle_without_adapter_registry_returns_empty_documents(self):
        context = AdapterDiscoveryHandler().handle(_make_event(repository="/repo"))
        output = context.adapter_result
        assert output == {"documents": []}

    def test_handle_collects_documents_and_adapter_keys(self):
        registry = MagicMock()
        registry.scan_all.return_value = {
            "adapter-a": ["doc-a1", "doc-a2"],
            "adapter-b": ["doc-b1"],
        }
        context = AdapterDiscoveryHandler().handle(
            _make_event(repository="/repo", metadata={"adapter_registry": registry})
        )
        registry.scan_all.assert_called_once_with("/repo")
        assert context.adapter_result == {
            "documents": ["doc-a1", "doc-a2", "doc-b1"],
            "adapters_used": ["adapter-a", "adapter-b"],
        }


class TestAdapterDiscoveryMetadata:
    def test_create_adapter_discovery_metadata_field_values(self):
        meta = create_adapter_discovery_metadata()
        assert isinstance(meta, PluginMetadata)
        assert meta.id == "adapter_discovery"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.SEMANTIC
        assert meta.handled_event_types == (EventType.REPOSITORY_LOADED,)
        assert meta.name == "Adapter Discovery Stage"
        assert (
            meta.description
            == "Discovers specification documents via registered adapters"
        )
        assert meta.version == "0.1.0"
        assert meta.handler_factory is not None
        handler = meta.handler_factory()
        assert isinstance(handler, AdapterDiscoveryHandler)
        assert handler.handler_id == "adapter_discovery"