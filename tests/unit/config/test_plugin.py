from __future__ import annotations

from pydantic import BaseModel

from specmetrics.infrastructure.config.plugin import PluginConfigCollector


class TestPluginConfigCollector:
    def test_register_and_declare(self):
        collector = PluginConfigCollector()
        collector.register("test_plugin", BaseModel)
        assert "test_plugin" in collector.declarations

    def test_build_merged_schemas(self):
        collector = PluginConfigCollector()

        class MyConfig(BaseModel):
            api_key: str

        collector.register("my_plugin", MyConfig)
        schemas = collector.build_merged_schemas()
        assert schemas["my_plugin"] == MyConfig

    def test_validate_plugin_config(self):
        collector = PluginConfigCollector()

        class MyConfig(BaseModel):
            api_key: str

        collector.register("my_plugin", MyConfig)
        result = collector.validate_plugin_config(
            "my_plugin", {"api_key": "test-key"}
        )
        assert result.api_key == "test-key"
