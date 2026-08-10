"""Output formatting for measurement results."""

from __future__ import annotations

import json

from specmetrics import __version__
from specmetrics.application.enums import StageExecutionStatus
from specmetrics.application.models import (
    JSON_NAME_TO_DISPLAY_MAP,
    MetricOutputItem,
    PipelineResult,
    StageResult,
)

from ._breakdowns import (
    metric_breakdown_lines,
)


def format_text_result(result: PipelineResult, verbose: bool = False) -> str:
    """Render a pipeline result as human-readable text."""
    lines: list[str] = _header_lines(result)
    lines.extend(_results_lines(result))

    if result.error:
        lines.append("")
        lines.append(f"Error: {result.error}")

    if result.export_path:
        lines.append("")
        lines.append(f"Output: {result.export_path}")

    return "\n".join(lines)


def _header_lines(result: PipelineResult) -> list[str]:
    lines: list[str] = []
    lines.append(f"SpecMetrics v{__version__} \u2014 Measurement Complete")
    lines.append("\u2500" * 48)
    if result.project_path:
        lines.append(f"Project: {result.project_path}")
    if result.stages_executed:
        lines.append(f"Pipeline: {len(result.stages_executed)} stages")
    lines.append(f"Duration: {result.duration_seconds:.1f}s")
    lines.append("")
    return lines


def _results_lines(result: PipelineResult) -> list[str]:
    lines: list[str] = []
    if result.metric_results:
        lines.append("Results:")
        for mr in result.metric_results:
            lines.append(_metric_header_line(result, mr))
            lines.extend(_metric_breakdown_lines(result, mr))
        lines.append("")
    elif result.measurement:
        lines.append("Results:")
        lines.append(f"  Total Function Points: {result.measurement.total_function_points}")
        for ftype, count in sorted(result.measurement.breakdown.items()):
            lines.append(f"  \u251c\u2500 {ftype}: {count}")
        lines.append("")

    lines.append("Stages:")
    for sr in result.stages_executed:
        lines.append(_stage_line(result, sr))
    return lines


def _stage_line(result: PipelineResult, sr: StageResult) -> str:
    extra = ""
    if sr.stage.value == "discover":
        framework = getattr(result, "_framework_detected", None)
        if framework:
            extra = f" [{framework}]"
        if sr.entities_found > 0:
            extra += f" ({sr.entities_found} documents)"
    elif sr.entities_found > 0:
        label = "metrics" if sr.stage.value == "measure" else "items"
        extra = f" ({sr.entities_found} {label})"
    return f"  {_status_icon(sr.status)} {sr.stage.value:<12} ({sr.duration_seconds:.1f}s){extra}"


def _metric_header_line(result: PipelineResult, mr: MetricOutputItem) -> str:
    display_name = JSON_NAME_TO_DISPLAY_MAP.get(mr.name, mr.name)
    status_tag = ""
    if mr.status == "skipped":
        status_tag = " (skipped)"
    elif mr.status == "failed":
        status_tag = " (failed)"
    if mr.name == "tshirt":
        return f"  {display_name}: {mr.total} entities{status_tag}"
    extra_tag = ""
    if mr.name == "business_complexity_points" and result.measurement_result_raw:
        bcp_warnings = result.measurement_result_raw.get("bcp_warnings", [])
        if bcp_warnings:
            extra_tag = " (SDK is missing)"
    if mr.name in ("cognitive_points", "token_points"):
        return f"  {display_name}: {mr.total:.1f}{status_tag}{extra_tag}"
    return f"  {display_name}: {mr.total}{status_tag}{extra_tag}"


def _metric_breakdown_lines(
    result: PipelineResult, mr: MetricOutputItem
) -> list[str]:
    return metric_breakdown_lines(result, mr)


def format_json_result(result: PipelineResult) -> str:
    """Render a pipeline result as a JSON string."""
    data = {
        "status": result.status.value,
        "project_path": str(result.project_path) if result.project_path else None,
        "duration_seconds": result.duration_seconds,
        "stages": [
            {
                "stage": sr.stage.value,
                "status": sr.status.value,
                "duration_seconds": sr.duration_seconds,
                "entities_found": sr.entities_found,
            }
            for sr in result.stages_executed
        ],
        "measurement": (
            {
                "total_function_points": result.measurement.total_function_points,
                "breakdown": result.measurement.breakdown,
                "complexity_distribution": result.measurement.complexity_distribution,
                "evidence_refs": result.measurement.evidence_refs,
                "applied_rule_pack": result.measurement.applied_rule_pack,
            }
            if result.measurement
            else None
        ),
        "error": result.error or None,
        "export_path": str(result.export_path) if result.export_path else None,
    }
    return json.dumps(data, indent=2)


def format_progress(stage_name: str, status: StageExecutionStatus) -> str:
    """Render a one-line progress indicator for a stage."""
    icon = _status_icon(status)
    return f"{icon} {stage_name}"


def _status_icon(status: StageExecutionStatus) -> str:
    if status == StageExecutionStatus.COMPLETED:
        return "\u2713"
    if status == StageExecutionStatus.FAILED:
        return "\u2717"
    if status == StageExecutionStatus.SKIPPED:
        return "\u2014"
    if status == StageExecutionStatus.RUNNING:
        return "\u25b6"
    return "\u25cb"