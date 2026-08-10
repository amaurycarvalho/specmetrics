"""Typer CLI application for the SpecMetrics measurement engine."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Annotated

import structlog
import typer

from .commands.clean import clean_command
from .commands.explain import explain_cli
from .commands.mcp import mcp_cli
from .commands.validate import validate_cli
from .config_commands import config_app
from .export_commands import export_app
from .measure import run_measure
from .plugins import plugins_app

logging.basicConfig(
    format="%(message)s",
    stream=sys.stderr,
    level=logging.WARNING,
)
structlog.configure(
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)

app = typer.Typer(
    name="specmetrics",
    help="A Functional Measurement Engine for Specification Driven Development",
    no_args_is_help=True,
)

app.add_typer(plugins_app)
app.add_typer(export_app)
app.add_typer(config_app)
app.add_typer(explain_cli)
app.add_typer(mcp_cli)
app.add_typer(validate_cli)


@app.command()
def clean(
    project_path: Annotated[
        Path,
        typer.Option(
            "--project-path",
            help="Path to the SpecMetrics project",
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ".",
    keep_runs: Annotated[
        int,
        typer.Option(
            "--keep-runs",
            help="Maximum number of most recent runs to retain (0 disables)",
        ),
    ] = 90,
    keep_days: Annotated[
        int,
        typer.Option(
            "--keep-days",
            help="Maximum age in days for a run to be retained (0 disables)",
        ),
    ] = 30,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Preview which runs would be deleted without actually deleting them",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed progress output",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress non-error output",
        ),
    ] = False,
) -> None:
    """Clean old run artifacts according to the retention policy."""
    clean_command(
        project_path=project_path,
        keep_runs=keep_runs,
        keep_days=keep_days,
        dry_run_flag=dry_run,
        verbose=verbose,
        quiet=quiet,
    )


@app.command()
def measure(
    project_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpecMetrics project",
            exists=False,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ".",
    metrics: Annotated[
        str | None,
        typer.Option(
            "--metrics",
            "-m",
            help="Metrics to measure: all, bcp, fpa, sfp, snap, sp, tshirt, tp, cp (comma-separated)",
        ),
    ] = None,
    output: Annotated[
        str | None,
        typer.Option(
            "--output",
            "-o",
            help="Output format and optional path: json, csv, xml, text, or json:./path.json",
        ),
    ] = None,
    stage: Annotated[
        str | None,
        typer.Option(
            "--stage",
            "-s",
            help="Run only this stage: discover, extract, graph, cfm, rule, measure, export",
        ),
    ] = None,
    from_stage: Annotated[
        str | None,
        typer.Option(
            "--from",
            help="Start from this stage (skip earlier stages)",
        ),
    ] = None,
    export_run: Annotated[
        bool,
        typer.Option(
            "--export",
            help="Automatically run export after measurement completes",
        ),
    ] = False,
    export_format: Annotated[
        str | None,
        typer.Option(
            "--format",
            help="Export format(s) when --export is used (comma-separated: json,csv,xml)",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed per-stage progress",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress non-error output",
        ),
    ] = False,
    log_file: Annotated[
        str | None,
        typer.Option(
            "--log-file",
            "-l",
            help="Persist logs to .specmetrics/logs/<filename>",
        ),
    ] = None,
    llm_rpm_limit: Annotated[
        int,
        typer.Option(
            "--llm-rpm-limit",
            help="LLM requests per minute limit (0 = unlimited)",
        ),
    ] = 15,
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to configuration file (supports $ENV_VAR expansion)",
            exists=False,
            file_okay=True,
            dir_okay=False,
            resolve_path=False,
        ),
    ] = None,
) -> None:
    """Measure functional metrics for a Specification-Driven Development project."""
    exit_code = run_measure(
        project_path=project_path,
        metrics=metrics,
        output=output,
        stage=stage,
        from_stage=from_stage,
        export_run=export_run,
        export_format=export_format,
        verbose=verbose,
        quiet=quiet,
        log_file=log_file,
        config_path=config,
        llm_rpm_limit=llm_rpm_limit,
    )
    raise typer.Exit(code=exit_code)


@app.command()
def version() -> None:
    """Print the SpecMetrics version and discovered plugin information."""
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
