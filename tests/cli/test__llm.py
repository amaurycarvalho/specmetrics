from __future__ import annotations

import sys
import types

import pytest
import typer

from specmetrics.cli import _llm


class TestFormatModelList:
    def test_none_row_uses_deterministic_labels(self):
        """Kills format_model_list__mutmut_3/5/6/7/8 (none row string literals)."""
        lines = _llm.format_model_list().split("\n")
        assert "none" in lines[0]
        assert "(deterministic)" in lines[0]
        assert "(no network)" in lines[0]

    def test_custom_row_uses_user_defined_labels(self):
        """Kills format_model_list__mutmut_15/17/18/19/20 (custom row literals)."""
        lines = _llm.format_model_list().split("\n")
        last = lines[-1]
        assert "custom" in last
        assert "(user-defined)" in last

    def test_lines_joined_with_newline(self):
        """Kills format_model_list__mutmut_22 (join separator -> XX\\nXX)."""
        joined = _llm.format_model_list()
        assert "\n" in joined
        assert joined.count("\n") == len(_llm.PROVIDER_PRESETS) + 1

    def test_provider_rows_include_model_and_url(self):
        """Targets format_model_list__mutmut_22 provider row content."""
        lines = _llm.format_model_list().split("\n")
        assert any("deepseek-chat" in line for line in lines)
        assert any("api.deepseek.com" in line for line in lines)


class TestResolveLlmProvider:
    def test_custom_with_model_returns_url_and_model(self):
        """Targets resolve_llm_provider__mutmut_9/10 custom success path."""
        assert _llm.resolve_llm_provider("custom", "http://x", "m1") == (
            "http://x",
            "m1",
        )

    def test_custom_without_model_prints_error(self, capsys):
        """Kills resolve_llm_provider__mutmut_9/10 (custom --model message)."""
        with pytest.raises(typer.Exit) as exc:
            _llm.resolve_llm_provider("custom", "http://x", None)
        assert exc.value.exit_code == 1
        err = capsys.readouterr().err
        assert "Provider 'custom' requires --model." in err

    def test_unknown_provider_prints_error(self, capsys):
        """Targets resolve_llm_provider__mutmut_9/10 unknown-provider message."""
        with pytest.raises(typer.Exit) as exc:
            _llm.resolve_llm_provider("nope", None, None)
        assert exc.value.exit_code == 1
        err = capsys.readouterr().err
        assert "Unknown provider 'nope'" in err
        assert "Available providers" in err

    def test_preset_uses_defaults_when_not_overridden(self):
        """Targets resolve_llm_provider__mutmut_9/10 preset defaults."""
        assert _llm.resolve_llm_provider("chatgpt", None, None) == (
            "https://api.openai.com/v1",
            "gpt-4o-mini",
        )

    def test_preset_overrides_win(self):
        """Targets resolve_llm_provider__mutmut_9/10 preset override path."""
        assert _llm.resolve_llm_provider("chatgpt", "http://alt", "custom-model") == (
            "http://alt",
            "custom-model",
        )


class TestPrintLlmTestConfig:
    def test_full_config_prints_masked_api_key(self, capsys):
        """Kills print_llm_test_config__mutmut_5 (API key ********)."""
        _llm.print_llm_test_config("chatgpt", "http://x", "m", "sk-secret")
        out = capsys.readouterr().out
        assert "Provider: chatgpt" in out
        assert "API URL:  http://x" in out
        assert "Model:    m" in out
        assert "API key:  ********" in out
        assert "sk-secret" not in out

    def test_missing_api_key_prints_not_configured(self, capsys):
        """Kills print_llm_test_config__mutmut_9/10 (not-configured message)."""
        with pytest.raises(typer.Exit) as exc:
            _llm.print_llm_test_config("chatgpt", "http://x", "m", None)
        assert exc.value.exit_code == 1
        out = capsys.readouterr().out
        assert "API key:  \u274c not configured" in out

    def test_missing_api_key_prints_run_hint(self, capsys):
        """Kills print_llm_test_config__mutmut_12/13/14/15 (run hint message)."""
        with pytest.raises(typer.Exit):
            _llm.print_llm_test_config("chatgpt", "http://x", "m", None)
        out = capsys.readouterr().out
        assert "Run:  specmetrics config llm set <provider> --api-key <key>" in out

    def test_missing_model_prints_no_model_configured(self, capsys):
        """Kills print_llm_test_config__mutmut_20 (no model configured)."""
        with pytest.raises(typer.Exit) as exc:
            _llm.print_llm_test_config("chatgpt", "http://x", None, "sk-key")
        assert exc.value.exit_code == 1
        out = capsys.readouterr().out
        assert "\u274c no model configured" in out


