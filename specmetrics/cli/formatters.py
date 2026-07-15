from __future__ import annotations

import json

from specmetrics import __version__
from specmetrics.application.enums import StageExecutionStatus
from specmetrics.application.models import PipelineResult


def format_text_result(result: PipelineResult, verbose: bool = False) -> str:
    lines: list[str] = []
    lines.append(f"SpecMetrics v{__version__} \u2014 Measurement Complete")
    lines.append("\u2500" * 48)
    if result.project_path:
        lines.append(f"Project: {result.project_path}")
    if result.stages_executed:
        stage_count = len(result.stages_executed)
        lines.append(f"Pipeline: {stage_count} stages")
    lines.append(f"Duration: {result.duration_seconds:.1f}s")
    lines.append("")

    if result.measurement:
        m = result.measurement
        lines.append("Results:")
        lines.append(f"  Total Function Points: {m.total_function_points}")
        for ftype, count in sorted(m.breakdown.items()):
            lines.append(f"  \u251c\u2500 {ftype}: {count}")
        lines.append("")

    lines.append("Stages:")
    for sr in result.stages_executed:
        icon = _status_icon(sr.status)
        stage_line = f"  {icon} {sr.stage.value:<12} ({sr.duration_seconds:.1f}s)"
        lines.append(stage_line)
        if verbose and sr.entities_found > 0:
            lines.append(f"       entities: {sr.entities_found}")

    if result.error:
        lines.append("")
        lines.append(f"Error: {result.error}")

    if result.export_path:
        lines.append("")
        lines.append(f"Output: {result.export_path}")

    return "\n".join(lines)


def format_json_result(result: PipelineResult) -> str:
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
        return "\u25B6"
    return "\u25CB"
