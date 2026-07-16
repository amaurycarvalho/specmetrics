from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from specmetrics.kernel.diagnostics import StageStatus as KernelStageStatus
from specmetrics.kernel.events import EventType
from specmetrics.kernel.exceptions import PipelineError
from specmetrics.kernel.handler_registry import HandlerRegistry
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import CANONICAL_EVENT_ORDER, PipelineEngine
from specmetrics.kernel.plugin_discovery import load_plugins
from specmetrics.kernel.plugin_registry import PluginRegistry
from specmetrics.kernel.plugin_validation import PluginValidator

from .enums import (
    OutputFormat,
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)
from .models import (
    MeasurementResult,
    PipelineRequest,
    PipelineResult,
    PluginInfo,
    StageResult,
    VersionInfo,
)

logger = structlog.get_logger(__name__)

_STAGE_NAME_TO_EVENT: dict[StageName, EventType] = {
    StageName.DISCOVER: EventType.REPOSITORY_LOADED,
    StageName.EXTRACT: EventType.DOCUMENTS_DISCOVERED,
    StageName.GRAPH: EventType.SEMANTIC_EXTRACTION_COMPLETED,
    StageName.CFM: EventType.EVIDENCE_GRAPH_BUILT,
    StageName.RULE: EventType.CANONICAL_MODEL_BUILT,
    StageName.MEASURE: EventType.RULE_PACK_APPLIED,
    StageName.EXPORT: EventType.MEASUREMENT_COMPLETED,
}


def _stage_name_from_event(event_type: EventType) -> str:
    for stage_name, et in _STAGE_NAME_TO_EVENT.items():
        if et == event_type:
            return stage_name.value
    return event_type.value


def _resolve_event_order(
    stages: list[StageName] | None,
    from_stage: StageName | None,
) -> list[EventType]:
    if stages is not None:
        return [_STAGE_NAME_TO_EVENT[s] for s in stages]
    if from_stage is not None:
        start_event = _STAGE_NAME_TO_EVENT[from_stage]
        started = False
        result: list[EventType] = []
        for et in CANONICAL_EVENT_ORDER:
            if et == start_event:
                started = True
            if started:
                result.append(et)
        return result
    return list(CANONICAL_EVENT_ORDER)


