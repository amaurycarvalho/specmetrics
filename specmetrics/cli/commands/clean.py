from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import structlog
import typer

from specmetrics.infrastructure.runs.cleaner import RetentionPolicy, clean_runs

logger = structlog.get_logger(__name__)


def clean_command(
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
    dry_run_flag: bool = typer.Option(
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
    runs_dir = project_path / ".specmetrics" / "runs"
    policy = RetentionPolicy(keep_runs=keep_runs, keep_days=keep_days)
    now = datetime.now(timezone.utc)

    if not runs_dir.is_dir():
        msg = f"{runs_dir} not found. Nothing to clean."
        if not quiet:
            typer.echo(msg)
        raise typer.Exit(code=0)

    deleted, failed, msg = clean_runs(
        runs_dir=runs_dir,
        policy=policy,
        dry_run_mode=dry_run_flag,
        now=now,
    )

    if not quiet:
        typer.echo(msg)

    if not dry_run_flag and failed > 0:
        raise typer.Exit(code=1)

    raise typer.Exit(code=0)
