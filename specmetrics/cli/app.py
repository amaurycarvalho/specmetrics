from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

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
    project_path: Path = typer.Option(
        ".",
        "--project-path",
        help="Path to the SpecMetrics project",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    keep_runs: int = typer.Option(
        90,
        "--keep-runs",
        help="Maximum number of most recent runs to retain (0 disables)",
    ),
    keep_days: int = typer.Option(
        30,
        "--keep-days",
        help="Maximum age in days for a run to be retained (0 disables)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview which runs would be deleted without actually deleting them",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress output",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output",
    ),
) -> None:
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
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    metrics: Optional[str] = typer.Option(
        None,
        "--metrics",
        "-m",
        help="Metrics to measure: all, bcp, fpa, sfp, snap, sp, tshirt, tp, cp (comma-separated)",
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
    export_run: bool = typer.Option(
        False,
        "--export",
        help="Automatically run export after measurement completes",
    ),
    export_format: Optional[str] = typer.Option(
        None,
        "--format",
        help="Export format(s) when --export is used (comma-separated: json,csv,xml)",
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
    log_file: Optional[str] = typer.Option(
        None,
        "--log-file",
        "-l",
        help="Persist logs to .specmetrics/logs/<filename>",
    ),
    llm_rpm_limit: int = typer.Option(
        15,
        "--llm-rpm-limit",
        help="LLM requests per minute limit (0 = unlimited)",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (supports $ENV_VAR expansion)",
        exists=False,
        file_okay=True,
        dir_okay=False,
        resolve_path=False,
    ),
) -> None:
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
