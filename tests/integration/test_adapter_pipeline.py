from __future__ import annotations

from pathlib import Path

import pytest

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginStatus, PluginType
from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry


class _MockAdapter:
    def __init__(
        self, adapter_id: str, supported_paths: list[str] | None = None
    ) -> None:
        self._adapter_id = adapter_id
        self._supported_paths = supported_paths or []

    def supports(self, path: Path) -> bool:
        return str(path) in self._supported_paths

    def scan(self, repository_path: Path) -> list[Document]:
        return [
            Document(
                id=f"{self._adapter_id}-doc-1",
                path="specs/req.md",
                document_type="section",
                content="# Requirement",
                metadata={"framework": "mock"},
            )
        ]


@pytest.fixture
def plugin_registry() -> PluginRegistry:
    return PluginRegistry()


@pytest.fixture
def adapter_registry(plugin_registry: PluginRegistry) -> AdapterRegistry:
    return AdapterRegistry(plugin_registry)


class TestAdapterPipelineIntegration:
    def test_mock_adapter_registered_via_f02_is_available_through_adapter_registry(
        self, plugin_registry: PluginRegistry, adapter_registry: AdapterRegistry
    ):
        adapter = _MockAdapter("mock-adapter", supported_paths=["/test/repo"])
        metadata = PluginMetadata(
            id="mock-adapter",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
            handler_factory=lambda: adapter,
        )
        descriptor = PluginDescriptor(
            metadata=metadata,
            entry_point_name="mock-adapter",
            status=PluginStatus.REGISTERED,
        )
        plugin_registry.register(descriptor)
        adapters = adapter_registry.list_adapters()
        assert len(adapters) == 1
        found = adapter_registry.find_adapter(Path("/test/repo"))
        assert found is not None

    def test_adapter_scan_output_consumable_by_pipeline(
        self, plugin_registry: PluginRegistry, adapter_registry: AdapterRegistry
    ):
        adapter = _MockAdapter("pipeline-adapter", supported_paths=["/test/pipeline"])
        metadata = PluginMetadata(
            id="pipeline-adapter",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
            handler_factory=lambda: adapter,
        )
        descriptor = PluginDescriptor(
            metadata=metadata,
            entry_point_name="pipeline-adapter",
            status=PluginStatus.REGISTERED,
        )
        plugin_registry.register(descriptor)
        results = adapter_registry.scan_all(Path("/test/pipeline"))
        assert "pipeline-adapter" in results
        docs = results["pipeline-adapter"]
        assert len(docs) == 1
        doc = docs[0]
        assert isinstance(doc, Document)
        assert doc.id == "pipeline-adapter-doc-1"
        assert doc.path == "specs/req.md"
        assert doc.document_type == "section"

    def test_two_adapters_coexist_and_each_processes_own_documents(
        self, plugin_registry: PluginRegistry, adapter_registry: AdapterRegistry
    ):
        adapter_a = _MockAdapter("adapter-a", supported_paths=["/repo/a"])
        adapter_b = _MockAdapter("adapter-b", supported_paths=["/repo/b"])
        for aid, aobj in [("adapter-a", adapter_a), ("adapter-b", adapter_b)]:
            metadata = PluginMetadata(
                id=aid,
                api_version="1.0.0",
                plugin_type=PluginType.ADAPTER,
                handler_factory=lambda a=aobj: a,
            )
            descriptor = PluginDescriptor(
                metadata=metadata,
                entry_point_name=aid,
                status=PluginStatus.REGISTERED,
            )
            plugin_registry.register(descriptor)
        found_a = adapter_registry.find_adapter(Path("/repo/a"))
        found_b = adapter_registry.find_adapter(Path("/repo/b"))
        assert found_a is not None
        assert found_b is not None
