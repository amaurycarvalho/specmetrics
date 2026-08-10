"""Orchestrates the pipeline by publishing events in canonical order."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Self

import structlog

from .diagnostics import (
    Diagnostics,
    StageStatus,
    StageTiming,
)
from .diagnostics import (
    StageError as StageErrorRecord,
)
from .event_bus import EventBus
from .events import EventType, PipelineEvent
from .exceptions import HandlerNotFoundError, PipelineError, StageError
from .handler_registry import HandlerRegistry
from .pipeline_context import PipelineContext
from .validation.pipeline import ValidationPipeline

logger = structlog.get_logger(__name__)


def _collect_spec_docs(docs_data: object) -> list[Path]:
    raw_docs = (docs_data or {}).get("documents", [])
    doc_paths: list[Path] = []
    for d in raw_docs:
        p = d.get("path") if isinstance(d, dict) else getattr(d, "path", None)
        if p:
            doc_paths.append(Path(p))
    return [p for p in doc_paths if p.name == "spec.md"]


def _mark_timing(timing: StageTiming, status: StageStatus) -> None:
    timing.status = status
    timing.completed_at = datetime.now(UTC)
    if timing.started_at:
        timing.duration_ms = int(
            (timing.completed_at - timing.started_at).total_seconds() * 1000
        )


def _finish_diagnostics(diagnostics: Diagnostics) -> None:
    diagnostics.completed_at = datetime.now(UTC)
    if diagnostics.started_at:
        diagnostics.total_duration_ms = int(
            (
                diagnostics.completed_at - diagnostics.started_at
            ).total_seconds()
            * 1000
        )


def _finalize_run(ctx: PipelineContext, diagnostics: Diagnostics) -> PipelineContext:
    completed_event = PipelineEvent(
        event_type=EventType.PIPELINE_COMPLETED,
        publisher="pipeline_engine",
        payload={},
        context=ctx,
    )
    ctx = ctx.with_stage_output(
        "published_events", ctx.published_events + (completed_event,)
    )
    _finish_diagnostics(diagnostics)
    logger.info(
        "pipeline_completed",
        execution_id=str(ctx.execution_id),
        duration_ms=diagnostics.total_duration_ms,
    )
    return ctx


CANONICAL_EVENT_ORDER: list[EventType] = [
    EventType.REPOSITORY_LOADED,
    EventType.DOCUMENTS_DISCOVERED,
    EventType.DOCUMENTS_VALIDATED,
    EventType.SEMANTIC_EXTRACTION_COMPLETED,
    EventType.EVIDENCE_GRAPH_BUILT,
    EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,
    EventType.CANONICAL_MODEL_BUILT,
    EventType.RULE_PACK_APPLIED,
    EventType.MEASUREMENT_COMPLETED,
    EventType.TSHIRT_CLASSIFICATION_COMPLETED,
    EventType.EXPORT_COMPLETED,
    EventType.TELEMETRY_PUBLISHED,
]


class PipelineEngine:
    """Runs registered pipeline stages in canonical event order."""

    def __init__(
        self: Self,
        registry: HandlerRegistry,
        validation_pipeline: ValidationPipeline | None = None,
    ) -> None:
        """Initialize the pipeline engine with a handler registry."""
        self._registry = registry
        self._bus = EventBus(registry)
        self._validation_pipeline = validation_pipeline or ValidationPipeline()

    def run(self: Self, context: PipelineContext) -> PipelineContext:
        """Run the pipeline over the given context and return the result."""
        if not self._registry.registered_types:
            raise PipelineError(
                "No plugins installed: no handlers registered for any event type. "
                "Install at least one plugin before running the pipeline."
            )

        started_at = datetime.now(UTC)
        diagnostics = Diagnostics(started_at=started_at)
        ctx = self._build_context(context, diagnostics)
        logger.info("pipeline_started", execution_id=str(ctx.execution_id))

        for event_type in CANONICAL_EVENT_ORDER:
            if event_type not in self._registry.registered_types:
                logger.debug("stage_skipped", event_type=event_type.value)
                continue

            stage_name = self._resolve_stage_name(event_type)
            timing = StageTiming(
                stage_name=stage_name,
                status=StageStatus.RUNNING,
                started_at=datetime.now(UTC),
            )
            diagnostics.stage_timings[stage_name] = timing

            event = PipelineEvent(
                event_type=event_type,
                publisher="pipeline_engine"
                if event_type
                in (EventType.REPOSITORY_LOADED, EventType.PIPELINE_COMPLETED)
                else stage_name,
                payload={},
                context=ctx,
            )

            self._run_document_validation(event_type, ctx)

            try:
                next_ctx = self._bus.publish(event)
                ctx = next_ctx.with_stage_output(
                    "published_events", next_ctx.published_events + (event,)
                )
                _mark_timing(timing, StageStatus.COMPLETED)
            except (HandlerNotFoundError, StageError) as exc:
                return self._fail_stage(ctx, stage_name, timing, exc, diagnostics)

        return _finalize_run(ctx, diagnostics)

    def _build_context(
        self: Self, context: PipelineContext, diagnostics: Diagnostics
    ) -> PipelineContext:
        return PipelineContext(
            execution_id=context.execution_id,
            diagnostics=diagnostics,
            metadata=context.metadata,
            repository=context.repository,
            adapter_result=context.adapter_result,
            extraction_result=context.extraction_result,
            evidence_graph=context.evidence_graph,
            canonical_model=context.canonical_model,
            measurement_result=context.measurement_result,
            exported_files=context.exported_files,
        )

    def _run_document_validation(
        self: Self, event_type: EventType, ctx: PipelineContext
    ) -> None:
        if (
            event_type != EventType.DOCUMENTS_VALIDATED
            or self._validation_pipeline is None
        ):
            return
        doc_paths = _collect_spec_docs(getattr(ctx, "adapter_result", None))
        if not doc_paths:
            return
        report = self._validation_pipeline.run_batch(doc_paths)
        if report.failed_documents > 0:
            logger.debug(
                "document_validation_failed",
                execution_id=str(ctx.execution_id),
                failed_documents=report.failed_documents,
                total=report.total_documents,
            )

    def _fail_stage(
        self: Self,
        ctx: PipelineContext,
        stage_name: str,
        timing: StageTiming,
        exc: Exception,
        diagnostics: Diagnostics,
    ) -> PipelineContext:
        _mark_timing(timing, StageStatus.FAILED)
        diagnostics.errors.append(
            StageErrorRecord(
                stage_name=stage_name,
                message=exc.message if hasattr(exc, "message") else str(exc),
                exception_type=type(exc).__name__,
                timestamp=datetime.now(UTC),
            )
        )
        _finish_diagnostics(diagnostics)
        failed_event = PipelineEvent(
            event_type=EventType.PIPELINE_FAILED,
            publisher="pipeline_engine",
            payload={"failed_stage": stage_name, "error_message": str(exc)},
            context=ctx,
        )
        ctx = ctx.with_stage_output(
            "published_events", ctx.published_events + (failed_event,)
        )
        logger.error(
            "pipeline_failed",
            execution_id=str(ctx.execution_id),
            failed_stage=stage_name,
            error=str(exc),
        )
        return ctx

    def _resolve_stage_name(self: Self, event_type: EventType) -> str:
        try:
            handler = self._registry.resolve(event_type)
            return handler.stage_name
        except Exception:
            return event_type.value
