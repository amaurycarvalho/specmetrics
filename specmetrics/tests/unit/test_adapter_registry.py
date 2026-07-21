from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.adapter_interface import (
    Document,
    SpecificationAdapter,
)
from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginStatus, PluginType
from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry


class _AdapterA:
    @property
    def supported_document_types(self) -> list[str]:
        return ["use_case"]

    def scan(self, path: Path) -> list[Document]:
        return [
            Document(
                id="a-doc",
                path=str(path / "a.md"),
                document_type="use_case",
                content="from A",
            )
        ]

    def supports(self, path: Path) -> bool:
        return "project-a" in str(path)


class _AdapterB:
    @property
    def supported_document_types(self) -> list[str]:
        return ["business_rule"]

    def scan(self, path: Path) -> list[Document]:
        return [
            Document(
                id="b-doc",
                path=str(path / "b.md"),
                document_type="business_rule",
                content="from B",
            )
        ]

    def supports(self, path: Path) -> bool:
        return "project-b" in str(path)


def _make_plugin_registry(
    *adapters: tuple[str, SpecificationAdapter],
) -> PluginRegistry:
    reg = PluginRegistry()
    for aid, adapter in adapters:

        def factory(a=adapter):
            return a

        meta = PluginMetadata(
            id=aid,
            api_version="1.0.0",
            plugin_type=PluginType.ADAPTER,
            handler_factory=factory,
        )
        desc = PluginDescriptor(
            metadata=meta,
            entry_point_name=aid,
            status=PluginStatus.REGISTERED,
        )
        reg.register(desc)
    return reg


class TestAdapterRegistry:
    def test_list_adapters_returns_all_registered(self) -> None:
        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
            ("adapter-b", _AdapterB()),
        )
        registry = AdapterRegistry(plugin_reg)
        adapters = registry.list_adapters()
        assert len(adapters) == 2

    def test_list_adapters_empty_when_no_adapters(self) -> None:
        plugin_reg = PluginRegistry()
        registry = AdapterRegistry(plugin_reg)
        assert registry.list_adapters() == []

    def test_find_adapter_returns_correct_adapter(self) -> None:
        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
            ("adapter-b", _AdapterB()),
        )
        registry = AdapterRegistry(plugin_reg)
        found = registry.find_adapter(Path("/repo/project-a"))
        assert found is not None
        docs = found.scan(Path("/repo/project-a"))
        assert docs[0].id == "a-doc"

    def test_find_adapter_returns_none_when_no_match(self) -> None:
        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
        )
        registry = AdapterRegistry(plugin_reg)
        found = registry.find_adapter(Path("/repo/unknown-project"))
        assert found is None

    def test_find_adapter_returns_first_match_in_registration_order(self) -> None:
        class _BothMatch:
            @property
            def supported_document_types(self) -> list[str]:
                return ["use_case"]

            def scan(self, path: Path) -> list[Document]:
                return [
                    Document(
                        id="first",
                        path="first.md",
                        document_type="use_case",
                        content="first",
                    )
                ]

            def supports(self, path: Path) -> bool:
                return True

        class _AlsoMatch:
            @property
            def supported_document_types(self) -> list[str]:
                return ["business_rule"]

            def scan(self, path: Path) -> list[Document]:
                return [
                    Document(
                        id="second",
                        path="second.md",
                        document_type="business_rule",
                        content="second",
                    )
                ]

            def supports(self, path: Path) -> bool:
                return True

        plugin_reg = _make_plugin_registry(
            ("first", _BothMatch()),
            ("second", _AlsoMatch()),
        )
        registry = AdapterRegistry(plugin_reg)
        found = registry.find_adapter(Path("/any/path"))
        assert found is not None
        docs = found.scan(Path("/any/path"))
        assert docs[0].id == "first"

    def test_scan_all_returns_results_from_all_supporting_adapters(self) -> None:
        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
            ("adapter-b", _AdapterB()),
        )
        registry = AdapterRegistry(plugin_reg)

        result = registry.scan_all(Path("/repo/project-a"))
        assert "adapter-a" in result
        assert "adapter-b" not in result
        assert len(result["adapter-a"]) == 1

    def test_scan_all_with_multiple_adapters_returns_combined(self) -> None:
        class _MatchesAll:
            @property
            def supported_document_types(self) -> list[str]:
                return ["use_case"]

            def scan(self, path: Path) -> list[Document]:
                return [
                    Document(
                        id="all", path="all.md", document_type="use_case", content="all"
                    )
                ]

            def supports(self, path: Path) -> bool:
                return True

        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
            ("adapter-universal", _MatchesAll()),
        )
        registry = AdapterRegistry(plugin_reg)

        result = registry.scan_all(Path("/repo/project-a"))
        assert "adapter-a" in result
        assert "adapter-universal" in result

    def test_scan_all_empty_when_no_adapters_support_path(self) -> None:
        plugin_reg = _make_plugin_registry(
            ("adapter-a", _AdapterA()),
        )
        registry = AdapterRegistry(plugin_reg)
        result = registry.scan_all(Path("/nonexistent"))
        assert result == {}
