"""LLM provider helpers for the CLI config commands."""

from __future__ import annotations

import sys
from typing import Any

import typer

PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "chatgpt": {
        "api_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
    "gemini": {
        "api_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.1-flash-lite",
    },
    "copilot": {
        "api_url": "https://models.inference.ai.azure.com",
        "model": "gpt-4o",
    },
    "claude": {
        "api_url": "https://api.anthropic.com/v1",
        "model": "claude-sonnet-4-20250514",
    },
    "deepseek": {
        "api_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "ollama": {
        "api_url": "http://localhost:11434/v1",
        "model": "llama3.2",
    },
}


def format_model_list() -> str:
    """Render the list of known LLM provider presets."""
    lines = []
    lines.append(f"  {'none':<12} {'(deterministic)':<30} {'(no network)'}")
    for name, preset in PROVIDER_PRESETS.items():
        lines.append(f"  {name:<12} {preset['model']:<30} {preset['api_url']}")
    lines.append(f"  {'custom':<12} {'(user-defined)':<30} {'(user-defined)'}")
    return "\n".join(lines)


def resolve_llm_provider(
    provider: str, api_url: str | None, model: str | None
) -> tuple[str | None, str | None]:
    """Return the resolved (api_url, model) for a provider, or raise on error."""
    if provider == "custom":
        if not model:
            print("Provider 'custom' requires --model.", file=sys.stderr)
            raise typer.Exit(code=1)
        return api_url, model

    preset = PROVIDER_PRESETS.get(provider)
    if preset is None:
        print(
            f"Unknown provider '{provider}'. Available providers:\n{format_model_list()}",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    final_api_url = api_url or preset["api_url"]
    final_model = model or preset["model"]
    return final_api_url, final_model


def print_llm_test_config(
    provider: str, api_url: str | None, model: str | None, api_key: str | None
) -> None:
    """Print the provider config summary, failing on missing required settings."""
    print(f"Provider: {provider}")
    if api_url:
        print(f"API URL:  {api_url}")
    if model:
        print(f"Model:    {model}")
    if api_key:
        print("API key:  ********")
    else:
        print("API key:  \u274c not configured")
        print()
        print("Run:  specmetrics config llm set <provider> --api-key <key>")
        raise typer.Exit(code=1)
    if not model:
        print("\u274c no model configured")
        raise typer.Exit(code=1)


def test_llm_connection(
    model: str, api_url: str | None, api_key: str | None
) -> None:
    """Attempt a minimal LLM completion and report the result."""
    import litellm

    litellm.suppress_debug_info = True

    kwargs: dict[str, Any] = {"model": model}
    if api_url:
        kwargs["api_base"] = api_url
        kwargs["custom_llm_provider"] = "openai"
    if api_key:
        kwargs["api_key"] = api_key

    try:
        response = litellm.completion(
            **kwargs,
            messages=[{"role": "user", "content": "Say exactly: LLM test successful"}],
            max_tokens=10,
        )
        content = response.choices[0].message.content.strip()
        print(f"Response: {content}")
        print("Status:   \u2705 connection successful")
    except Exception as exc:
        print("Status:   \u274c connection failed")
        print(f"Error:    {exc}")
        raise typer.Exit(code=1)