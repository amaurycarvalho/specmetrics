from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import ruamel.yaml
import typer

from .measure import get_config_system

config_app = typer.Typer(
    name="config",
    help="Inspect and manage configuration",
    no_args_is_help=True,
)

llm_app = typer.Typer(
    name="llm",
    help="Configure LLM provider settings",
    no_args_is_help=True,
)
config_app.add_typer(llm_app)

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

LLM_NAMESPACE = ("plugins", "extraction_stage", "llm")


def _get_user_config_dir() -> Path:
    xdg_home = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
    return Path(xdg_home) / "specmetrics"


def _get_user_config_path() -> Path:
    for filename in ["config.yml", "config.yaml", "config.json"]:
        path = _get_user_config_dir() / filename
        if path.exists():
            return path
    return _get_user_config_dir() / "config.yml"


def _read_config_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _write_config_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)


def _set_nested(data: dict[str, Any], keys: tuple[str, ...], value: Any) -> None:
    for key in keys[:-1]:
        if key not in data or not isinstance(data[key], dict):
            data[key] = {}
        data = data[key]
    data[keys[-1]] = value


def _get_nested(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def _write_llm_config(**kwargs: str | None) -> None:
    path = _get_user_config_path()
    data = _read_config_yaml(path)
    for key, value in kwargs.items():
        if value is not None:
            _set_nested(data, LLM_NAMESPACE + (key,), value)
    _write_config_yaml(path, data)
    print(f"Updated {path}")


def _format_model_list() -> str:
    lines = []
    lines.append(f"  {'none':<12} {'(deterministic)':<30} {'(no network)'}")
    for name, preset in PROVIDER_PRESETS.items():
        lines.append(f"  {name:<12} {preset['model']:<30} {preset['api_url']}")
    lines.append(f"  {'custom':<12} {'(user-defined)':<30} {'(user-defined)'}")
    return "\n".join(lines)


@config_app.command(name="dump")
def config_dump(
    format: str = typer.Option(
        "text",
        "--format",
        "-f",
        help="Output format: text, json",
    ),
) -> None:
    cfg_system = get_config_system()
    provider = cfg_system.load()
    dump = provider.dump

    if format == "json":
        data = [
            {
                "key": e.key,
                "value": e.value,
                "source": e.source,
                "level": e.level,
                "is_default": e.is_default,
                "is_sensitive": e.is_sensitive,
            }
            for e in dump.entries
        ]
        json.dump(data, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        header = f"{'Key':<40} {'Value':<30} {'Source':<25} {'Level':<15} {'Default':<8}"
        print(header)
        print("-" * len(header))
        for entry in dump.entries:
            value_str = "**********" if entry.is_sensitive else str(entry.value)
            default_str = "yes" if entry.is_default else "no"
            print(
                f"{entry.key:<40} {value_str:<30} {entry.source:<25} {entry.level:<15} {default_str:<8}"
            )

    if dump.warnings:
        print("\nWarnings:")
        for w in dump.warnings:
            print(f"  - {w.message}")


@llm_app.command(name="set")
def llm_set(
    provider: str = typer.Argument(
        ...,
        help="Provider name (use 'list' subcommand to see available providers)",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="Model identifier (overrides provider default)",
    ),
    api_key: str = typer.Option(
        None,
        "--api-key",
        "-k",
        help="API key or authentication token",
    ),
    api_url: str = typer.Option(
        None,
        "--api-url",
        "-u",
        help="API base URL (overrides provider default)",
    ),
) -> None:
    if provider == "none":
        path = _get_user_config_path()
        data = _read_config_yaml(path)
        llm_data = _get_nested(data, LLM_NAMESPACE)
        if llm_data:
            for key in ("api_url", "model", "api_key"):
                llm_data.pop(key, None)
        _set_nested(data, LLM_NAMESPACE + ("provider",), "none")
        _write_config_yaml(path, data)
        print(f"Updated {path}")
        print("LLM provider set to 'none' — using deterministic structural extraction")
        print("  (no API key required, fully offline)")
        return

    preset = PROVIDER_PRESETS.get(provider)
    if preset is None and provider != "custom":
        print(f"Unknown provider '{provider}'. Available providers:\n{_format_model_list()}", file=sys.stderr)
        raise typer.Exit(code=1)

    if provider == "custom" and not model:
        print("Provider 'custom' requires --model.", file=sys.stderr)
        raise typer.Exit(code=1)

    final_api_url = api_url or (preset["api_url"] if preset else None)
    final_model = model or (preset["model"] if preset else None)

    _write_llm_config(provider=provider, api_url=final_api_url, model=final_model, api_key=api_key)

    print(f"LLM provider set to '{provider}'")
    if final_api_url:
        print(f"  API URL:   {final_api_url}")
    if final_model:
        print(f"  Model:     {final_model}")
    if api_key:
        print("  API key:   ********")


@llm_app.command(name="show")
def llm_show() -> None:
    path = _get_user_config_path()
    data = _read_config_yaml(path)
    llm_data = _get_nested(data, LLM_NAMESPACE) or {}

    print("Current LLM configuration:")
    print()

    if llm_data:
        for key in ("provider", "api_url", "model", "api_key"):
            value = llm_data.get(key)
            if value is not None:
                display = "**********" if key == "api_key" else str(value)
                print(f"  {'.'.join(LLM_NAMESPACE)}.{key:<10} {display}")
        print()
        print(f"  Config file: {path}")
    else:
        print("  (not configured — will use 'none' / deterministic engine by default)")
        print()
        print("Set a provider with:  specmetrics config llm set <provider> [--api-key KEY]")
        print("Available providers:\n" + _format_model_list())


@llm_app.command(name="list")
def llm_list() -> None:
    """List all available LLM providers."""
    print("Available providers:\n")
    print(f"  {'Provider':<12} {'Model':<30} {'API URL'}")
    print(f"  {'-'*12:<12} {'-'*30:<30} {'-'*40}")
    print(_format_model_list())


@llm_app.command(name="set-model")
def llm_set_model(
    model: str = typer.Argument(
        ...,
        help="Model identifier (e.g. gpt-4o-mini, claude-sonnet-4-20250514)",
    ),
) -> None:
    _write_llm_config(model=model)
    print(f"LLM model set to '{model}'")


@llm_app.command(name="set-api-key")
def llm_set_api_key(
    api_key: str = typer.Argument(
        ...,
        help="API key or authentication token",
    ),
) -> None:
    _write_llm_config(api_key=api_key)
    print("LLM API key updated")


@llm_app.command(name="test")
def llm_test() -> None:
    path = _get_user_config_path()
    data = _read_config_yaml(path)
    llm_data = _get_nested(data, LLM_NAMESPACE) or {}

    provider = llm_data.get("provider", "none")
    api_url = llm_data.get("api_url")
    model = llm_data.get("model")
    api_key = llm_data.get("api_key")

    if provider == "none" or not provider:
        print("Provider: none (deterministic engine)")
        print("Status:  \u2705 deterministic engine is always available")
        return

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
            messages=[
                {"role": "user", "content": "Say exactly: LLM test successful"}
            ],
            max_tokens=10,
        )
        content = response.choices[0].message.content.strip()
        print(f"Response: {content}")
        print("Status:   \u2705 connection successful")
    except Exception as exc:
        print("Status:   \u274c connection failed")
        print(f"Error:    {exc}")
        raise typer.Exit(code=1)
