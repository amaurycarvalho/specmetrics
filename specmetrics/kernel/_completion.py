"""LiteLLM integration helpers for completions."""

from __future__ import annotations

import importlib.util
from threading import Lock
from types import ModuleType
from typing import Any

from ._config import LLMGatewayConfig

HAS_LITELLM = importlib.util.find_spec("litellm") is not None

_litellm_import_lock = Lock()
_litellm_module: ModuleType | None = None


def _load_litellm() -> ModuleType:
    """Import the litellm module on first use and cache it.

    Importing litellm is expensive (it pulls in many transitive models), so we
    defer it until the gateway actually issues an LLM call instead of paying the
    cost whenever any kernel module is imported.
    """
    global _litellm_module
    if _litellm_module is None:
        with _litellm_import_lock:
            if _litellm_module is None:
                _litellm_module = importlib.import_module("litellm")
    return _litellm_module


def get_litellm_exceptions() -> tuple[type[Exception], ...]:
    """Build the tuple of transient LiteLLM exceptions.

    Materialized lazily so that merely importing the kernel does not import the
    heavyweight litellm package.
    """
    if not HAS_LITELLM:
        return (Exception,)
    litellm = _load_litellm()
    return (
        getattr(litellm, "AuthenticationError", Exception),
        getattr(litellm, "RateLimitError", Exception),
        getattr(litellm, "Timeout", Exception),
        getattr(litellm, "APIError", Exception),
        getattr(litellm, "ServiceUnavailableError", Exception),
        Exception,
    )


def detect_provider(model: str) -> str:
    """Infer the provider name from a model string."""
    if model.startswith(("gpt-", "text-", "ft:gpt")):
        return "openai"
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith("gemini-"):
        return "google"
    if model.startswith("ollama/"):
        return "ollama"
    if model.startswith("azure/"):
        return "azure"
    return "openai"


def supports_json_mode(provider: str) -> bool:
    """Return whether the provider supports native JSON mode."""
    return provider in ("openai", "azure")


def build_json_instruction(provider: str) -> str:
    """Return a JSON-only instruction prompt when JSON mode is unsupported."""
    if supports_json_mode(provider):
        return ""
    return "\n\nRespond with valid JSON only. No markdown fences."


def build_completion_kwargs(config: LLMGatewayConfig) -> dict[str, Any]:
    """Build kwargs for a litellm completion call from the gateway config."""
    kwargs: dict[str, Any] = {
        "model": config.model,
    }
    if config.api_url:
        kwargs["api_base"] = config.api_url
        kwargs["custom_llm_provider"] = "openai"
    if config.api_key:
        kwargs["api_key"] = config.api_key
    if config.max_tokens:
        kwargs["max_tokens"] = config.max_tokens
    return kwargs