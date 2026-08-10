"""Per-metric breakdown rendering helpers for CLI output."""

from __future__ import annotations

from specmetrics.application.models import MetricOutputItem, PipelineResult


def metric_breakdown_lines(
    result: PipelineResult, mr: MetricOutputItem
) -> list[str]:
    """Return the detail lines to print beneath a metric result."""
    if mr.name == "cognitive_points":
        return cognitive_bloom_lines(result)
    if mr.name == "tshirt":
        return tshirt_lines(result)
    if mr.name == "function_points":
        return function_points_lines(result)
    return []


def cognitive_bloom_lines(result: PipelineResult) -> list[str]:
    """Render the cognitive bloom breakdown as indented lines."""
    if not result.measurement_result_raw:
        return []
    breakdown = result.measurement_result_raw.get("cognitive_bloom_breakdown")
    if not isinstance(breakdown, dict) or not breakdown:
        return []
    return [
        f"    {level_name.title()}: {breakdown_total(level_data):.1f}"
        for level_name, level_data in breakdown.items()
    ]


def tshirt_lines(result: PipelineResult) -> list[str]:
    """Render the t-shirt size breakdown as an indented line."""
    if not result.measurement_result_raw:
        return []
    breakdown = result.measurement_result_raw.get("tshirt_breakdown")
    if not isinstance(breakdown, dict):
        return []
    parts = [
        f"{size}: {info.get('count', info)}"
        for size, info in sorted(breakdown.items())
    ]
    return [f"    {'  '.join(parts)}"] if parts else []


def function_points_lines(result: PipelineResult) -> list[str]:
    """Render the function-points breakdown as indented lines."""
    if not result.measurement or not result.measurement.breakdown:
        return []
    lines: list[str] = []
    for ftype, info in sorted(result.measurement.breakdown.items()):
        if isinstance(info, dict):
            count = info.get("count", 0)
            subtot = info.get("total_ufp", 0)
        else:
            count = info
            subtot = info
        lines.append(f"    \u251c\u2500 {ftype}: count={count}, subtot={subtot}")
    return lines


def breakdown_total(level_data: object) -> float:
    """Return the numeric total stored in a breakdown entry."""
    if isinstance(level_data, dict):
        return level_data.get("total", 0)
    return float(level_data)
