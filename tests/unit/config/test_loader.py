from __future__ import annotations

from specmetrics.infrastructure.config.loader import Loader


class TestLoader:
    def test_discover_sources_no_files(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / ".config"))
        loader = Loader()
        sources = loader.discover_sources(tmp_path)
        assert (
            len(sources) == 0
        )  # no files in temp dir, env added by ConfigurationSystem

    def test_expand_env_vars(self, monkeypatch):
        monkeypatch.setenv("HOME", "/home/test")
        loader = Loader()
        result = loader._expand_env_vars("$HOME/config.yml")
        assert result == "/home/test/config.yml"


from pathlib import Path

from specmetrics.infrastructure.config.loader import ConfigurationSystem
from specmetrics.infrastructure.config.resolver import Resolver
from specmetrics.infrastructure.config.schema import CoreConfig


class TestLoaderXdgHome:
    """Kills survivors in ``Loader._get_xdg_config_home`` (mutmut_9..10)."""

    def test_default_xdg_config_home(self, monkeypatch) -> None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        loader = Loader()
        assert loader._get_xdg_config_home() == Path.home() / ".config"


class TestConfigurationSystemInit:
    """Kills survivors in ``ConfigurationSystem.__init__`` (mutmut_2..8)."""

    def test_project_root_preserved(self, tmp_path) -> None:
        system = ConfigurationSystem(project_root=tmp_path)
        assert system._project_root == tmp_path

    def test_project_root_defaults_to_cwd(self, monkeypatch) -> None:
        system = ConfigurationSystem(project_root=None)
        assert system._project_root == Path.cwd()

    def test_config_path_preserved(self, tmp_path) -> None:
        cfg_path = tmp_path / "custom.yml"
        system = ConfigurationSystem(config_path=cfg_path)
        assert system._config_path == cfg_path

    def test_resolver_instantiated(self) -> None:
        system = ConfigurationSystem()
        assert isinstance(system._resolver, Resolver)

    def test_config_starts_none(self) -> None:
        system = ConfigurationSystem()
        assert system._config is None


class TestResolveEnvConfigPath:
    """Kills survivors in ``ConfigurationSystem._resolve_env_config_path``."""

    def test_returns_existing_env_path(self, tmp_path, monkeypatch) -> None:
        cfg = tmp_path / "config.yml"
        cfg.write_text("{}")
        monkeypatch.setenv("SPECMETRICS_CONFIG_PATH", str(cfg))
        assert ConfigurationSystem._resolve_env_config_path() == cfg

    def test_none_when_unset(self, monkeypatch) -> None:
        monkeypatch.delenv("SPECMETRICS_CONFIG_PATH", raising=False)
        assert ConfigurationSystem._resolve_env_config_path() is None


class TestApplyValue:
    """Kills survivors in ``ConfigurationSystem._apply_value`` (mutmut_2..38)."""

    def test_sets_nested_field_with_coercion(self) -> None:
        system = ConfigurationSystem()
        cfg = CoreConfig()
        system._apply_value(cfg, "pipeline.stage_timeout", "30")
        assert cfg.pipeline.stage_timeout == 30

    def test_passthrough_value_on_coercion_failure(self) -> None:
        system = ConfigurationSystem()
        cfg = CoreConfig()
        system._apply_value(cfg, "pipeline.stage_timeout", "abc")
        assert cfg.pipeline.stage_timeout == "abc"
