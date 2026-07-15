from __future__ import annotations

import typer

from specmetrics.application.orchestrator import PipelineOrchestrator

plugins_app = typer.Typer(
    name="plugins",
    help="Manage and inspect plugins",
    no_args_is_help=True,
)


@plugins_app.command(name="list")
def list_plugins(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed plugin info",
    ),
    plugin_type: str = typer.Option(
        None,
        "--type",
        help="Filter by plugin type (adapter, measurement, export, publisher)",
    ),
) -> None:
    orch = PipelineOrchestrator()
    orch.discover_plugins()
    all_plugins = orch.list_plugins()

    if plugin_type:
        all_plugins = [p for p in all_plugins if p.type == plugin_type]

    if not all_plugins:
        print("No plugins found.")
        return

    print("Plugin List:")
    for p in all_plugins:
        status = "\u2713" if p.enabled else "\u2717"
        print(f"  {p.name} v{p.version} ({p.type}) {status}")
        if verbose:
            print(f"    compatible: {p.compatible}")


@plugins_app.command()
def verify() -> None:
    orch = PipelineOrchestrator()
    orch.discover_plugins()
    all_plugins = orch.list_plugins()

    if not all_plugins:
        print("No plugins found to verify.")
        return

    all_compatible = True
    for p in all_plugins:
        if not p.compatible:
            print(f"\u2717 {p.name} v{p.version} ({p.type}) \u2014 INCOMPATIBLE")
            all_compatible = False
        else:
            print(f"\u2713 {p.name} v{p.version} ({p.type})")

    if all_compatible:
        print("All plugins compatible.")
    else:
        print("Some plugins are incompatible.")
