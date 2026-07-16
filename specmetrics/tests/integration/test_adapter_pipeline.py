from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.adapter_interface import (
    Document,
    SpecificationAdapter,
)
from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.handler_registry import HandlerRegistry
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import PipelineEngine
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginStatus, PluginType
from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry


class _MockAdapter:
    @property
    def supported_document_types(self) -> list[str]:
        return ["use_case", "business_rule"]

    def scan(self, path: Path) -> list[Document]:
        return [
            Document(
                id="uc-01",
                path="specs/uc-01.md",
                document_type="use_case",
                content="# Use Case 1\nDescription",
            )
        ]

    def supports(self, path: Path) -> bool:
        return True


class _AdapterHandler:
    def __init__(self, adapter: SpecificationAdapter) -> None:
        self._adapter = adapter

    @property
    def handled_event_type(self) -> EventType:
        return EventType.REPOSITORY_LOADED

    @property
    def handler_id(self) -> str:
        return "test-adapter-handler"

    @property
    def stage_name(self) -> str:
        return "adapter_stage"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        repo_path = event.payload.get("repository_path", Path("/tmp"))
        docs = self._adapter.scan(Path(repo_path))
        return event.context.with_stage_output("adapter_result", docs)


class _FailingAdapter:
    @property
    def supported_document_types(self) -> list[str]:
        return []

    def scan(self, path: Path) -> list[Document]:
        msg = "Intentional scan failure"
        raise RuntimeError(msg)

    def supports(self, path: Path) -> bool:
        return True


class _FailingAdapterHandler:
    def __init__(self, adapter: SpecificationAdapter) -> None:
        self._adapter = adapter

    @property
    def handled_event_type(self) -> EventType:
        return EventType.REPOSITORY_LOADED

    @property
    def handler_id(self) -> str:
        return "failing-adapter-handler"

    @property
    def stage_name(self) -> str:
        return "adapter_stage"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        return event.context


def _register_adapter_plugin(
    plugin_registry: PluginRegistry,
    plugin_id: str,
    adapter: SpecificationAdapter,
    handler_factory_override=None,
) -> None:
    factory = handler_factory_override or (lambda a=adapter: a)
    meta = PluginMetadata(
        id=plugin_id,
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=(EventType.REPOSITORY_LOADED,),
        handler_factory=factory,
    )
    descriptor = PluginDescriptor(
        metadata=meta,
        entry_point_name=plugin_id,
        status=PluginStatus.REGISTERED,
    )
    plugin_registry.register(descriptor)


class TestF02PluginIntegration:
    def test_mock_adapter_discovered_via_plugin_registry(self) -> None:
        plugin_reg = PluginRegistry()
        _register_adapter_plugin(plugin_reg, "test-adapter", _MockAdapter())

        descriptors = plugin_reg.get_by_type(PluginType.ADAPTER.value)
        assert len(descriptors) == 1
        assert descriptors[0].metadata.id == "test-adapter"
        assert descriptors[0].status == PluginStatus.REGISTERED

    def test_adapter_available_through_adapter_registry(self) -> None:
        plugin_reg = PluginRegistry()
        _register_adapter_plugin(plugin_reg, "test-adapter", _MockAdapter())

        adapter_reg = AdapterRegistry(plugin_reg)
        adapters = adapter_reg.list_adapters()
        assert len(adapters) == 1

        found = adapter_reg.find_adapter(Path("/any/repo"))
        assert found is not None
        docs = found.scan(Path("/any/repo"))
        assert len(docs) == 1
        assert docs[0].id == "uc-01"

    def test_adapter_scan_output_consumable_by_pipeline(self) -> None:
        handler_reg = HandlerRegistry()
        handler_reg.register(_AdapterHandler(_MockAdapter()))
        engine = PipelineEngine(handler_reg)

        ctx = PipelineContext(
            metadata={"repository_path": "/tmp/test-repo"},
        )
        result = engine.run(ctx)

        assert result.diagnostics is not None
        timings = result.diagnostics.stage_timings
        assert "adapter_stage" in timings
        assert timings["adapter_stage"].status.value == "completed"


class TestMultipleAdaptersCoexist:
    def test_two_adapters_coexist_and_each_processes_own_documents(self) -> None:
        class _AdapterForA:
            @property
            def supported_document_types(self) -> list[str]:
                return ["use_case"]

            def scan(self, path: Path) -> list[Document]:
                return [
                    Document(
                        id="a-doc",
                        path="a.md",
                        document_type="use_case",
                        content="Adapter A content",
                    )
                ]

            def supports(self, path: Path) -> bool:
                return "project-a" in str(path)

        class _AdapterForB:
            @property
            def supported_document_types(self) -> list[str]:
                return ["business_rule"]

            def scan(self, path: Path) -> list[Document]:
                return [
                    Document(
                        id="b-doc",
                        path="b.md",
                        document_type="business_rule",
                        content="Adapter B content",
                    )
                ]

            def supports(self, path: Path) -> bool:
                return "project-b" in str(path)

        plugin_reg = PluginRegistry()
        _register_adapter_plugin(plugin_reg, "adapter-a", _AdapterForA())
        _register_adapter_plugin(plugin_reg, "adapter-b", _AdapterForB())

        adapter_reg = AdapterRegistry(plugin_reg)
        adapters = adapter_reg.list_adapters()
        assert len(adapters) == 2

        found_a = adapter_reg.find_adapter(Path("/repo/project-a"))
        assert found_a is not None
        docs_a = found_a.scan(Path("/repo/project-a"))
        assert docs_a[0].id == "a-doc"

        found_b = adapter_reg.find_adapter(Path("/repo/project-b"))
        assert found_b is not None
        docs_b = found_b.scan(Path("/repo/project-b"))
        assert docs_b[0].id == "b-doc"

    def test_unknown_adapter_returns_none(self) -> None:
        class _StrictAdapter:
            @property
            def supported_document_types(self) -> list[str]:
                return ["use_case"]

            def scan(self, path: Path) -> list[Document]:
                return []

            def supports(self, path: Path) -> bool:
                return "strict-project" in str(path)

        plugin_reg = PluginRegistry()
        _register_adapter_plugin(plugin_reg, "strict", _StrictAdapter())

        adapter_reg = AdapterRegistry(plugin_reg)
        found = adapter_reg.find_adapter(Path("/repo/strict-project"))
        assert found is not None
        found = adapter_reg.find_adapter(Path("/repo/unrelated-project"))
        assert found is None
