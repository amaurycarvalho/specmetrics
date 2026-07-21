from specmetrics.kernel import (
    EventType,
    HandlerRegistry,
    PluginDescriptor,
    PluginMetadata,
    PluginRegistry,
    PluginStatus,
    PluginType,
)


def _make_descriptor(
    plugin_id: str = "test-p",
    plugin_type: PluginType = PluginType.ADAPTER,
    handled: tuple = (EventType.REPOSITORY_LOADED,),
    status: PluginStatus = PluginStatus.REGISTERED,
    with_handler: bool = True,
) -> PluginDescriptor:
    def _make_handler() -> _FakeHandler:
        return _FakeHandler()

    handler_factory = None
    if with_handler:
        handler_factory = _make_handler
    meta = PluginMetadata(
        id=plugin_id,
        api_version="1.0.0",
        plugin_type=plugin_type,
        handled_event_types=handled,
        handler_factory=handler_factory,
    )
    return PluginDescriptor(
        metadata=meta,
        entry_point_name=plugin_id,
        status=status,
    )


class _FakeHandler:
    handled_event_type = EventType.REPOSITORY_LOADED
    handler_id = "fake"
    stage_name = "FakeStage"

    def handle(self, event):
        return event.context


class TestPluginRegistry:
    def test_register_stores_descriptor(self) -> None:
        registry = PluginRegistry()
        desc = _make_descriptor("my-plugin")
        registry.register(desc)

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].metadata.id == "my-plugin"

    def test_get_handler_returns_handler_for_registered_event_type(self) -> None:
        registry = PluginRegistry()
        desc = _make_descriptor("p1")
        registry.register(desc)

        handler = registry.get_handler(EventType.REPOSITORY_LOADED)
        assert handler is not None
        assert handler.handler_id == "fake"

    def test_get_handler_returns_none_for_unregistered_event_type(self) -> None:
        registry = PluginRegistry()
        desc = _make_descriptor("p1")
        registry.register(desc)

        handler = registry.get_handler(EventType.DOCUMENTS_DISCOVERED)
        assert handler is None

    def test_get_handlers_returns_all_in_registration_order(self) -> None:
        registry = PluginRegistry()
        registry.register(_make_descriptor("p1"))
        registry.register(_make_descriptor("p2"))

        handlers = registry.get_handlers(EventType.REPOSITORY_LOADED)
        assert len(handlers) == 2

    def test_get_handlers_returns_empty_for_unregistered_type(self) -> None:
        registry = PluginRegistry()
        handlers = registry.get_handlers(EventType.TELEMETRY_PUBLISHED)
        assert handlers == []

    def test_install_handlers_populates_handler_registry(self) -> None:
        plugin_registry = PluginRegistry()
        plugin_registry.register(_make_descriptor("p1"))
        plugin_registry.register(_make_descriptor("p2"))

        handler_registry = HandlerRegistry()
        plugin_registry.install_handlers(handler_registry)

        assert EventType.REPOSITORY_LOADED in handler_registry.registered_types

    def test_install_handlers_skips_non_registered_plugins(self) -> None:
        plugin_registry = PluginRegistry()
        plugin_registry.register(_make_descriptor("p1", status=PluginStatus.REJECTED))
        plugin_registry.register(_make_descriptor("p2", status=PluginStatus.PENDING))

        handler_registry = HandlerRegistry()
        plugin_registry.install_handlers(handler_registry)

        assert EventType.REPOSITORY_LOADED not in handler_registry.registered_types

    def test_get_by_type_returns_matching_plugins(self) -> None:
        registry = PluginRegistry()
        registry.register(_make_descriptor("p1", plugin_type=PluginType.ADAPTER))
        registry.register(_make_descriptor("p2", plugin_type=PluginType.SEMANTIC))

        adapters = registry.get_by_type("adapter")
        assert len(adapters) == 1
        assert adapters[0].metadata.id == "p1"

    def test_load_plugins_isolates_errors(self) -> None:
        registry = PluginRegistry()
        registry.register(_make_descriptor("healthy", status=PluginStatus.REGISTERED))

        plugins = registry.list_plugins()
        assert len(plugins) == 1
        assert plugins[0].metadata.id == "healthy"
