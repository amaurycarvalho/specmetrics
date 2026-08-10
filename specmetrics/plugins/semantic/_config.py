"""Internal configuration resolution helpers for the LLM provider."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from specmetrics.kernel.llm_gateway import LLMGateway, LLMGatewayConfig

CONFIG_SEARCH = [
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "specmetrics",
    Path("/etc/specmetrics"),
]


def load_llm_config() -> dict[str, Any]:
    """Load the LLM configuration from the first available config file."""
    for base in CONFIG_SEARCH:
        for fname in ("config.yml", "config.yaml", "config.json"):
            path = base / fname
            if path.exists():
                try:
                    import ruamel.yaml

                    yaml = ruamel.yaml.YAML(typ="safe")
                    data = yaml.load(path.read_text(encoding="utf-8"))
                    return (
                        (data or {})
                        .get("plugins", {})
                        .get("extraction_stage", {})
                        .get("llm", {})
                    )
                except Exception:
                    return {}
    return {}


def resolve_api_url(api_url: str | None, cfg: dict[str, Any]) -> str | None:
    """Resolve the LLM API URL from arguments, config, or environment."""
    return api_url or cfg.get("api_url") or os.environ.get(
        "SPECMETRICS_LLM_API_URL"
    )


def resolve_model(model: str | None, cfg: dict[str, Any]) -> str:
    """Resolve the LLM model from arguments, config, or a default."""
    return (
        model
        or cfg.get("model")
        or os.environ.get("SPECMETRICS_LLM_MODEL")
        or "gpt-4o-mini"
    )


def resolve_api_key(api_key: str | None, cfg: dict[str, Any]) -> str | None:
    """Resolve the LLM API key from arguments, config, or environment."""
    return (
        api_key
        or cfg.get("api_key")
        or os.environ.get("SPECMETRICS_LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


def build_gateway(
    provider: str | None,
    model: str,
    api_key: str | None,
    api_url: str | None,
) -> LLMGateway:
    """Build and return a configured LLM gateway."""
    gw_config = LLMGatewayConfig(
        provider=provider or "openai",
        model=model,
        api_key=api_key,
        api_url=api_url,
    )
    return LLMGateway(gw_config)


def build_completion_kwargs(
    model: str,
    api_url: str | None,
    api_key: str | None,
) -> dict[str, Any]:
    """Build the keyword arguments for a completion request."""
    kwargs: dict[str, Any] = {
        "model": model,
    }
    if api_url:
        kwargs["api_base"] = api_url
        kwargs["custom_llm_provider"] = "openai"
    if api_key:
        kwargs["api_key"] = api_key
    return kwargs