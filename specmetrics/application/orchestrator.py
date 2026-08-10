"""Orchestration of the full specification measurement pipeline.

The orchestrator discovers plugins, executes the pipeline through the Kernel
``PipelineEngine``, and assembles the structured ``PipelineResult`` consumed by
the CLI, MCP, and library interfaces.

This module is intentionally a thin coordinator. Each result-assembly
responsibility (entity building, metric assembly, stage/result rows, artifact
persistence, structured export) is delegated to a dedicated unit under
``specmetrics/application/``:

* ``stage_mapping`` - stage/event mapping, event-order resolution, framework detection
* ``truncation`` - text/entity truncation helpers
* ``artifact_persistence`` - ``save_run_artifacts`` / ``read_run_artifacts``
* ``entity_builders`` - per-stage entity payload builders
* ``metric_builders`` - metric and measurement result assembly
* ``stage_builders`` - stage result/detail rows and counting
* ``export_writer`` - output / structured export and error assembly
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import structlog

from specmetrics.infrastructure.config.loader import ConfigurationSystem
from specmetrics.kernel.adapter_registry import AdapterRegistry
from specmetrics.kernel.events import EventType
from specmetrics.kernel.exceptions import PipelineError
from specmetrics.kernel.handler_registry import HandlerRegistry
from specmetrics.kernel.llm_gateway import LLMGateway, LLMGatewayConfig
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.pipeline_engine import PipelineEngine
from specmetrics.kernel.plugin_discovery import load_plugins
from specmetrics.kernel.plugin_registry import PluginRegistry
from specmetrics.kernel.plugin_validation import PluginValidator

from .artifact_persistence import read_run_artifacts, save_run_artifacts
from .entity_builders import _build_stage_entities
from .enums import PipelineStatus, StageExecutionStatus
from .export_writer import (
    _build_output_errors,
    _get_llm_info,
    _handle_export,
    _write_json_output,
)
from .metric_builders import _build_metric_results, _extract_measurement
from .models import (
    MeasurementResult,
    PipelineRequest,
    PipelineResult,
    PluginInfo,
    VersionInfo,
)
from .stage_builders import _build_stage_details, _build_stage_results
from .stage_mapping import _resolve_event_order, detect_framework

__all__ = [
    "PipelineOrchestrator",
    "read_run_artifacts",
    "save_run_artifacts",
]

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """Shared pipeline orchestrator consumed by both CLI and MCP interfaces.

    Discovers plugins, executes the pipeline via Kernel PipelineEngine,
    and returns structured PipelineResult. Ensures behavioral consistency
    across all interaction mechanisms.
    """

    def __init__(self: Self) -> None:
        """Initialize the orchestrator with empty registries."""
        self._registry = PluginRegistry()
        self._handler_registry = HandlerRegistry()
        self._plugin_validator = PluginValidator()
        self._config_system: ConfigurationSystem | None = None
        self._framework_detected: str = ""

    def set_config_system(self: Self, config_system: ConfigurationSystem) -> None:
        """Set the configuration system used by the orchestrator."""
        self._config_system = config_system

    def discover_plugins(self: Self, metrics_filter: list[str] | None = None) -> None:
        """Discover plugins and install their handlers into the handler registry."""
        self._registry = load_plugins(
            registry=self._registry,
            validator=self._plugin_validator,
        )
        self._registry.install_handlers(
            self._handler_registry, metrics_filter=metrics_filter
        )
        if self._config_system is not None:
            for desc in self._registry.list_plugins():
                factory = desc.metadata.handler_factory
                if factory is not None:
                    try:
                        handler = factory()
                        schema_method = getattr(handler, "config_schema", None)
                        if schema_method is not None and callable(schema_method):
                            schema = schema_method()
                            if schema is not None:
                                self._config_system.register_plugin_schema(
                                    desc.metadata.id,
                                    schema,
                                )
                    except Exception:
                        pass

    def list_plugins(self: Self) -> list[PluginInfo]:
        """Return metadata about all discovered plugins."""
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

    def get_version_info(self: Self) -> VersionInfo:
        """Return platform, Python, and plugin version information."""
        import sys

        from specmetrics import __version__ as platform_version

        return VersionInfo(
            platform_version=platform_version,
            python_version=sys.version.split()[0],
            plugins=self.list_plugins(),
        )

    def execute(self: Self, request: PipelineRequest) -> PipelineResult:
        """Execute the pipeline for the given request and return its result."""
        started_at = datetime.now(UTC)

        if not request.project_path.exists():
            return PipelineResult(
                status=PipelineStatus.FAILED,
                error=f"Project path not found: {request.project_path}",
            )

        self.discover_plugins(metrics_filter=request.metrics_filter)

        event_order = _resolve_event_order(request.stages, request.from_stage)

        engine = PipelineEngine(self._handler_registry)
        adapter_registry = AdapterRegistry(self._registry)

        config_provider = None
        if self._config_system is not None:
            try:
                config_provider = self._config_system.load()
            except Exception:
                logger.warning("config_load_failed")

        llm_gateway = LLMGateway(LLMGatewayConfig(rpm_limit=request.llm_rpm_limit))

        context = PipelineContext(
            repository=request.project_path,
            metadata={
                "adapter_registry": adapter_registry,
                "config": config_provider,
                "llm_gateway": llm_gateway,
            },
        )

        try:
            result_ctx = engine.run(context)
        except PipelineError as exc:
            elapsed = (datetime.now(UTC) - started_at).total_seconds()
            return PipelineResult(
                status=PipelineStatus.FAILED,
                project_path=request.project_path,
                error=str(exc),
                duration_seconds=elapsed,
            )

        elapsed = (datetime.now(UTC) - started_at).total_seconds()

        stages_executed = self._build_stage_results(
            result_ctx, event_order, request.metrics_filter
        )
        measurement = self._extract_measurement(result_ctx)
        metric_results = self._build_metric_results(
            result_ctx, request.metrics_filter
        )
        output_errors = self._build_output_errors(result_ctx)
        llm_provider, llm_model = self._get_llm_info()
        export_path = self._handle_export(request, result_ctx)
        stage_entities = self._build_stage_entities(
            result_ctx, event_order, export_path
        )
        stage_details = self._build_stage_details(
            result_ctx, event_order, request.metrics_filter, export_path
        )

        max_entities_per_stage = 5000
        if config_provider is not None:
            try:
                max_entities_per_stage = config_provider.get(
                    "run_artifacts.max_entities_per_stage", 5000
                )
            except Exception:
                pass

        has_failures = any(
            s.status == StageExecutionStatus.FAILED for s in stages_executed
        )

        measurement_result_raw: dict[str, Any] = {}
        mr = getattr(result_ctx, "measurement_result", None)
        if isinstance(mr, dict):
            measurement_result_raw = mr

        llm_call_stats = llm_gateway.get_summary_stats()

        return PipelineResult(
            status=PipelineStatus.FAILED if has_failures else PipelineStatus.SUCCESS,
            project_path=request.project_path,
            run_id=str(result_ctx.execution_id),
            stages_executed=stages_executed,
            measurement=measurement,
            duration_seconds=elapsed,
            export_path=export_path,
            _framework_detected=getattr(self, "_framework_detected", ""),
            canonical_model=result_ctx.canonical_model,
            metric_results=metric_results,
            stage_entities=stage_entities,
            stage_details=stage_details,
            output_errors=output_errors,
            llm_provider=llm_provider,
            llm_model=llm_model,
            _max_entities_per_stage=max_entities_per_stage,
            measurement_result_raw=measurement_result_raw,
            llm_call_stats=llm_call_stats,
        )

    def _build_metric_results(
        self: Self,
        ctx: PipelineContext,
        metrics_filter: list[str] | None,
    ) -> list[Any]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _build_metric_results(ctx, metrics_filter)

    def _build_stage_results(
        self: Self,
        ctx: PipelineContext,
        event_order: list[EventType],
        metrics_filter: list[str] | None = None,
    ) -> list[Any]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _build_stage_results(
            ctx,
            event_order,
            metrics_filter,
            on_discover=lambda c: setattr(
                self, "_framework_detected", detect_framework(c)
            ),
        )

    def _build_stage_details(
        self: Self,
        ctx: PipelineContext,
        event_order: list[EventType],
        metrics_filter: list[str] | None = None,
        export_path: Path | None = None,
    ) -> list[Any]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _build_stage_details(ctx, event_order, metrics_filter, export_path)

    def _build_stage_entities(
        self: Self,
        ctx: PipelineContext,
        event_order: list[EventType],
        export_path: Path | None,
    ) -> dict[str, list[dict]]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _build_stage_entities(ctx, event_order, export_path)

    def _extract_measurement(
        self: Self, ctx: PipelineContext
    ) -> MeasurementResult | None:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _extract_measurement(ctx)

    def _build_output_errors(self: Self, ctx: PipelineContext) -> list[Any]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _build_output_errors(ctx)

    def _get_llm_info(self: Self) -> tuple[str, str]:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _get_llm_info(self._config_system)

    def _handle_export(
        self: Self, request: PipelineRequest, ctx: PipelineContext
    ) -> Path | None:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _handle_export(
            request,
            ctx,
            self._config_system,
            getattr(self, "_framework_detected", ""),
        )

    def _write_json_output(
        self: Self,
        request: PipelineRequest,
        ctx: PipelineContext,
        export_dir: Path,
        metric_results: list[Any],
        stage_details: list[Any],
        output_errors: list[Any],
    ) -> Path:
        """Thin delegating wrapper kept for test compatibility (FR-006)."""
        return _write_json_output(
            request,
            ctx,
            export_dir,
            metric_results,
            stage_details,
            output_errors,
            config_system=self._config_system,
            framework_detected=getattr(self, "_framework_detected", ""),
        )