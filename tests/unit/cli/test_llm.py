from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import typer

from specmetrics.cli import _llm


class TestFormatModelList:
    def test_includes_all_presets(self):
        text = _llm.format_model_list()
        assert "none" in text
        assert "custom" in text
        for name in _llm.PROVIDER_PRESETS:
            assert name in text


class TestResolveLLMProvider:
    def test_custom_with_model(self):
        api_url, model = _llm.resolve_llm_provider("custom", "http://x", "m1")
        assert api_url == "http://x"
        assert model == "m1"

    def test_custom_without_model_exits(self, capsys):
        with pytest.raises(typer.Exit) as exc_info:
            _llm.resolve_llm_provider("custom", "http://x", None)
        assert exc_info.value.exit_code == 1
        assert "requires --model" in capsys.readouterr().err

    def test_known_provider_defaults(self):
        api_url, model = _llm.resolve_llm_provider("chatgpt", None, None)
        assert api_url == "https://api.openai.com/v1"
        assert model == "gpt-4o-mini"

    def test_known_provider_overrides(self):
        api_url, model = _llm.resolve_llm_provider("chatgpt", "http://custom", "my-model")
        assert api_url == "http://custom"
        assert model == "my-model"

    def test_unknown_provider_exits(self, capsys):
        with pytest.raises(typer.Exit) as exc_info:
            _llm.resolve_llm_provider("nope", None, None)
        assert exc_info.value.exit_code == 1
        assert "Unknown provider 'nope'" in capsys.readouterr().err


class TestPrintLLMTestConfig:
    def test_full_config_prints(self, capsys):
        _llm.print_llm_test_config("chatgpt", "http://a", "gpt-4", "secret")
        captured = capsys.readouterr().out
        assert "Provider: chatgpt" in captured
        assert "API URL:  http://a" in captured
        assert "Model:    gpt-4" in captured
        assert "API key:  ********" in captured

    def test_missing_api_key_exits(self, capsys):
        with pytest.raises(typer.Exit) as exc_info:
            _llm.print_llm_test_config("chatgpt", "http://a", "gpt-4", None)
        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr().out
        assert "not configured" in captured

    def test_missing_model_with_key_exits(self, capsys):
        with pytest.raises(typer.Exit) as exc_info:
            _llm.print_llm_test_config("chatgpt", "http://a", None, "secret")
        assert exc_info.value.exit_code == 1
        assert "no model configured" in capsys.readouterr().out


class TestLLMConnection:
    def _fake_litellm(self, monkeypatch):
        fake = SimpleNamespace()
        module = MagicMock()
        module.suppress_debug_info = None
        fake.module = module
        monkeypatch.setitem(
            __import__("sys").modules, "litellm", module
        )
        return module

    def test_success(self, monkeypatch, capsys):
        module = self._fake_litellm(monkeypatch)
        module.completion.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="LLM test successful"))]
        )
        _llm.test_llm_connection("gpt-4", "http://x", "key")
        captured = capsys.readouterr().out
        assert "connection successful" in captured

    def test_failure_exits(self, monkeypatch, capsys):
        module = self._fake_litellm(monkeypatch)
        module.completion.side_effect = RuntimeError("boom")
        with pytest.raises(typer.Exit) as exc_info:
            _llm.test_llm_connection("gpt-4", None, None)
        assert exc_info.value.exit_code == 1
        captured = capsys.readouterr().out
        assert "connection failed" in captured