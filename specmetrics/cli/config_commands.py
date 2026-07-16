from __future__ import annotations

import json
import sys

import typer

from .measure import get_config_system

config_app = typer.Typer(
    name="config",
    help="Inspect and manage configuration",
    no_args_is_help=True,
)


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
