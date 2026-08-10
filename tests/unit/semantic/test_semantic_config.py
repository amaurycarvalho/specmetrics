from __future__ import annotations

from specmetrics.plugins.semantic._config import (
    build_completion_kwargs,
    build_gateway,
    load_llm_config,
    resolve_api_key,
    resolve_api_url,
    resolve_model,
)


class TestLoadLlmConfig:
    def test_no_config_files_returns_empty(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "specmetrics.plugins.semantic._config.CONFIG_SEARCH",
            [tmp_path],
        )
        assert load_llm_config() == {}

    def test_reads_yaml_config(self, monkeypatch, tmp_path):
        (tmp_path / "config.yml").write_text(
            "plugins:\n  extraction_stage:\n    llm:\n"
            "      model: my-model\n      api_key: secret\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "specmetrics.plugins.semantic._config.CONFIG_SEARCH",
            [tmp_path],
        )
        cfg = load_llm_config()
        assert cfg["model"] == "my-model"
        assert cfg["api_key"] == "secret"

    def test_invalid_yaml_returns_empty(self, monkeypatch, tmp_path):
        (tmp_path / "config.yml").write_text(
            "plugins:\n  extraction_stage: [unclosed\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "specmetrics.plugins.semantic._config.CONFIG_SEARCH",
            [tmp_path],
        )
        assert load_llm_config() == {}

    def test_empty_first_dir_falls_through_to_second(self, monkeypatch, tmp_path):
        second = tmp_path / "second"
        second.mkdir()
        (second / "config.json").write_text(
            '{"plugins": {"extraction_stage": {"llm": {"model": "json-model"}}}}',
            encoding="utf-8",
        )
        monkeypatch.setattr(
            "specmetrics.plugins.semantic._config.CONFIG_SEARCH",
            [tmp_path / "first", second],
        )
        cfg = load_llm_config()
        assert cfg["model"] == "json-model"


class TestResolveApiUrl:
    def test_argument_wins(self):
        assert resolve_api_url("http://arg", {"api_url": "http://cfg"}) == "http://arg"

    def test_config_fallback(self):
        assert resolve_api_url(None, {"api_url": "http://cfg"}) == "http://cfg"

    def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("SPECMETRICS_LLM_API_URL", "http://env")
        assert resolve_api_url(None, {}) == "http://env"

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("SPECMETRICS_LLM_API_URL", raising=False)
        assert resolve_api_url(None, {}) is None


class TestResolveModel:
    def test_argument_wins(self):
        assert resolve_model("arg-model", {"model": "cfg"}) == "arg-model"

    def test_config_fallback(self):
        assert resolve_model(None, {"model": "cfg-model"}) == "cfg-model"

    def test_env_fallback(self, monkeypatch):
        monkeypatch.setenv("SPECMETRICS_LLM_MODEL", "env-model")
        assert resolve_model(None, {}) == "env-model"

    def test_default_when_unset(self, monkeypatch):
        monkeypatch.delenv("SPECMETRICS_LLM_MODEL", raising=False)
        assert resolve_model(None, {}) == "gpt-4o-mini"


class TestResolveApiKey:
    def test_argument_wins(self):
        assert resolve_api_key("arg-key", {"api_key": "cfg"}) == "arg-key"

    def test_config_fallback(self):
        assert resolve_api_key(None, {"api_key": "cfg-key"}) == "cfg-key"

    def test_env_fallback(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("SPECMETRICS_LLM_API_KEY", "spec-key")
        assert resolve_api_key(None, {}) == "spec-key"

    def test_openai_env_fallback(self, monkeypatch):
        monkeypatch.delenv("SPECMETRICS_LLM_API_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "oa-key")
        assert resolve_api_key(None, {}) == "oa-key"

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv("SPECMETRICS_LLM_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert resolve_api_key(None, {}) is None


class TestBuildGateway:
    def test_builds_gateway_with_defaults(self):
        gw = build_gateway(None, "my-model", "my-key", "http://url")
        assert gw.config.model == "my-model"
        assert gw.config.api_key == "my-key"
        assert gw.config.api_url == "http://url"
        assert gw.config.provider == "openai"

    def test_builds_gateway_with_explicit_provider(self):
        gw = build_gateway("claude", "m", None, None)
        assert gw.config.provider == "claude"


class TestBuildCompletionKwargs:
    def test_model_only(self):
        kwargs = build_completion_kwargs("m", None, None)
        assert kwargs == {"model": "m"}

    def test_with_api_url_and_key(self):
        kwargs = build_completion_kwargs("m", "http://url", "key")
        assert kwargs["model"] == "m"
        assert kwargs["api_base"] == "http://url"
        assert kwargs["custom_llm_provider"] == "openai"
        assert kwargs["api_key"] == "key"

    def test_with_api_url_only(self):
        kwargs = build_completion_kwargs("m", "http://url", None)
        assert "api_key" not in kwargs
        assert kwargs["api_base"] == "http://url"