def _install_fake_litellm(monkeypatch, completion=None, suppress_default=False) -> types.ModuleType:
    fake = types.ModuleType("litellm")
    fake.suppress_debug_info = suppress_default
    fake.completion = completion or (lambda **kwargs: None)
    monkeypatch.setitem(sys.modules, "litellm", fake)
    return fake


class TestTestLlmConnection:
    def test_sets_suppress_debug_info_true(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_1/2 (suppress_debug_info -> None/False)."""
        fake = _install_fake_litellm(
            monkeypatch,
            completion=lambda **kwargs: types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="  LLM test successful  "))]
            ),
        )
        _llm.test_llm_connection("m", "http://api", "key")
        assert fake.suppress_debug_info is True

    def test_success_builds_kwargs_and_messages(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_4-33 (kwargs/messages/max_tokens mutations)."""
        captured: dict = {}

        def completion(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="LLM test successful"))]
            )

        _install_fake_litellm(monkeypatch, completion=completion)
        _llm.test_llm_connection("gpt-model", "http://api/v1", "sk-abc")
        assert captured["model"] == "gpt-model"
        assert captured["api_base"] == "http://api/v1"
        assert captured["custom_llm_provider"] == "openai"
        assert captured["api_key"] == "sk-abc"
        assert captured["max_tokens"] == 10
        assert captured["messages"] == [
            {"role": "user", "content": "Say exactly: LLM test successful"}
        ]

    def test_no_api_url_omits_base_and_provider(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_6-13 (api_base/custom_llm_provider mutations)."""
        captured: dict = {}

        def completion(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))]
            )

        _install_fake_litellm(monkeypatch, completion=completion)
        _llm.test_llm_connection("m", None, None)
        assert "api_base" not in captured
        assert "custom_llm_provider" not in captured
        assert "api_key" not in captured

    def test_no_api_key_omits_key(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_14/15/16 (api_key kwargs mutations)."""
        captured: dict = {}

        def completion(**kwargs):
            captured.update(kwargs)
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="ok"))]
            )

        _install_fake_litellm(monkeypatch, completion=completion)
        _llm.test_llm_connection("m", "http://api", None)
        assert "api_key" not in captured
        assert captured["api_base"] == "http://api"

    def test_success_prints_response_and_status(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_35/37/38 (success print messages)."""
        _install_fake_litellm(
            monkeypatch,
            completion=lambda **kwargs: types.SimpleNamespace(
                choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="LLM test successful"))]
            ),
        )
        _llm.test_llm_connection("m", None, None)
        out = capsys.readouterr().out
        assert "Response: LLM test successful" in out
        assert "Status:   \u2705 connection successful" in out

    def test_failure_prints_error_and_status(self, monkeypatch, capsys):
        """Kills test_llm_connection__mutmut_41/42/44 (failure print messages)."""
        _install_fake_litellm(
            monkeypatch,
            completion=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        with pytest.raises(typer.Exit) as exc:
            _llm.test_llm_connection("m", None, None)
        assert exc.value.exit_code == 1
        out = capsys.readouterr().out
        assert "Status:   \u274c connection failed" in out
        assert "Error:    boom" in out
