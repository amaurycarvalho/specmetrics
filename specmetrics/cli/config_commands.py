"""CLI commands for inspecting and managing configuration."""

from __future__ import annotations

import json
import sys
from typing import Annotated

import typer

from ._config_file import (
    LLM_NAMESPACE,
    get_nested,
    get_user_config_path,
    read_config_yaml,
    set_provider_none,
    write_llm_config,
)
from ._llm import (
    format_model_list,
    print_llm_test_config,
    resolve_llm_provider,
    test_llm_connection,
)
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


@config_app.command(name="dump")
def config_dump(
    format: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Output format: text, json",
        ),
    ] = "text",
) -> None:
    """Dump the resolved configuration with source provenance."""
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
        header = (
            f"{'Key':<40} {'Value':<30} {'Source':<25} {'Level':<15} {'Default':<8}"
        )
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
    provider: Annotated[
        str,
        typer.Argument(
            help="Provider name (use 'list' subcommand to see available providers)",
        ),
    ],
    model: Annotated[
        str | None,
        typer.Option(
            "--model",
            "-m",
            help="Model identifier (overrides provider default)",
        ),
    ] = None,
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            "-k",
            help="API key or authentication token",
        ),
    ] = None,
    api_url: Annotated[
        str | None,
        typer.Option(
            "--api-url",
            "-u",
            help="API base URL (overrides provider default)",
        ),
    ] = None,
) -> None:
    """Set the LLM provider configuration."""
    if provider == "none":
        set_provider_none()
        return

    final_api_url, final_model = resolve_llm_provider(provider, api_url, model)

    write_llm_config(
        provider=provider, api_url=final_api_url, model=final_model, api_key=api_key
    )

    print(f"LLM provider set to '{provider}'")
    if final_api_url:
        print(f"  API URL:   {final_api_url}")
    if final_model:
        print(f"  Model:     {final_model}")
    if api_key:
        print("  API key:   ********")


@llm_app.command(name="show")
def llm_show() -> None:
    """Show the current LLM configuration."""
    path = get_user_config_path()
    data = read_config_yaml(path)
    llm_data = get_nested(data, LLM_NAMESPACE) or {}

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
        print("  (not configured \u2014 will use 'none' / deterministic engine by default)")
        print()
        print(
            "Set a provider with:  specmetrics config llm set <provider> [--api-key KEY]"
        )
        print("Available providers:\n" + format_model_list())


@llm_app.command(name="list")
def llm_list() -> None:
    """List all available LLM providers."""
    print("Available providers:\n")
    print(f"  {'Provider':<12} {'Model':<30} {'API URL'}")
    print(f"  {'-' * 12:<12} {'-' * 30:<30} {'-' * 40}")
    print(format_model_list())


@llm_app.command(name="set-model")
def llm_set_model(
    model: Annotated[
        str,
        typer.Argument(
            help="Model identifier (e.g. gpt-4o-mini, claude-sonnet-4-20250514)",
        ),
    ],
) -> None:
    """Set the LLM model identifier."""
    write_llm_config(model=model)
    print(f"LLM model set to '{model}'")


@llm_app.command(name="set-api-key")
def llm_set_api_key(
    api_key: Annotated[
        str,
        typer.Argument(
            help="API key or authentication token",
        ),
    ],
) -> None:
    """Set the LLM API key."""
    write_llm_config(api_key=api_key)
    print("LLM API key updated")


@llm_app.command(name="test")
def llm_test() -> None:
    """Test the configured LLM provider connection."""
    path = get_user_config_path()
    data = read_config_yaml(path)
    llm_data = get_nested(data, LLM_NAMESPACE) or {}

    provider = llm_data.get("provider", "none")
    api_url = llm_data.get("api_url")
    model = llm_data.get("model")
    api_key = llm_data.get("api_key")

    if provider == "none" or not provider:
        print("Provider: none (deterministic engine)")
        print("Status:  \u2705 deterministic engine is always available")
        return

    print_llm_test_config(provider, api_url, model, api_key)
    test_llm_connection(model, api_url, api_key)