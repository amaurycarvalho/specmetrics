"""MCP tool handler for running the measurement pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.types import TextContent, Tool

from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator

_orchestrator: PipelineOrchestrator | None = None


def get_orchestrator() -> PipelineOrchestrator:
    """Return the shared pipeline orchestrator, creating it on first use."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator


RUN_PIPELINE_TOOL = Tool(
    name="run_pipeline",
    description="Execute the SpecMetrics measurement pipeline on a project",
    inputSchema={
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the SpecMetrics project directory",
            },
            "stage": {
                "type": "string",
                "description": "Pipeline stage to execute",
                "enum": ["full", "extract", "cfm", "measure", "export"],
            },
            "export_format": {
                "type": "string",
                "description": "Export format for results",
                "enum": ["json", "csv"],
            },
        },
        "required": ["project_path"],
    },
)


def handle_run_pipeline(arguments: dict) -> list[TextContent]:
    """Run the measurement pipeline and return the result as text content."""
    project_path = Path(arguments["project_path"])
    stage_str = arguments.get("stage", "full")
    export_format_str = arguments.get("export_format", "json")

    stage = None
    if stage_str != "full":
        stage = StageName(stage_str)

    request = PipelineRequest(
        project_path=project_path.resolve(),
        output_format=OutputFormat(export_format_str),
        from_stage=stage,
    )

    orch = get_orchestrator()
    result = orch.execute(request)

    result_dict = {
        "status": result.status.value,
        "project_path": str(result.project_path) if result.project_path else None,
        "run_id": result.run_id,
        "stages_executed": [
            {
                "stage": sr.stage.value,
                "status": sr.status.value,
                "duration_seconds": sr.duration_seconds,
            }
            for sr in result.stages_executed
        ],
        "duration_seconds": result.duration_seconds,
        "error": result.error or None,
    }
    if result.measurement:
        m = result.measurement
        result_dict["measurement"] = {
            "total_function_points": m.total_function_points,
            "breakdown": m.breakdown,
            "complexity_distribution": m.complexity_distribution,
            "evidence_refs": m.evidence_refs,
            "applied_rule_pack": m.applied_rule_pack,
        }

    return [TextContent(type="text", text=json.dumps(result_dict, indent=2))]
