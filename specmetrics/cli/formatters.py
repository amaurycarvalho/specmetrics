from __future__ import annotations

import json

from specmetrics import __version__
from specmetrics.application.enums import StageExecutionStatus
from specmetrics.application.models import PipelineResult

from specmetrics.application.models import JSON_NAME_TO_DISPLAY_MAP


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

    if result.metric_results:
        lines.append("Results:")
        for mr in result.metric_results:
            display_name = JSON_NAME_TO_DISPLAY_MAP.get(mr.name, mr.name)
            status_tag = ""
            if mr.status == "skipped":
                status_tag = " (skipped)"
            elif mr.status == "failed":
                status_tag = " (failed)"
            if mr.name == "tshirt":
                lines.append(f"  {display_name}: {mr.total} entities{status_tag}")
            else:
                extra_tag = ""
                if mr.name == "business_complexity_points" and result.measurement_result_raw:
                    bcp_warnings = result.measurement_result_raw.get("bcp_warnings", [])
                    if bcp_warnings:
                        extra_tag = " (SDK is missing)"
                if mr.name in ("cognitive_points", "token_points"):
                    lines.append(f"  {display_name}: {mr.total:.1f}{status_tag}{extra_tag}")
                else:
                    lines.append(f"  {display_name}: {mr.total}{status_tag}{extra_tag}")

            if mr.name == "cognitive_points" and result.measurement_result_raw:
                cp_breakdown = result.measurement_result_raw.get("cognitive_bloom_breakdown")
                if isinstance(cp_breakdown, dict) and cp_breakdown:
                    for level_name, level_data in cp_breakdown.items():
                        if isinstance(level_data, dict):
                            total = level_data.get("total", 0)
                        else:
                            total = level_data
                        lines.append(f"    {level_name.title()}: {total:.1f}")

            if mr.name == "tshirt" and result.measurement_result_raw:
                tshirt_breakdown = result.measurement_result_raw.get("tshirt_breakdown")
                if isinstance(tshirt_breakdown, dict):
                    parts = [
                        f"{size}: {info.get('count', info)}"
                        for size, info in sorted(tshirt_breakdown.items())
                    ]
                    if parts:
                        lines.append(f"    {'  '.join(parts)}")

            if (
                mr.name == "function_points"
                and result.measurement
                and result.measurement.breakdown
            ):
                for ftype, info in sorted(result.measurement.breakdown.items()):
                    if isinstance(info, dict):
                        count = info.get("count", 0)
                        subtot = info.get("total_ufp", 0)
                    else:
                        count = info
                        subtot = info
                    lines.append(
                        f"    \u251c\u2500 {ftype}: count={count}, subtot={subtot}"
                    )
        lines.append("")
    elif result.measurement:
        m = result.measurement
        lines.append("Results:")
        lines.append(f"  Total Function Points: {m.total_function_points}")
        for ftype, count in sorted(m.breakdown.items()):
            lines.append(f"  \u251c\u2500 {ftype}: {count}")
        lines.append("")

    lines.append("Stages:")
    for sr in result.stages_executed:
        icon = _status_icon(sr.status)
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
        stage_line = (
            f"  {icon} {sr.stage.value:<12} ({sr.duration_seconds:.1f}s){extra}"
        )
        lines.append(stage_line)

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
        return "\u25b6"
    return "\u25cb"
