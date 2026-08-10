"""CLI command for cleaning old run artifacts."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
import typer

from specmetrics.infrastructure.runs.cleaner import RetentionPolicy, clean_runs

logger = structlog.get_logger(__name__)


def clean_command(
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
    dry_run_flag: Annotated[
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
    runs_dir = project_path / ".specmetrics" / "runs"
    policy = RetentionPolicy(keep_runs=keep_runs, keep_days=keep_days)
    now = datetime.now(UTC)

    if not runs_dir.is_dir():
        msg = f"{runs_dir} not found. Nothing to clean."
        if not quiet:
            typer.echo(msg)
        raise typer.Exit(code=0)

    _deleted, failed, msg = clean_runs(
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
