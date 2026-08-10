"""BCP measurement plugin: handler, plugin, and metadata factory."""

from __future__ import annotations

import time
from typing import Any, Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from ._measure import measure_all
from ._telemetry import _sdk_duration, _sdk_errors, _sdk_requests, _story_gauge
from .models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
    MeasurementWarning,
)
from .sdk_adapter import BcpSdkAdapter, check_credentials

logger = structlog.get_logger(__name__)


class BCPHandler:
    """Pipeline event handler for BCP measurement."""

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this handler consumes."""
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self: Self) -> str:
        """Return the unique identifier of this handler."""
        return "bcp_measurement"

    @property
    def stage_name(self: Self) -> str:
        """Return the human-readable name of this handler stage."""
        return "BCP Measurement"

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Measure BCP for the event context and merge stage output."""
        ctx = event.context
        cfm: CanonicalFunctionalModel | None = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None

        logger.info(
            "bcp_measurement_started",
            execution_id=str(ctx.execution_id),
            has_cfm=cfm is not None,
        )

        result = self._measure(cfm, str(ctx.execution_id))

        bcp_entities = [
            {
                "element_id": item.element_id,
                "element_name": item.element_name,
                "bcp_score": item.bcp_score,
                "component_breakdown": item.component_breakdown,
                "generated_story": item.generated_story,
                "status": item.status,
            }
            for item in result.items
            if item.status == "success"
        ]

        payload: dict[str, Any] = {
            "bcp_method": result.method,
            "bcp_sdk_version": result.sdk_version,
            "bcp_provider": result.provider,
            "bcp_total_bcp": result.total_bcp,
            "bcp_measured_items": len(result.items),
            "bcp_items_succeeded": result.execution_metadata.items_succeeded,
            "bcp_items_failed": result.execution_metadata.items_failed,
            "bcp_duration_ms": result.execution_metadata.duration_ms,
            "bcp_warnings": [w.model_dump() for w in result.warnings],
            "bcp_entities": bcp_entities,
        }

        bcp_event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="bcp",
            payload=payload,
            context=ctx,
        )

        logger.info(
            "bcp_measurement_completed",
            total_bcp=result.total_bcp,
            measured_items=len(result.items),
            duration_ms=result.execution_metadata.duration_ms,
        )

        return ctx.merge_stage_output("measurement_result", payload, event=bcp_event)

    def _measure(
        self: Self,
        cfm: CanonicalFunctionalModel | None,
        run_id: str,
    ) -> BCPMeasurementResult:
        start = time.monotonic()
        warnings: list[MeasurementWarning] = []

        if cfm is None:
            return BCPMeasurementResult(
                run_id=run_id,
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0,
                    total_fps_processed=0,
                ),
                warnings=[
                    MeasurementWarning(
                        code="MISSING_CFM",
                        message="Canonical Functional Model is not available. "
                        "BCP measurement skipped.",
                    )
                ],
            )

        provider = self._resolve_provider()
        adapter = BcpSdkAdapter(provider=provider)

        if not adapter.is_available:
            return BCPMeasurementResult(
                run_id=run_id,
                provider=provider,
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0,
                    total_fps_processed=0,
                ),
                warnings=[
                    MeasurementWarning(
                        code="SDK_NOT_AVAILABLE",
                        message=adapter._import_error
                        or "BCP SDK not available. "
                        "Install with: pip install bcp-calculator",
                    )
                ],
            )

        missing_env = check_credentials(provider)
        if missing_env:
            return BCPMeasurementResult(
                run_id=run_id,
                provider=provider,
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0,
                    total_fps_processed=0,
                ),
                warnings=[
                    MeasurementWarning(
                        code="MISSING_CREDENTIALS",
                        message=f"Missing {missing_env} environment variable. "
                        f"Set it in .env or environment.",
                    )
                ],
            )

        items, succeeded, failed, sdk_call_count, sdk_errors = self._measure_fps(
            cfm, adapter
        )

        total_bcp = sum(item.bcp_score for item in items if item.status == "success")
        duration_ms = (time.monotonic() - start) * 1000

        if _story_gauge is not None:
            _story_gauge.set(len(items))

        metadata = ExecutionMetadata(
            duration_ms=round(duration_ms, 2),
            total_fps_processed=len(cfm.functional_processes),
            items_succeeded=succeeded,
            items_failed=failed,
            sdk_call_count=sdk_call_count,
            sdk_errors=sdk_errors,
        )

        return BCPMeasurementResult(
            run_id=run_id,
            provider=provider,
            total_bcp=total_bcp,
            items=items,
            execution_metadata=metadata,
            warnings=warnings,
        )

    def _resolve_provider(self: Self) -> str:
        import os

        return os.environ.get("BCP_PROVIDER", "openai")

    def _measure_fps(
        self: Self,
        cfm: CanonicalFunctionalModel,
        adapter: BcpSdkAdapter,
    ) -> tuple[list[BCPWorkItem], int, int, int, int]:
        return measure_all(
            cfm,
            adapter,
            record_request=lambda: _sdk_requests.add(1)
            if _sdk_requests is not None
            else None,
            record_success=lambda d: _sdk_duration.record(d)
            if _sdk_duration is not None
            else None,
            record_error=lambda n: _sdk_errors.add(n)
            if _sdk_errors is not None
            else None,
            include_evidence=True,
        )


