from __future__ import annotations

import json
import shutil
from importlib.metadata import entry_points
from pathlib import Path

import structlog
import typer

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import (
    PipelineOrchestrator,
    read_run_artifacts,
)
from specmetrics.plugins.exporter.base import ExporterPlugin
from specmetrics.plugins.exporter.orchestrator import (
    ExportOrchestrator,
    stage_to_csv,
    stage_to_xml,
)
from specmetrics.plugins.publisher.base import PublisherConfig
from specmetrics.plugins.publisher.orchestrator import publish_all

logger = structlog.get_logger(__name__)

MEASURE_ID_PATTERN = "????????-??????-????????"


def list_measure_runs(project_path: Path) -> list[dict]:
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


def _discover_exporter_plugins() -> list[ExporterPlugin]:
    plugins: list[ExporterPlugin] = []
    for ep in entry_points(group="specmetrics.exporters"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                plugins.append(cls())
        except Exception as exc:
            logger.warning("exporter_load_failed", entry_point=ep.name, error=str(exc))
    return plugins


@export_app.command()
def run(
    measure_id: str = typer.Argument(
        None,
        help="Measure ID to export (default: most recent run)",
    ),
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    formats: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Comma-separated list of export formats (json, csv, xml)",
    ),
    output_dir: Path = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Directory to write export files to",
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    publish: bool = typer.Option(
        False,
        "--publish",
        help="Publish results to configured telemetry backends",
    ),
    otel_endpoint: str = typer.Option(
        None,
        "--otel-endpoint",
        help="OpenTelemetry OTLP HTTP endpoint URL",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed progress",
    ),
) -> None:
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

    target_measure_id = measure_id
    runs_dir = project_path / ".specmetrics" / "runs"

    if target_measure_id is None:
        runs = list_measure_runs(project_path)
        if not runs:
            typer.echo(
                "No measure runs found. Running measurement pipeline directly..."
            )
            _run_pipeline_export(
                project_path, out_dir, selected_formats, publish, otel_endpoint, verbose
            )
            typer.echo(f"Export complete — {out_dir}")
            return
        target_measure_id = runs[0]["id"]

    run_dir = runs_dir / target_measure_id
    if not run_dir.exists():
        available = list_measure_runs(project_path)
        msg = f'Measure run "{target_measure_id}" not found.'
        if available:
            ids = ", ".join(r["id"] for r in available[:5])
            msg += f" Available runs: {ids}"
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    artifacts = read_run_artifacts(run_dir)

    for fmt in selected_formats:
        if fmt == "json":
            for src in run_dir.glob("*.json"):
                if src.name == "metadata.json":
                    continue
                dst = out_dir / src.name
                shutil.copy2(src, dst)
                typer.echo(f"  \u2713 json: {dst.name}")
        elif fmt == "csv":
            for fname, data in artifacts.items():
                if fname == "metadata":
                    continue
                csv_content = stage_to_csv(fname, data)
                dst = out_dir / f"{fname}.csv"
                dst.write_text(csv_content)
                typer.echo(f"  \u2713 csv: {dst.name}")
        elif fmt == "xml":
            for fname, data in artifacts.items():
                if fname == "metadata":
                    continue
                xml_content = stage_to_xml(fname, data)
                dst = out_dir / f"{fname}.xml"
                dst.write_text(xml_content)
                typer.echo(f"  \u2713 xml: {dst.name}")

    typer.echo(f"Export complete — {out_dir}")


def _run_pipeline_export(
    project_path: Path,
    out_dir: Path,
    selected_formats: list[str],
    publish: bool,
    otel_endpoint: str | None,
    verbose: bool,
) -> None:

    orch = PipelineOrchestrator()
    request = PipelineRequest(
        project_path=project_path,
        output_format=OutputFormat.NONE,
        verbose=verbose,
    )
    result = orch.execute(request)

    if result.status.value == "failed":
        typer.echo(f"Pipeline failed: {result.error}", err=True)
        raise typer.Exit(code=1)

    cfm = result.canonical_model
    if cfm is None:
        typer.echo("No measurement data available to export", err=True)
        raise typer.Exit(code=1)

    exporters = _discover_exporter_plugins()
    if not exporters:
        typer.echo("No exporter plugins found", err=True)
        raise typer.Exit(code=1)

    if "json" in selected_formats or not selected_formats:
        export_orch = ExportOrchestrator(exporters)
        export_results = export_orch.export_to_dir(
            cfm=cfm,
            output_dir=out_dir,
            formats=selected_formats,
        )
        for r in export_results:
            status = "\u2713" if r["status"] == "completed" else "\u2717"
            typer.echo(
                f"  {status} {r['format']}: {r.get('path', r.get('error', 'unknown'))}"
            )

    if publish:
        from specmetrics.plugins.exporter.models import ExportMetadata

        measurements = _extract_measurements(cfm)
        metadata = ExportMetadata(
            run_id=cfm.run_id,
            function_count=len(measurements),
        )
        configs: dict[str, PublisherConfig] = {}
        if otel_endpoint:
            configs["otel"] = PublisherConfig(endpoint_url=otel_endpoint)

        pub_results = publish_all(
            measurements,
            metadata,
            configs=configs,
            publisher_configs=[],
        )
        for r in pub_results:
            status = "\u2713" if r["success"] else "\u2717"
            typer.echo(f"  {status} {r['publisher']}: {r['message']}")


@export_app.command()
def list(
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
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
    exporters = _discover_exporter_plugins()
    if not exporters:
        typer.echo("No exporter plugins discovered")
        return
    typer.echo("Available export formats:")
    for exp in exporters:
        typer.echo(f"  {exp.format_id():10s}  ({exp.content_type()})")


@export_app.command()
def publisher_status(
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
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


def _extract_measurements(cfm: object) -> list:
    from specmetrics.plugins.exporter.models import Measurement

    measurements: list[Measurement] = []
    try:
        processes = getattr(cfm, "functional_processes", {})
        for proc in processes.values():
            measurements.append(
                Measurement(
                    function_id=getattr(proc, "id", ""),
                    function_name=getattr(proc, "name", ""),
                    category="functional_process",
                    evidence=[getattr(proc, "evidence")]
                    if hasattr(proc, "evidence")
                    else [],
                )
            )
    except Exception:
        pass
    return measurements
