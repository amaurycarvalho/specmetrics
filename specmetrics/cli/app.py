from __future__ import annotations

from pathlib import Path

import typer

from specmetrics import __version__

from .measure import run_measure
from .plugins import plugins_app

app = typer.Typer(
    name="specmetrics",
    help="A Functional Measurement Engine for Specification Driven Development",
    no_args_is_help=True,
)

app.add_typer(plugins_app)


@app.command()
def measure(
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output format and optional path: json, csv, xml, text, or json:./path.json",
    ),
    stage: str = typer.Option(
        None,
        "--stage",
        "-s",
        help="Run only this stage: discover, extract, graph, cfm, rule, measure, export",
    ),
    from_stage: str = typer.Option(
        None,
        "--from",
        help="Start from this stage (skip earlier stages)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed per-stage progress",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output",
    ),
) -> None:
    exit_code = run_measure(
        project_path=project_path,
        output=output,
        stage=stage,
        from_stage=from_stage,
        verbose=verbose,
        quiet=quiet,
    )
    raise typer.Exit(code=exit_code)


@app.command()
def version() -> None:
    from specmetrics.application.orchestrator import PipelineOrchestrator

    orch = PipelineOrchestrator()
    orch.discover_plugins()
    vi = orch.get_version_info()

    print(f"SpecMetrics v{vi.platform_version}")
    print(f"Python {vi.python_version}")
    if vi.plugins:
        print("Plugins:")
        for p in vi.plugins:
            status = "\u2713" if p.enabled else "\u2717"
            print(f"  {p.name} v{p.version} ({p.type}) {status}")


if __name__ == "__main__":
    app()
