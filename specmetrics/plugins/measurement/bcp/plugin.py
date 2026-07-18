from __future__ import annotations

import time
from typing import Any, Optional

import structlog

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("specmetrics.bcp")
    _sdk_duration = _meter.create_histogram(
        name="bcp.sdk.execution.duration",
        description="Duration of BCP SDK execution per item",
        unit="ms",
    )
    _story_gauge = _meter.create_gauge(
        name="bcp.processed_stories",
        description="Number of stories processed",
    )
    _sdk_requests = _meter.create_counter(
        name="bcp.sdk.requests",
        description="Total SDK requests made",
    )
    _sdk_errors = _meter.create_counter(
        name="bcp.sdk.errors",
        description="Total SDK errors encountered",
    )
except Exception:
    _sdk_duration = None
    _story_gauge = None
    _sdk_requests = None
    _sdk_errors = None

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
    MeasurementEvidence,
    MeasurementWarning,
)
from .sdk_adapter import BcpSdkAdapter, check_credentials
from .story_generator import generate_story

logger = structlog.get_logger(__name__)


class BCPHandler:
    @property
    def handled_event_type(self) -> EventType:
        return EventType.MEASUREMENT_COMPLETED

    @property
    def handler_id(self) -> str:
        return "bcp_measurement"

    @property
    def stage_name(self) -> str:
        return "BCP Measurement"

    def handle(self, event: PipelineEvent) -> PipelineContext:
        ctx = event.context
        cfm: Optional[CanonicalFunctionalModel] = ctx.canonical_model

        if not isinstance(cfm, CanonicalFunctionalModel):
            cfm = None

        logger.info(
            "bcp_measurement_started",
            execution_id=str(ctx.execution_id),
            has_cfm=cfm is not None,
        )

        result = self._measure(cfm, str(ctx.execution_id))

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

        return ctx.merge_stage_output(
            "measurement_result", payload, event=bcp_event
        )

    def _measure(
        self,
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
                        message=adapter._import_error or "BCP SDK not available. "
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

        items: list[BCPWorkItem] = []
        succeeded = 0
        failed = 0
        sdk_call_count = 0
        sdk_errors = 0

        for fp_id, fp in cfm.functional_processes.items():
            story = generate_story(fp, cfm)

            if _sdk_requests is not None:
                _sdk_requests.add(1)

            sdk_result = adapter.calculate(story)
            sdk_call_count += 1

            if sdk_result.errors:
                failed += 1
                sdk_errors += len(sdk_result.errors)
                if _sdk_errors is not None:
                    _sdk_errors.add(len(sdk_result.errors))

                items.append(
                    BCPWorkItem(
                        element_id=fp_id,
                        element_name=fp.name,
                        generated_story=story,
                        sdk_response=sdk_result.raw_response,
                        bcp_score=0.0,
                        status="failed",
                        evidence_refs=[
                            MeasurementEvidence(
                                element_id=fp_id,
                                document_id=getattr(
                                    fp.evidence, "document_id", ""
                                ),
                                text=getattr(fp.evidence, "text", ""),
                            )
                        ],
                    )
                )
            else:
                succeeded += 1
                if _sdk_duration is not None:
                    _sdk_duration.record(sdk_result.duration_ms)

                items.append(
                    BCPWorkItem(
                        element_id=fp_id,
                        element_name=fp.name,
                        generated_story=story,
                        sdk_response=sdk_result.raw_response,
                        bcp_score=sdk_result.total_bcp,
                        component_breakdown=sdk_result.breakdown,
                        status="success",
                        evidence_refs=[
                            MeasurementEvidence(
                                element_id=fp_id,
                                document_id=getattr(
                                    fp.evidence, "document_id", ""
                                ),
                                text=getattr(fp.evidence, "text", ""),
                            )
                        ],
                    )
                )

        total_bcp = sum(
            item.bcp_score for item in items if item.status == "success"
        )
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

    def _resolve_provider(self) -> str:
        import os

        return os.environ.get("BCP_PROVIDER", "openai")


class BCPPlugin:
    def plugin_id(self) -> str:
        return "bcp"

    def supported_methodology(self) -> str:
        return "BCP"

    def supported_component_types(self) -> list[str]:
        return ["functional_process"]

    def measure(
        self,
        cfm: CanonicalFunctionalModel | None,
        provider: str | None = None,
    ) -> BCPMeasurementResult:
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

        items: list[BCPWorkItem] = []
        succeeded = 0
        failed = 0
        sdk_call_count = 0
        sdk_errors = 0

        for fp_id, fp in cfm.functional_processes.items():
            story = generate_story(fp, cfm)
            sdk_result = adapter.calculate(story)
            sdk_call_count += 1

            if sdk_result.errors:
                failed += 1
                sdk_errors += len(sdk_result.errors)
                items.append(
                    BCPWorkItem(
                        element_id=fp_id,
                        element_name=fp.name,
                        generated_story=story,
                        sdk_response=sdk_result.raw_response,
                        bcp_score=0.0,
                        status="failed",
                    )
                )
            else:
                succeeded += 1
                items.append(
                    BCPWorkItem(
                        element_id=fp_id,
                        element_name=fp.name,
                        generated_story=story,
                        sdk_response=sdk_result.raw_response,
                        bcp_score=sdk_result.total_bcp,
                        component_breakdown=sdk_result.breakdown,
                        status="success",
                    )
                )

        total_bcp = sum(
            item.bcp_score for item in items if item.status == "success"
        )
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
