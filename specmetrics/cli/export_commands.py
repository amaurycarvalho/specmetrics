"""CLI commands for exporting measurement results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import structlog
import typer

from specmetrics.application.orchestrator import (
    read_run_artifacts,
)

from ._impl import (
    discover_exporter_plugins,
    export_selected,
    run_pipeline_export,
)

logger = structlog.get_logger(__name__)

MEASURE_ID_PATTERN = "????????-??????-????????"


def list_measure_runs(project_path: Path) -> list[dict]:
    """List stored measure runs, newest first, with their creation times."""
    runs_dir = project_path / ".specmetrics" / "runs"
    if not runs_dir.exists():
        return []
    entries: list[dict] = []
    for child in sorted(runs_dir.iterdir(), reverse=True):
        if not child.is_dir():
            continue
        meta_file = child / "metadata.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                created = meta.get("created_at", "")
            except Exception:
                created = ""
        else:
            created = ""
        entries.append({"id": child.name, "created_at": created})
    return entries


export_app = typer.Typer(
    name="export",
    help="Export measurement results to various formats",
    no_args_is_help=True,
)


@export_app.command()
def run(
    measure_id: Annotated[
        str | None,
        typer.Argument(
            help="Measure ID to export (default: most recent run)",
        ),
    ] = None,
    project_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpecMetrics project",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ".",
    formats: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Comma-separated list of export formats (json, csv, xml)",
        ),
    ] = "json",
    output_dir: Annotated[
        Path | None,
        typer.Option(
            "--output-dir",
            "-o",
            help="Directory to write export files to",
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = None,
    publish: Annotated[
        bool,
        typer.Option(
            "--publish",
            help="Publish results to configured telemetry backends",
        ),
    ] = False,
    otel_endpoint: Annotated[
        str | None,
        typer.Option(
            "--otel-endpoint",
            help="OpenTelemetry OTLP HTTP endpoint URL",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Show detailed progress",
        ),
    ] = False,
) -> None:
    """Export a stored measure run to the selected output formats."""
    out_dir = output_dir or (project_path / ".specmetrics" / "exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    selected_formats = [f.strip().lower() for f in formats.split(",") if f.strip()]
    invalid_fmts = [f for f in selected_formats if f not in ("json", "csv", "xml")]
    if invalid_fmts:
        typer.echo(
            f"Invalid format(s): {', '.join(invalid_fmts)}. Use json, csv, xml.",
            err=True,
        )
        raise typer.Exit(code=1)

    runs_dir = project_path / ".specmetrics" / "runs"

    target_measure_id = _resolve_target_run(
        measure_id,
        project_path,
        out_dir,
        selected_formats,
        publish,
        otel_endpoint,
        verbose,
    )
    if target_measure_id is None:
        return

    run_dir = runs_dir / target_measure_id
    if not run_dir.exists():
        _fail_run_not_found(target_measure_id, project_path)

    artifacts = read_run_artifacts(run_dir)
    export_selected(selected_formats, run_dir, artifacts, out_dir)

    typer.echo(f"Export complete \u2014 {out_dir}")


def _resolve_target_run(
    measure_id: str | None,
    project_path: Path,
    out_dir: Path,
    selected_formats: list[str],
    publish: bool,
    otel_endpoint: str | None,
    verbose: bool,
) -> str | None:
    if measure_id is not None:
        return measure_id
    runs = list_measure_runs(project_path)
    if not runs:
        typer.echo("No measure runs found. Running measurement pipeline directly...")
        run_pipeline_export(
            project_path, out_dir, selected_formats, publish, otel_endpoint, verbose
        )
        typer.echo(f"Export complete \u2014 {out_dir}")
        return None
    return runs[0]["id"]


def _fail_run_not_found(target_measure_id: str, project_path: Path) -> None:
    available = list_measure_runs(project_path)
    msg = f'Measure run "{target_measure_id}" not found.'
    if available:
        ids = ", ".join(r["id"] for r in available[:5])
        msg += f" Available runs: {ids}"
    typer.echo(msg, err=True)
    raise typer.Exit(code=1)


@export_app.command()
def list(
    project_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpecMetrics project",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ".",
) -> None:
    """List stored measure runs."""
    runs = list_measure_runs(project_path)
    if not runs:
        typer.echo("No measure runs found.")
        return
    typer.echo(f"{'Measure ID':<35} {'Created'}")
    typer.echo(f"{'-' * 35} {'-' * 30}")
    for r in runs:
        created = r["created_at"][:19] if r["created_at"] else "unknown"
        typer.echo(f"{r['id']:<35} {created}")


@export_app.command()
def list_formats() -> None:
    """List available export formats."""
    exporters = discover_exporter_plugins()
    if not exporters:
        typer.echo("No exporter plugins discovered")
        return
    typer.echo("Available export formats:")
    for exp in exporters:
        typer.echo(f"  {exp.format_id():10s}  ({exp.content_type()})")


@export_app.command()
def publisher_status(
    project_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpecMetrics project",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = ".",
) -> None:
    """Show the status of configured publisher endpoints."""
    from specmetrics.plugins.publisher.config import load_publisher_configs

    project_config = project_path / "specmetrics.yml"
    configs = (
        load_publisher_configs(str(project_config)) if project_config.exists() else []
    )

    if not configs:
        typer.echo("No publisher endpoints configured in specmetrics.yml")
        return

    from specmetrics.plugins.publisher.otel_publisher import OTelPublisher

    pub = OTelPublisher()
    pub.initialize(configs)
    statuses = pub.get_status()

    typer.echo("Publisher Status:")
    for s in statuses:
        state = "\u2713" if s.connection_state.value == "connected" else "\u2717"
        typer.echo(f"  {state} {s.endpoint_url}")
        typer.echo(f"     State: {s.connection_state.value}")
        typer.echo(f"     Published: {s.total_metrics_published}")
        typer.echo(f"     Queue: {s.queue_depth}")
        if s.last_error_message:
            typer.echo(f"     Last Error: {s.last_error_message}")
        typer.echo(f"     Uptime: {s.uptime_seconds:.1f}s")