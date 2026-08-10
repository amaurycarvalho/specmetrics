"""Output writing and structured export for pipeline results.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). Handles writing the legacy JSON
output and delegating structured exports (JSON/CSV/XML) to the exporter plugin
orchestrator.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import structlog

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import (
    ErrorOutputItem,
    MetricOutputItem,
    PipelineRequest,
    StageOutputItem,
)
from specmetrics.cli.output_models import (
    ErrorRecord,
    MeasureMetadata,
    MeasureOutput,
)
from specmetrics.cli.output_models import (
    MetricResult as OutputMetricResult,
)
from specmetrics.cli.output_models import (
    StageInfo as OutputStageInfo,
)
from specmetrics.infrastructure.config.loader import ConfigurationSystem
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import CANONICAL_EVENT_ORDER as _ALL_EVENTS

from .metric_builders import _build_metric_results
from .stage_builders import _build_stage_details

logger = structlog.get_logger(__name__)


def _get_llm_info(
    config_system: ConfigurationSystem | None,
) -> tuple[str, str]:
    provider = "none"
    model = ""
    if config_system is not None:
        try:
            cfg = config_system.load()
            if cfg:
                provider = getattr(cfg, "llm_provider", "") or "none"
                model = getattr(cfg, "llm_model", "") or ""
        except Exception:
            pass
    return provider, model


def _write_json_output(
    request: PipelineRequest,
    ctx: PipelineContext,
    export_dir: Path,
    metric_results: list[MetricOutputItem],
    stage_details: list[StageOutputItem],
    output_errors: list[ErrorOutputItem],
    config_system: ConfigurationSystem | None,
    framework_detected: str,
) -> Path:
    export_file = export_dir / "specmetrics-output.json"

    llm_provider, llm_model = _get_llm_info(config_system)

    llm_info: dict[str, str] = {"provider": llm_provider}
    if llm_model:
        llm_info["model"] = llm_model

    measure_meta = MeasureMetadata(
        id=request.measure_id,
        id_path=request.measure_id,
        sdd_framework=framework_detected or "unknown",
        created=datetime.now(UTC).isoformat(),
        llm=llm_info,
        project_path=str(request.project_path),
    )

    output = MeasureOutput(
        measure=measure_meta,
        results=[
            OutputMetricResult(
                name=r.name,
                total=r.total,
                status=r.status,
                duration_ms=r.duration_ms,
            )
            for r in metric_results
        ],
        stages=[
            OutputStageInfo(
                name=s.name,
                count=s.count,
                count_type=s.count_type,
                duration_ms=s.duration_ms,
            )
            for s in stage_details
        ],
        errors=[
            ErrorRecord(
                stage=e.stage,
                message=e.message,
                details=e.details,
            )
            for e in output_errors
        ],
    )

    export_file.write_text(output.model_dump_json(indent=2))
    logger.info("json_export_written", path=str(export_file))
    return export_file


def _build_output_errors(ctx: PipelineContext) -> list[ErrorOutputItem]:
    if not ctx.diagnostics or not ctx.diagnostics.errors:
        return []
    return [
        ErrorOutputItem(
            stage=str(getattr(err, "stage_name", "")),
            message=getattr(err, "message", str(err)),
        )
        for err in ctx.diagnostics.errors
    ]


def _handle_export(
    request: PipelineRequest,
    ctx: PipelineContext,
    config_system: ConfigurationSystem | None,
    framework_detected: str,
) -> Path | None:
    if request.output_format == OutputFormat.NONE:
        return None

    export_dir = (
        request.output_path
        if request.output_path
        else request.project_path / ".specmetrics" / "output"
    )
    export_dir.mkdir(parents=True, exist_ok=True)

    if request.output_format in (
        OutputFormat.JSON,
        OutputFormat.CSV,
        OutputFormat.XML,
    ):
        return _handle_structured_export(request, ctx, export_dir)

    export_file = export_dir / "specmetrics-output.json"

    metric_results = _build_metric_results(ctx, request.metrics_filter)
    stage_details = _build_stage_details(
        ctx, _ALL_EVENTS, request.metrics_filter, export_file
    )
    output_errors = _build_output_errors(ctx)

    _write_json_output(
        request,
        ctx,
        export_dir,
        metric_results,
        stage_details,
        output_errors,
        config_system,
        framework_detected,
    )
    logger.info("export_written", path=str(export_file))
    return export_file


def _handle_structured_export(
    request: PipelineRequest,
    ctx: PipelineContext,
    export_dir: Path,
) -> Path | None:
    from importlib.metadata import entry_points

    from specmetrics.plugins.exporter.base import ExporterPlugin
    from specmetrics.plugins.exporter.orchestrator import ExportOrchestrator

    exporters: list[ExporterPlugin] = []
    for ep in entry_points(group="specmetrics.exporters"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                exporters.append(cls())
        except Exception as exc:
            logger.warning(
                "exporter_load_failed", entry_point=ep.name, error=str(exc)
            )

    if not exporters:
        logger.warning("No exporter plugins available for structured export")
        return None

    cfm = ctx.canonical_model
    if cfm is None:
        logger.warning("No canonical model available for export")
        return None

    orch = ExportOrchestrator(exporters)
    fmt = request.output_format.value
    orch.export_to_dir(cfm, export_dir, formats=[fmt])
    export_file = export_dir / f"measurements.{fmt}"
    logger.info("structured_export_completed", format=fmt, path=str(export_file))
    return export_file