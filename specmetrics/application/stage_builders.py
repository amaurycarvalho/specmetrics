"""Stage result and stage-detail row assembly for pipeline outputs.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). Produces ``StageResult`` and
``StageOutputItem`` rows from the kernel diagnostics for each executed stage.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from specmetrics.application.enums import (
    StageExecutionStatus,
    StageName,
)
from specmetrics.application.models import (
    METRIC_NAME_MAP,
    StageOutputItem,
    StageResult,
)
from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.diagnostics import StageStatus as KernelStageStatus
from specmetrics.kernel.diagnostics import StageTiming
from specmetrics.kernel.events import EventType
from specmetrics.kernel.pipeline_context import PipelineContext

from .stage_mapping import (
    _STAGE_NAME_TO_HANDLER_NAMES,
    _stage_name_from_event,
)


def _build_stage_results(
    ctx: PipelineContext,
    event_order: list[EventType],
    metrics_filter: list[str] | None = None,
    on_discover: Callable[[PipelineContext], None] | None = None,
) -> list[StageResult]:
    if not ctx.diagnostics:
        return []

    results: list[StageResult] = []
    valid_stage_names = {s.value for s in StageName}

    for event_type in event_order:
        stage_name = _stage_name_from_event(event_type)
        if stage_name not in valid_stage_names:
            continue

        timing = _stage_timing(ctx, stage_name)

        if timing is None:
            results.append(
                StageResult(
                    stage=StageName(stage_name),
                    status=StageExecutionStatus.SKIPPED,
                )
            )
            continue

        status = _status_for_kernel(timing.status)
        duration_s = _duration_seconds(timing)

        if stage_name == "discover" and on_discover is not None:
            on_discover(ctx)
        entities_found = _entities_for_stage(ctx, stage_name, metrics_filter)

        results.append(
            StageResult(
                stage=StageName(stage_name),
                status=status,
                duration_seconds=duration_s,
                entities_found=entities_found,
            )
        )
    return results


def _stage_timing(
    ctx: PipelineContext, stage_name: str
) -> StageTiming | None:
    timing = ctx.diagnostics.stage_timings.get(stage_name)
    if timing is not None:
        return timing
    for alt_name in _STAGE_NAME_TO_HANDLER_NAMES.get(stage_name, []):
        timing = ctx.diagnostics.stage_timings.get(alt_name)
        if timing is not None:
            return timing
    return None


def _status_for_kernel(
    kernel_status: KernelStageStatus,
) -> StageExecutionStatus:
    if kernel_status == KernelStageStatus.COMPLETED:
        return StageExecutionStatus.COMPLETED
    if kernel_status == KernelStageStatus.FAILED:
        return StageExecutionStatus.FAILED
    if kernel_status == KernelStageStatus.RUNNING:
        return StageExecutionStatus.RUNNING
    return StageExecutionStatus.PENDING


def _duration_seconds(timing: StageTiming) -> float:
    if timing.duration_ms is None:
        return 0.0
    return timing.duration_ms / 1000.0


def _entities_for_stage(
    ctx: PipelineContext,
    stage_name: str,
    metrics_filter: list[str] | None,
) -> int:
    counters: dict[str, Callable[[], int]] = {
        "discover": lambda: _count_discover(ctx),
        "extract": lambda: _count_extract(ctx),
        "graph": lambda: _count_graph(ctx),
        "csm": lambda: _count_model_elements(ctx, stage_name),
        "cfm": lambda: _count_model_elements(ctx, stage_name),
        "rule": lambda: _count_model_elements(ctx, stage_name),
        "measure": lambda: len(metrics_filter)
        if metrics_filter
        else len(METRIC_NAME_MAP),
    }
    counter = counters.get(stage_name)
    return counter() if counter else 0


def _count_discover(ctx: PipelineContext) -> int:
    adapter_data = getattr(ctx, "adapter_result", None) or {}
    return len(adapter_data.get("documents", []))


def _count_extract(ctx: PipelineContext) -> int:
    extract_data = getattr(ctx, "extraction_result", None) or {}
    return extract_data.get("total_elements", 0)


def _count_graph(ctx: PipelineContext) -> int:
    graph_data = getattr(ctx, "evidence_graph", None) or {}
    if isinstance(graph_data, dict):
        return graph_data.get("node_count", 0)
    return 0


def _count_model_elements(
    ctx: PipelineContext, stage_name: str
) -> int:
    if stage_name == "csm":
        csm = getattr(ctx, "canonical_spec_model", None)
        if isinstance(csm, CanonicalSpecificationModel):
            return sum(csm.metadata.element_counts.values())
        return 0
    cfm = getattr(ctx, "canonical_model", None)
    if isinstance(cfm, CanonicalFunctionalModel):
        return sum(cfm.metadata.element_counts.values())
    return 0


def _build_stage_details(
    ctx: PipelineContext,
    event_order: list[EventType],
    metrics_filter: list[str] | None = None,
    export_path: Path | None = None,
) -> list[StageOutputItem]:
    if not ctx.diagnostics:
        return []

    details: list[StageOutputItem] = []
    valid_stage_names = {s.value for s in StageName}

    for event_type in event_order:
        stage_name = _stage_name_from_event(event_type)
        if stage_name not in valid_stage_names:
            continue

        timing = _stage_timing(ctx, stage_name)
        duration_ms = (
            timing.duration_ms if timing and timing.duration_ms is not None else 0
        )

        count, count_type = _detail_count(
            ctx, stage_name, metrics_filter, export_path
        )

        details.append(
            StageOutputItem(
                name=stage_name,
                count=count,
                count_type=count_type,
                duration_ms=duration_ms,
            )
        )

    return details


def _detail_count(
    ctx: PipelineContext,
    stage_name: str,
    metrics_filter: list[str] | None,
    export_path: Path | None,
) -> tuple[int, str]:
    counts: dict[str, Callable[[], tuple[int, str]]] = {
        "discover": lambda: (_count_discover(ctx), "documents"),
        "extract": lambda: (_count_extract(ctx), "items"),
        "graph": lambda: (_count_graph(ctx), "items"),
        "csm": lambda: (_count_model_elements(ctx, stage_name), "items"),
        "cfm": lambda: (_count_model_elements(ctx, stage_name), "items"),
        "rule": lambda: (_count_model_elements(ctx, stage_name), "items"),
        "measure": lambda: _count_measure(ctx, metrics_filter),
        "export": lambda: (1 if export_path else 0, "files"),
    }
    counter = counts.get(stage_name)
    return counter() if counter else (0, "items")


def _count_measure(
    ctx: PipelineContext, metrics_filter: list[str] | None
) -> tuple[int, str]:
    mr = getattr(ctx, "measurement_result", None) or {}
    if not isinstance(mr, dict):
        return 0, "metrics"
    count = len(metrics_filter) if metrics_filter else len(METRIC_NAME_MAP)
    return count, "metrics"