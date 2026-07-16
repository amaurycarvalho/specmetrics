from __future__ import annotations


from specmetrics.infrastructure.config.loader import Loader


class TestLoader:
    def test_discover_sources_no_files(self, tmp_path):
        loader = Loader()
        sources = loader.discover_sources(tmp_path)
        assert len(sources) == 0  # no files in temp dir, env added by ConfigurationSystem

    def test_expand_env_vars(self, monkeypatch):
        monkeypatch.setenv("HOME", "/home/test")
        loader = Loader()
        result = loader._expand_env_vars("$HOME/config.yml")
        assert result == "/home/test/config.yml"
