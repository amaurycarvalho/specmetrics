from __future__ import annotations

from pathlib import Path

from specmetrics.cli import _config_file


class TestGetUserConfigPath:
    def test_prefers_existing_config_yml(self, tmp_path: Path, monkeypatch):
        """Kills get_user_config_path__mutmut_1/2 (config.yml name mutations)."""
        cfg_dir = tmp_path / "specmetrics"
        cfg_dir.mkdir()
        (cfg_dir / "config.yml").write_text("a: 1")
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.yml"

    def test_prefers_existing_config_yaml(self, tmp_path: Path, monkeypatch):
        """Kills get_user_config_path__mutmut_3/4 (config.yaml name mutations)."""
        cfg_dir = tmp_path / "specmetrics"
        cfg_dir.mkdir()
        (cfg_dir / "config.yaml").write_text("a: 1")
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.yaml"

    def test_defaults_to_config_yml_when_none_exist(self, tmp_path: Path, monkeypatch):
        """Targets get_user_config_path__mutmut_1/2/3/4 default return."""
        cfg_dir = tmp_path / "specmetrics"
        cfg_dir.mkdir()
        monkeypatch.setattr(_config_file, "get_user_config_dir", lambda: cfg_dir)
        assert _config_file.get_user_config_path() == cfg_dir / "config.yml"


class TestReadConfigYaml:
    def test_missing_file_returns_empty_dict(self, tmp_path: Path):
        """Targets read_config_yaml__mutmut_3/8/10 missing-file branch."""
        assert _config_file.read_config_yaml(tmp_path / "nope.yml") == {}

    def test_reads_yaml_as_plain_dict(self, tmp_path: Path):
        """Kills read_config_yaml__mutmut_3 (typ='safe' -> None)."""
        path = tmp_path / "config.yml"
        path.write_text("plugins:\n  llm:\n    provider: none\n")
        data = _config_file.read_config_yaml(path)
        assert type(data) is dict
        assert data == {"plugins": {"llm": {"provider": "none"}}}

    def test_reads_unicode_content(self, tmp_path: Path):
        """Targets read_config_yaml__mutmut_8/10 (read_text encoding)."""
        path = tmp_path / "config.yml"
        path.write_text("name: caf\u00e9\n", encoding="utf-8")
        assert _config_file.read_config_yaml(path) == {"name": "caf\u00e9"}

    def test_non_dict_yaml_returns_empty_dict(self, tmp_path: Path):
        """Targets read_config_yaml__mutmut_3 non-mapping fallback."""
        path = tmp_path / "config.yml"
        path.write_text("[1, 2]\n")
        assert _config_file.read_config_yaml(path) == {}


class TestWriteConfigYaml:
    def test_creates_nested_parent_directories(self, tmp_path: Path):
        """Kills write_config_yaml__mutmut_1/3/5 (mkdir parents=True mutations)."""
        path = tmp_path / "a" / "b" / "config.yml"
        _config_file.write_config_yaml(path, {"plugins": {"llm": {"provider": "none"}}})
        assert path.exists()
        assert _config_file.read_config_yaml(path) == {
            "plugins": {"llm": {"provider": "none"}}
        }

    def test_writes_nested_sequence_with_mapping_indent(self, tmp_path: Path):
        """Kills write_config_yaml__mutmut_8/11/14/15/16 (yaml.indent mutations)."""
        path = tmp_path / "config.yml"
        data = {"plugins": {"llm": {"model": "gpt", "providers": ["openai", "deepseek"]}}}
        _config_file.write_config_yaml(path, data)
        content = path.read_text(encoding="utf-8")
        # With mapping=2, sequence=4, offset=2 the list item sits under 'providers:'.
        assert "providers:" in content
        assert "\n      - openai" in content

    def test_writes_unicode_with_utf8_encoding(self, tmp_path: Path):
        """Targets write_config_yaml__mutmut_19/22/26 (open encoding)."""
        path = tmp_path / "config.yml"
        _config_file.write_config_yaml(path, {"name": "caf\u00e9"})
        assert "caf\u00e9" in path.read_text(encoding="utf-8")


class TestSetNested:
    def test_sets_nested_value(self):
        """Targets set_nested nested key creation (supports write_config_yaml__mutmut_1/3/5 coverage)."""
        data: dict = {}
        _config_file.set_nested(data, ("plugins", "llm", "provider"), "none")
        assert data == {"plugins": {"llm": {"provider": "none"}}}

    def test_overwrites_existing_nested_value(self):
        """Targets set_nested overwrite (supports write_config_yaml__mutmut_8-16 coverage)."""
        data: dict = {"plugins": {"llm": {"provider": "openai"}}}
        _config_file.set_nested(data, ("plugins", "llm", "provider"), "none")
        assert data["plugins"]["llm"]["provider"] == "none"


class TestGetNested:
    def test_returns_none_when_missing(self):
        """Targets get_nested missing key behavior (supports set_provider_none__mutmut_9-12)."""
        assert _config_file.get_nested({}, ("plugins", "llm")) is None

    def test_returns_value_when_present(self):
        """Targets get_nested present key behavior (supports set_provider_none__mutmut_9-12)."""
        data = {"plugins": {"llm": {"provider": "none"}}}
        assert _config_file.get_nested(data, ("plugins", "llm", "provider")) == "none"


class TestSetProviderNone:
    def test_clears_previous_llm_keys(self, tmp_path: Path, monkeypatch, capsys):
        """Kills set_provider_none__mutmut_9/10/11/12 (cleared key name mutations)."""
        path = tmp_path / "config.yml"
        path.write_text(
            "plugins:\n  extraction_stage:\n    llm:\n      provider: openai\n"
            "      api_url: https://x\n      model: gpt\n      api_key: secret\n"
        )
        monkeypatch.setattr(_config_file, "get_user_config_path", lambda: path)
        _config_file.set_provider_none()
        content = path.read_text(encoding="utf-8")
        assert "api_url" not in content
        assert "model" not in content
        assert "api_key" not in content
        assert "provider: none" in content

    def test_prints_updated_path_and_provider_messages(self, tmp_path: Path, monkeypatch, capsys):
        """Kills set_provider_none__mutmut_33/35/38/39/40/41 (print messages)."""
        path = tmp_path / "config.yml"
        path.write_text("plugins:\n  llm:\n    provider: openai\n")
        monkeypatch.setattr(_config_file, "get_user_config_path", lambda: path)
        _config_file.set_provider_none()
        out = capsys.readouterr().out
        assert f"Updated {path}" in out
        assert (
            "LLM provider set to 'none' \u2014 using deterministic structural extraction"
            in out
        )
        assert "  (no API key required, fully offline)" in out
