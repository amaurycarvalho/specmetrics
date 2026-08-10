"""Exporter implementation helpers for the CLI export commands."""

from __future__ import annotations

import shutil
from importlib.metadata import entry_points
from pathlib import Path

import structlog
import typer

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.plugins.exporter.base import ExporterPlugin
from specmetrics.plugins.exporter.orchestrator import (
    ExportOrchestrator,
    stage_to_csv,
    stage_to_xml,
)
from specmetrics.plugins.publisher.base import PublisherConfig
from specmetrics.plugins.publisher.orchestrator import publish_all

logger = structlog.get_logger(__name__)


def discover_exporter_plugins() -> list[ExporterPlugin]:
    """Discover exporter plugins registered via entry points."""
    plugins: list[ExporterPlugin] = []
    for ep in entry_points(group="specmetrics.exporters"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                plugins.append(cls())
        except Exception as exc:
            logger.warning("exporter_load_failed", entry_point=ep.name, error=str(exc))
    return plugins


def export_selected(
    selected_formats: list[str],
    run_dir: Path,
    artifacts: dict,
    out_dir: Path,
) -> None:
    """Export the stored artifacts in each of the selected formats."""
    for fmt in selected_formats:
        if fmt == "json":
            _export_json(run_dir, out_dir)
        elif fmt == "csv":
            _export_csv(artifacts, out_dir)
        elif fmt == "xml":
            _export_xml(artifacts, out_dir)


def _export_json(run_dir: Path, out_dir: Path) -> None:
    for src in run_dir.glob("*.json"):
        if src.name == "metadata.json":
            continue
        dst = out_dir / src.name
        shutil.copy2(src, dst)
        typer.echo(f"  \u2713 json: {dst.name}")


def _export_csv(artifacts: dict, out_dir: Path) -> None:
    for fname, data in artifacts.items():
        if fname == "metadata":
            continue
        csv_content = stage_to_csv(fname, data)
        dst = out_dir / f"{fname}.csv"
        dst.write_text(csv_content)
        typer.echo(f"  \u2713 csv: {dst.name}")


def _export_xml(artifacts: dict, out_dir: Path) -> None:
    for fname, data in artifacts.items():
        if fname == "metadata":
            continue
        xml_content = stage_to_xml(fname, data)
        dst = out_dir / f"{fname}.xml"
        dst.write_text(xml_content)
        typer.echo(f"  \u2713 xml: {dst.name}")


def run_pipeline_export(
    project_path: Path,
    out_dir: Path,
    selected_formats: list[str],
    publish: bool,
    otel_endpoint: str | None,
    verbose: bool,
) -> None:
    """Run the measurement pipeline and export its results directly."""
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

    exporters = discover_exporter_plugins()
    if not exporters:
        typer.echo("No exporter plugins found", err=True)
        raise typer.Exit(code=1)

    if "json" in selected_formats or not selected_formats:
        _export_canonical_model(cfm, exporters, out_dir, selected_formats)

    if publish:
        _publish_canonical_model(cfm, otel_endpoint)


def _export_canonical_model(
    cfm: object,
    exporters: list[ExporterPlugin],
    out_dir: Path,
    selected_formats: list[str],
) -> None:
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


def _publish_canonical_model(cfm: object, otel_endpoint: str | None) -> None:
    from specmetrics.plugins.exporter.models import ExportMetadata

    measurements = extract_measurements(cfm)
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


def extract_measurements(cfm: object) -> list:
    """Extract functional process measurements from a canonical model."""
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
                    evidence=[proc.evidence]
                    if hasattr(proc, "evidence")
                    else [],
                )
            )
    except Exception:
        pass
    return measurements