from __future__ import annotations

from specmetrics.infrastructure.config.loader import ConfigurationSystem
from specmetrics.infrastructure.config.schema import CoreConfig


class TestConfigurationSystem:
    def test_load_with_defaults(self, tmp_path):
        system = ConfigurationSystem(project_root=tmp_path)
        provider = system.load()
        config = provider.get_model(CoreConfig)
        assert config.pipeline.stage_timeout == 60
        assert config.logging.level == "info"
