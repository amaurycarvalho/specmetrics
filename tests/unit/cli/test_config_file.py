from __future__ import annotations

from pathlib import Path

from specmetrics.cli import _config_file


class TestUserConfigPaths:
    def test_get_user_config_dir_with_xdg(self, monkeypatch, tmp_path):
        xdg = tmp_path / "cfg"
        monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
        assert _config_file.get_user_config_dir() == xdg / "specmetrics"

    def test_get_user_config_dir_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert _config_file.get_user_config_dir() == tmp_path / ".config" / "specmetrics"

    def test_get_user_config_path_prefers_yml(self, monkeypatch, tmp_path):
        cfg_dir = tmp_path / "specmetrics"
        cfg_dir.mkdir()
        (cfg_dir / "config.json").write_text("{}")
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.json"

    def test_get_user_config_path_single_exists(self, monkeypatch, tmp_path):
        cfg_dir = tmp_path / "spec"
        cfg_dir.mkdir()
        (cfg_dir / "config.yml").write_text("{}")
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.yml"

    def test_get_user_config_path_fallback(self, monkeypatch, tmp_path):
        cfg_dir = tmp_path / "spec"
        cfg_dir.mkdir()
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.yml"


class TestReadWriteYaml:
    def test_read_missing_returns_empty(self, tmp_path):
        assert _config_file.read_config_yaml(tmp_path / "nope.yml") == {}

    def test_read_roundtrip(self, tmp_path):
        target = tmp_path / "sub" / "cfg.yml"
        _config_file.write_config_yaml(target, {"a": 1, "b": {"c": 2}})
        assert _config_file.read_config_yaml(target) == {"a": 1, "b": {"c": 2}}

    def test_read_non_mapping_returns_empty(self, tmp_path):
        target = tmp_path / "cfg.yml"
        target.write_text("- one\n- two\n")
        assert _config_file.read_config_yaml(target) == {}


class TestNestedHelpers:
    def test_set_and_get_nested(self):
        data = {}
        _config_file.set_nested(data, ("a", "b", "c"), 42)
        assert data == {"a": {"b": {"c": 42}}}
        assert _config_file.get_nested(data, ("a", "b", "c")) == 42

    def test_get_nested_missing(self):
        assert _config_file.get_nested({}, ("a", "b")) is None
        assert _config_file.get_nested({"a": {"b": 1}}, ("a", "x")) is None
        assert _config_file.get_nested(5, ("a",)) is None


class TestWriteLLMConfig:
    def test_writes_only_non_none(self, monkeypatch, tmp_path, capsys):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        target = cfg_dir / "config.yml"
        monkeypatch.setattr(_config_file, "get_user_config_path", lambda: target)

        _config_file.write_llm_config(provider="chatgpt", api_key=None, model="m1")

        data = _config_file.read_config_yaml(target)
        llm = data["plugins"]["extraction_stage"]["llm"]
        assert llm.get("provider") == "chatgpt"
        assert llm.get("model") == "m1"
        assert "api_key" not in llm
        assert "Updated" in capsys.readouterr().out

    def test_preserves_existing(self, monkeypatch, tmp_path):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        target = cfg_dir / "config.yml"
        target.write_text("key: value\n")
        monkeypatch.setattr(_config_file, "get_user_config_path", lambda: target)

        _config_file.write_llm_config(provider="gemini")

        data = _config_file.read_config_yaml(target)
        assert data["key"] == "value"


class TestSetProviderNone:
    def test_clears_llm_keys_and_sets_none(self, monkeypatch, tmp_path, capsys):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        target = cfg_dir / "config.yml"
        target.write_text(
            "plugins:\n  extraction_stage:\n    llm:\n      provider: gemini\n"
            "      api_key: secret\n"
        )
        monkeypatch.setattr(_config_file, "get_user_config_path", lambda: target)

        _config_file.set_provider_none()

        data = _config_file.read_config_yaml(target)
        llm = data["plugins"]["extraction_stage"]["llm"]
        assert llm["provider"] == "none"
        assert "api_key" not in llm
        assert "api_url" not in llm
        assert "model" not in llm
        captured = capsys.readouterr().out
        assert "LLM provider set to 'none'" in captured

    def test_no_llm_section_still_sets_none(self, tmp_path, monkeypatch):
        cfg_dir = tmp_path / "cfg"
        cfg_dir.mkdir()
        target = cfg_dir / "config.yml"
        target.write_text("other: 1\n")
        monkeypatch.setattr(
            _config_file, "get_user_config_path", lambda: target
        )

        _config_file.set_provider_none()

        data = _config_file.read_config_yaml(target)
        assert data["other"] == 1
        llm = data["plugins"]["extraction_stage"]["llm"]
        assert llm["provider"] == "none"