class PipelineOrchestrator:
    """Shared pipeline orchestrator consumed by both CLI and MCP interfaces.

    Discovers plugins, executes the pipeline via Kernel PipelineEngine,
    and returns structured PipelineResult. Ensures behavioral consistency
    across all interaction mechanisms.
    """

    def __init__(self) -> None:
        self._registry = PluginRegistry()
        self._handler_registry = HandlerRegistry()
        self._plugin_validator = PluginValidator()

    def discover_plugins(self) -> None:
        self._registry = load_plugins(
            registry=self._registry,
            validator=self._plugin_validator,
        )
        self._registry.install_handlers(self._handler_registry)

    def list_plugins(self) -> list[PluginInfo]:
        descriptors = self._registry.list_plugins()
        result: list[PluginInfo] = []
        for d in descriptors:
            m = d.metadata
            result.append(
                PluginInfo(
                    name=m.name or m.id,
                    version=m.version or "0.0.0",
                    type=m.plugin_type.value,
                    enabled=d.status.value == "registered",
                    compatible=True,
                )
            )
        return result

    def get_version_info(self) -> VersionInfo:
        import sys

        from specmetrics import __version__ as platform_version

        return VersionInfo(
            platform_version=platform_version,
            python_version=sys.version.split()[0],
            plugins=self.list_plugins(),
        )

    def execute(self, request: PipelineRequest) -> PipelineResult:
        started_at = datetime.now(timezone.utc)

        if not request.project_path.exists():
            return PipelineResult(
                status=PipelineStatus.FAILED,
                error=f"Project path not found: {request.project_path}",
            )

        self.discover_plugins()

        event_order = _resolve_event_order(request.stages, request.from_stage)

        engine = PipelineEngine(self._handler_registry)
        context = PipelineContext()

        try:
            result_ctx = engine.run(context)
        except PipelineError as exc:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
            return PipelineResult(
                status=PipelineStatus.FAILED,
                project_path=request.project_path,
                error=str(exc),
                duration_seconds=elapsed,
            )

        elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()

        stages_executed = self._build_stage_results(result_ctx, event_order)
        measurement = self._extract_measurement(result_ctx)
        export_path = self._handle_export(request, result_ctx)

        has_failures = any(
            s.status == StageExecutionStatus.FAILED for s in stages_executed
        )

        return PipelineResult(
            status=PipelineStatus.FAILED if has_failures else PipelineStatus.SUCCESS,
            project_path=request.project_path,
            stages_executed=stages_executed,
            measurement=measurement,
            duration_seconds=elapsed,
            export_path=export_path,
            canonical_model=result_ctx.canonical_model,
        )

    def _build_stage_results(
        self,
        ctx: PipelineContext,
        event_order: list[EventType],
    ) -> list[StageResult]:
        if not ctx.diagnostics:
            return []

        results: list[StageResult] = []
        valid_stage_names = {s.value for s in StageName}
        for event_type in event_order:
            stage_name = _stage_name_from_event(event_type)
            if stage_name not in valid_stage_names:
                continue
            timing = ctx.diagnostics.stage_timings.get(stage_name)
            if timing is None:
                results.append(
                    StageResult(
                        stage=StageName(stage_name),
                        status=StageExecutionStatus.SKIPPED,
                    )
                )
                continue
            kernel_status = timing.status
            if kernel_status == KernelStageStatus.COMPLETED:
                status = StageExecutionStatus.COMPLETED
            elif kernel_status == KernelStageStatus.FAILED:
                status = StageExecutionStatus.FAILED
            elif kernel_status == KernelStageStatus.RUNNING:
                status = StageExecutionStatus.RUNNING
            else:
                status = StageExecutionStatus.PENDING

            duration_s = (
                (timing.duration_ms or 0) / 1000.0
                if timing.duration_ms is not None
                else 0.0
            )
            results.append(
                StageResult(
                    stage=StageName(stage_name),
                    status=status,
                    duration_seconds=duration_s,
                )
            )
        return results

    def _extract_measurement(
        self, ctx: PipelineContext
    ) -> MeasurementResult | None:
        if ctx.measurement_result is None:
            return None

        mr = ctx.measurement_result
        if isinstance(mr, dict):
            return MeasurementResult(
                total_function_points=mr.get("total_function_points", 0),
                breakdown=mr.get("breakdown", {}),
                complexity_distribution=mr.get("complexity_distribution", {}),
                evidence_refs=mr.get("evidence_refs", []),
                applied_rule_pack=mr.get("applied_rule_pack", ""),
            )
        return MeasurementResult()

    def _handle_export(
        self, request: PipelineRequest, ctx: PipelineContext
    ) -> Path | None:
        if request.output_format == OutputFormat.NONE:
            return None

        export_dir = (
            request.output_path
            if request.output_path
            else request.project_path / ".specmetrics" / "output"
        )
        export_dir.mkdir(parents=True, exist_ok=True)

        if request.output_format in (OutputFormat.JSON, OutputFormat.CSV, OutputFormat.XML):
            return self._handle_structured_export(request, ctx, export_dir)

        ext = request.output_format.value
        export_file = export_dir / f"specmetrics-output.{ext}"

        result_data: dict[str, Any] = {
            "total_function_points": (
                ctx.measurement_result.get("total_function_points", 0)
                if isinstance(ctx.measurement_result, dict)
                else 0
            ),
            "status": "completed" if ctx.diagnostics and not ctx.diagnostics.errors else "failed",
            "duration_ms": (
                ctx.diagnostics.total_duration_ms
                if ctx.diagnostics
                else None
            ),
        }
        export_file.write_text(str(result_data))
        logger.info("export_written", path=str(export_file))
        return export_file

    def _handle_structured_export(
        self, request: PipelineRequest, ctx: PipelineContext, export_dir: Path
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
                logger.warning("exporter_load_failed", entry_point=ep.name, error=str(exc))

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
