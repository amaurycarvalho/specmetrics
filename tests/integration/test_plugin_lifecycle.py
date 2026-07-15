from unittest.mock import patch

from specmetrics.kernel import (
    EventType,
    HandlerRegistry,
    PluginMetadata,
    PluginRegistry,
    PluginStatus,
    PluginType,
    PluginValidator,
    PipelineContext,
    PipelineEngine,
    load_plugins,
)


def _mock_ep(ep_name: str, metadata: PluginMetadata):
    class MockEntryPoint:
        name = ep_name
        group = "specmetrics.plugins"

        def load(self):
            return lambda: metadata

    return MockEntryPoint()


class _EchoHandler:
    handled_event_type = EventType.REPOSITORY_LOADED
    handler_id = "echo"
    stage_name = "Echo"

    def handle(self, event):
        return event.context


class TestPluginLifecycle:
    def test_plugin_discovers_validates_and_registers(self) -> None:
        meta = PluginMetadata(
            id="lifecycle-test",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
        )
        mock_ep = _mock_ep("lifecycle-test", meta)

        with patch("specmetrics.kernel.plugin_discovery.entry_points", return_value=[mock_ep]), \
             patch("specmetrics.kernel.plugin_validation.version", return_value="1.0.0"):
            registry = load_plugins(PluginRegistry(), PluginValidator())

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].metadata.id == "lifecycle-test"
        assert plugins[0].status == PluginStatus.REGISTERED

    def test_broken_plugin_skipped_healthy_one_registers(self) -> None:
        class BrokenEntryPoint:
            name = "broken"
            group = "specmetrics.plugins"

            def load(self):
                raise ImportError("broken module")

        healthy_meta = PluginMetadata(
            id="healthy",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
        )
        healthy_ep = _mock_ep("healthy", healthy_meta)

        with patch(
            "specmetrics.kernel.plugin_discovery.entry_points",
            return_value=[BrokenEntryPoint(), healthy_ep],
        ):
            registry = load_plugins(PluginRegistry(), PluginValidator())

        plugins = registry.list_plugins()
        plugin_ids = [p.metadata.id for p in plugins]
        assert "healthy" in plugin_ids
        assert len(plugins) == 1

    def test_pipeline_engine_uses_registry_handlers(self) -> None:
        handler_registry = HandlerRegistry()
        plugin_registry = PluginRegistry()

        desc_meta = PluginMetadata(
            id="repo-loader",
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
            handled_event_types=(EventType.REPOSITORY_LOADED,),
            handler_factory=lambda: _EchoHandler(),
        )
        from specmetrics.kernel.plugin_registry import PluginDescriptor

        desc = PluginDescriptor(
            metadata=desc_meta,
            entry_point_name="repo-loader",
            status=PluginStatus.REGISTERED,
        )
        plugin_registry.register(desc)
        plugin_registry.install_handlers(handler_registry)

        engine = PipelineEngine(handler_registry)
        ctx = engine.run(PipelineContext())

        published = [e.event_type for e in ctx.published_events]
        assert EventType.REPOSITORY_LOADED in published
        assert EventType.PIPELINE_COMPLETED in published

    def test_rejected_plugin_not_available_to_pipeline(self) -> None:
        handler_registry = HandlerRegistry()
        plugin_registry = PluginRegistry()

        rejected_meta = PluginMetadata(
            id="bad-version",
            api_version="99.0.0",
            plugin_type=PluginType.ADAPTER,
            handled_event_types=(EventType.REPOSITORY_LOADED,),
            handler_factory=lambda: _EchoHandler(),
        )
        from specmetrics.kernel.plugin_registry import PluginDescriptor

        desc = PluginDescriptor(
            metadata=rejected_meta,
            entry_point_name="bad-version",
            status=PluginStatus.REJECTED,
            validation_errors=["Incompatible API version"],
        )
        plugin_registry.register(desc)
        plugin_registry.install_handlers(handler_registry)

        assert EventType.REPOSITORY_LOADED not in handler_registry.registered_types
