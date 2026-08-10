"""Tests for specmetrics.kernel._completion."""

from __future__ import annotations

import importlib
import types

from specmetrics.kernel import _completion as completion
from specmetrics.kernel._config import LLMGatewayConfig


class _FakeAuth(Exception):
    pass


class _FakeRateLimit(Exception):
    pass


class _FakeTimeout(Exception):
    pass


class _FakeAPIError(Exception):
    pass


class _FakeServiceUnavailable(Exception):
    pass


def _stub_with_exceptions() -> types.SimpleNamespace:
    return types.SimpleNamespace(
        AuthenticationError=_FakeAuth,
        RateLimitError=_FakeRateLimit,
        Timeout=_FakeTimeout,
        APIError=_FakeAPIError,
        ServiceUnavailableError=_FakeServiceUnavailable,
    )


def _stub_without_exceptions() -> types.SimpleNamespace:
    return types.SimpleNamespace()


def test_load_litellm_imports_and_caches(monkeypatch):
    """Kills _load_litellm__mutmut_1/2 (is None -> is not None),
    __mutmut_3 (module set to None), __mutmut_4 (import_module(None)) and
    __mutmut_5/6 (module name string)."""
    sentinel = types.SimpleNamespace(name="fake litellm")
    calls = []

    def fake_import(name):
        calls.append(name)
        return sentinel

    monkeypatch.setattr(completion, "_litellm_module", None)
    monkeypatch.setattr(importlib, "import_module", fake_import)
    result = completion._load_litellm()
    assert result is sentinel
    assert calls == ["litellm"]


def test_get_litellm_exceptions_when_litellm_unavailable(monkeypatch):
    """Kills get_litellm_exceptions__mutmut_1 (if not HAS_LITELLM -> if HAS_LITELLM)."""
    monkeypatch.setattr(completion, "HAS_LITELLM", False)
    assert completion.get_litellm_exceptions() == (Exception,)


def test_get_litellm_exceptions_resolves_attributes(monkeypatch):
    """Kills get_litellm_exceptions__mutmut_2 (litellm=None),
    __mutmut_3/12/21/30/39 (getattr(None, ...)) and the STRING_LITERAL variants
    __mutmut_9/10/11, __mutmut_18/19/20, __mutmut_27/29, __mutmut_36/37/38,
    __mutmut_45/46/47."""
    monkeypatch.setattr(completion, "HAS_LITELLM", True)
    monkeypatch.setattr(
        completion, "_load_litellm", lambda: _stub_with_exceptions()
    )
    result = completion.get_litellm_exceptions()
    assert result == (
        _FakeAuth,
        _FakeRateLimit,
        _FakeTimeout,
        _FakeAPIError,
        _FakeServiceUnavailable,
        Exception,
    )


def test_get_litellm_exceptions_defaults_to_exception(monkeypatch):
    """Kills get_litellm_exceptions__mutmut_5/14/23/32/41 (default -> None) and
    __mutmut_8/17/26/35/44 (getattr without default)."""
    monkeypatch.setattr(completion, "HAS_LITELLM", True)
    monkeypatch.setattr(
        completion, "_load_litellm", lambda: _stub_without_exceptions()
    )
    assert completion.get_litellm_exceptions() == (Exception,) * 6


def test_detect_provider_openai_prefixes():
    """Kills detect_provider__mutmut_2/3/4/5/6/7 (gpt prefixes) and
    __mutmut_30/31 (return 'openai')."""
    assert completion.detect_provider("gpt-4o") == "openai"
    assert completion.detect_provider("text-davinci-003") == "openai"
    assert completion.detect_provider("ft:gpt-3.5-turbo") == "openai"
    assert completion.detect_provider("unknown-vendor") == "openai"


def test_detect_provider_anthropic():
    """Kills detect_provider__mutmut_13/14 (return 'anthropic')."""
    assert completion.detect_provider("claude-3-opus") == "anthropic"


def test_detect_provider_google():
    """Kills detect_provider__mutmut_15/16/17 (gemini prefix) and
    __mutmut_18/19 (return 'google')."""
    assert completion.detect_provider("gemini-1.5-pro") == "google"


def test_detect_provider_ollama():
    """Kills detect_provider__mutmut_20/21/22 (ollama prefix) and
    __mutmut_23/24 (return 'ollama')."""
    assert completion.detect_provider("ollama/llama3") == "ollama"


def test_detect_provider_azure():
    """Kills detect_provider__mutmut_25/26/27 (azure prefix) and
    __mutmut_28/29 (return 'azure')."""
    assert completion.detect_provider("azure/gpt-4") == "azure"


def test_supports_json_mode():
    """Kills supports_json_mode__mutmut_4/5 (azure literal)."""
    assert completion.supports_json_mode("openai") is True
    assert completion.supports_json_mode("azure") is True
    assert completion.supports_json_mode("anthropic") is False


def test_build_json_instruction_empty_for_json_mode():
    """Kills build_json_instruction__mutmut_1 (supports_json_mode(None)) and
    __mutmut_2 (return '' -> 'XXXX')."""
    assert completion.build_json_instruction("openai") == ""
    assert completion.build_json_instruction("azure") == ""


def test_build_json_instruction_prompt():
    """Kills build_json_instruction__mutmut_3 (instruction literal)."""
    assert (
        completion.build_json_instruction("anthropic")
        == "\n\nRespond with valid JSON only. No markdown fences."
    )


def test_build_completion_kwargs_full():
    """Kills build_completion_kwargs__mutmut_4/5/6 (api_base),
    __mutmut_7/8/9/10/11 (custom_llm_provider), __mutmut_12/13/14 (api_key)
    and __mutmut_15/16/17 (max_tokens)."""
    config = LLMGatewayConfig(
        model="custom-model",
        api_url="http://llm.local/v1",
        api_key="secret-key",
        max_tokens=321,
    )
    kwargs = completion.build_completion_kwargs(config)
    assert kwargs["model"] == "custom-model"
    assert kwargs["api_base"] == "http://llm.local/v1"
    assert kwargs["custom_llm_provider"] == "openai"
    assert kwargs["api_key"] == "secret-key"
    assert kwargs["max_tokens"] == 321


def test_build_completion_kwargs_minimal():
    """Verifies optional kwargs omitted when unset."""
    kwargs = completion.build_completion_kwargs(LLMGatewayConfig(model="m"))
    assert kwargs == {"model": "m", "max_tokens": 4096}
    assert "api_base" not in kwargs
    assert "custom_llm_provider" not in kwargs
    assert "api_key" not in kwargs


def test_build_completion_kwargs_zero_max_tokens():
    """Verifies falsy max_tokens omits the key."""
    kwargs = completion.build_completion_kwargs(LLMGatewayConfig(model="m", max_tokens=0))
    assert "max_tokens" not in kwargs