class BCPPlugin:
    """Measurement engine plugin for Business Complexity Points."""

    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return "bcp"

    def supported_methodology(self: Self) -> str:
        """Return the methodology name implemented by this plugin."""
        return "BCP"

    def supported_component_types(self: Self) -> list[str]:
        """Return the CFM component types measured by this plugin."""
        return ["functional_process"]

    def measure(
        self: Self,
        cfm: CanonicalFunctionalModel | None,
        provider: str | None = None,
    ) -> BCPMeasurementResult:
        """Measure BCP for the given canonical functional model."""
        return self._handler_measure(cfm, provider)

    @staticmethod
    def _handler_measure(
        cfm: CanonicalFunctionalModel | None,
        provider: str | None = None,
    ) -> BCPMeasurementResult:
        import os as _os
        import uuid as _uuid

        actual_provider = provider or _os.environ.get("BCP_PROVIDER", "openai")
        start = time.monotonic()
        run_id = str(_uuid.uuid4())
        warnings: list[MeasurementWarning] = []

        if cfm is None:
            return BCPMeasurementResult(
                run_id=run_id,
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0, total_fps_processed=0
                ),
                warnings=[
                    MeasurementWarning(
                        code="MISSING_CFM",
                        message="CFM not available.",
                    )
                ],
            )

        adapter = BcpSdkAdapter(provider=actual_provider)
        if not adapter.is_available:
            return BCPMeasurementResult(
                run_id=run_id,
                provider=actual_provider,
                total_bcp=0.0,
                items=[],
                execution_metadata=ExecutionMetadata(
                    duration_ms=0.0, total_fps_processed=0
                ),
                warnings=[
                    MeasurementWarning(
                        code="SDK_NOT_AVAILABLE",
                        message="BCP SDK not available.",
                    )
                ],
            )

        items, succeeded, failed, sdk_call_count, sdk_errors = measure_all(
            cfm,
            adapter,
            include_evidence=False,
        )

        total_bcp = sum(item.bcp_score for item in items if item.status == "success")
        duration_ms = (time.monotonic() - start) * 1000

        return BCPMeasurementResult(
            run_id=run_id,
            provider=actual_provider,
            total_bcp=total_bcp,
            items=items,
            execution_metadata=ExecutionMetadata(
                duration_ms=round(duration_ms, 2),
                total_fps_processed=len(cfm.functional_processes),
                items_succeeded=succeeded,
                items_failed=failed,
                sdk_call_count=sdk_call_count,
                sdk_errors=sdk_errors,
            ),
            warnings=warnings,
        )


def create_bcp_measurement_metadata() -> PluginMetadata:
    """Build the plugin metadata entry for the BCP measurement plugin."""
    return PluginMetadata(
        id="bcp",
        api_version="0.1.0",
        plugin_type=PluginType.MEASUREMENT,
        handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
        handler_factory=lambda: BCPHandler(),
        name="BCP",
        description="Business Complexity Points — estimates business complexity via external LLM-based SDK from CFM",
        version="0.1.0",
    )