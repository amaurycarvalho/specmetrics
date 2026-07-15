from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import structlog
import typer

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.plugins.exporter.base import ExporterPlugin
from specmetrics.plugins.exporter.orchestrator import ExportOrchestrator
from specmetrics.plugins.publisher.base import PublisherConfig, PublisherConfiguration
from specmetrics.plugins.publisher.orchestrator import publish_all

logger = structlog.get_logger(__name__)

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
    project_path: Path = typer.Argument(
        ".",
        help="Path to the SpecMetrics project",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    formats: str = typer.Option(
        "json,csv,xml",
        "--format",
        "-f",
        help="Comma-separated list of export formats",
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

    out_dir = output_dir or (project_path / "exports")
    out_dir.mkdir(parents=True, exist_ok=True)

    selected_formats = [f.strip() for f in formats.split(",") if f.strip()]
    export_orch = ExportOrchestrator(exporters)
    export_results = export_orch.export_to_dir(
        cfm=cfm,
        output_dir=out_dir,
        formats=selected_formats,
    )

    typer.echo("Export results:")
    for r in export_results:
        status = "\u2713" if r["status"] == "completed" else "\u2717"
        typer.echo(
            f"  {status} {r['format']}: {r.get('path', r.get('error', 'unknown'))}"
        )

    if publish:
        from specmetrics.plugins.exporter.models import ExportMetadata
        from specmetrics.plugins.publisher.config import load_publisher_configs

        project_config = project_path / "specmetrics.yml"
        publisher_configs = (
            load_publisher_configs(str(project_config))
            if project_config.exists()
            else []
        )

        if otel_endpoint and not publisher_configs:
            publisher_configs = [PublisherConfiguration(endpoint_url=otel_endpoint)]

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
            publisher_configs=publisher_configs,
        )
        typer.echo("Publish results:")
        for r in pub_results:
            status = "\u2713" if r["success"] else "\u2717"
            typer.echo(f"  {status} {r['publisher']}: {r['message']}")

    typer.echo(f"Export complete — {out_dir}")


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
