"""Metric and measurement result assembly for pipeline outputs.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). Produces the per-metric output
items and the primary measurement summary from the kernel measurement result.
"""

from __future__ import annotations

from specmetrics.application.models import (
    METRIC_NAME_MAP,
    MeasurementResult,
    MetricOutputItem,
)
from specmetrics.kernel.pipeline_context import PipelineContext

_KEY_MAP = {
    "bcp": "bcp_measured_items",
    "fpa": "fpa_total_function_points",
    "sfp": "sfp_total_sfp",
    "snap": "snap_total_snap",
    "sp": "storypoints_total_story_points",
    "tshirt": "tshirt",
    "tp": "token_total_score",
    "cp": "cognitive_raw_score",
}


def _build_metric_results(
    ctx: PipelineContext,
    metrics_filter: list[str] | None,
) -> list[MetricOutputItem]:
    mr = ctx.measurement_result
    if not isinstance(mr, dict):
        return []

    metric_ids = metrics_filter or list(METRIC_NAME_MAP.keys())
    results: list[MetricOutputItem] = []

    for mid in metric_ids:
        json_name = METRIC_NAME_MAP.get(mid, mid)
        total_key = _KEY_MAP.get(mid)
        total = mr.get(total_key, 0) if total_key else 0

        results.append(
            MetricOutputItem(
                name=json_name,
                total=total,
                status="completed",
                duration_ms=0,
            )
        )

    return results


def _extract_measurement(ctx: PipelineContext) -> MeasurementResult | None:
    if ctx.measurement_result is None:
        return None

    mr = ctx.measurement_result
    if isinstance(mr, dict):
        return MeasurementResult(
            total_function_points=mr.get("fpa_total_function_points", 0),
            breakdown=mr.get("fpa_breakdown", {}),
            complexity_distribution=mr.get("fpa_complexity_distribution", []),
            evidence_refs=mr.get("evidence_refs", []),
            applied_rule_pack=mr.get("storypoints_applied_rule_pack", ""),
        )
    return MeasurementResult()