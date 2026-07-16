from __future__ import annotations

from specmetrics.infrastructure.config.schema import (
    ConfigProvider,
    CoreConfig,
    LoggingSettings,
    PipelineSettings,
)


class TestCoreConfig:
    def test_defaults(self):
        config = CoreConfig()
        assert config.pipeline.stage_timeout == 60
        assert config.pipeline.fail_fast is True
        assert config.logging.level == "info"
        assert config.security.api_key is None

    def test_custom_values(self):
        config = CoreConfig(
            pipeline=PipelineSettings(stage_timeout=120, fail_fast=False),
            logging=LoggingSettings(level="debug"),
        )
        assert config.pipeline.stage_timeout == 120
        assert config.pipeline.fail_fast is False
        assert config.logging.level == "debug"


class TestConfigProvider:
    def test_protocol_has_required_methods(self):
        methods = {"get", "get_model", "dump", "warnings"}
        protocol_methods = {
            name for name in dir(ConfigProvider) if not name.startswith("_")
        }
        assert methods.issubset(protocol_methods)
