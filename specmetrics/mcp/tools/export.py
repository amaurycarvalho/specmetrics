from __future__ import annotations

import json
from pathlib import Path

from mcp.types import TextContent, Tool

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.plugins.exporter.base import ExporterPlugin
from specmetrics.plugins.exporter.orchestrator import ExportOrchestrator

from importlib.metadata import entry_points


EXPORT_RESULTS_TOOL = Tool(
    name="export_results",
    description="Export measurement results in a specified format",
    inputSchema={
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the SpecMetrics project",
            },
            "format": {
                "type": "string",
                "description": "Export format",
                "enum": ["json", "csv", "xml"],
            },
            "output_path": {
                "type": "string",
                "description": "Optional output path for exported files",
            },
        },
        "required": ["project_path", "format"],
    },
)


def handle_export_results(arguments: dict) -> list[TextContent]:
    project_path = Path(arguments["project_path"]).resolve()
    fmt = arguments.get("format", "json")
    output_path_str = arguments.get("output_path")

    orch = PipelineOrchestrator()
    request = PipelineRequest(
        project_path=project_path,
        output_format=OutputFormat.NONE,
    )
    result = orch.execute(request)

    if result.canonical_model is None:
        return [TextContent(type="text", text=json.dumps({"error": "No measurement data available"}))]

    exporters: list[ExporterPlugin] = []
    for ep in entry_points(group="specmetrics.exporters"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                exporters.append(cls())
        except Exception:
            pass

    if not exporters:
        return [TextContent(type="text", text=json.dumps({"error": "No exporter plugins found"}))]

    out_dir = Path(output_path_str) if output_path_str else (project_path / ".specmetrics" / "exports")
    out_dir.mkdir(parents=True, exist_ok=True)

    export_orch = ExportOrchestrator(exporters)
    results = export_orch.export_to_dir(
        cfm=result.canonical_model,
        output_dir=out_dir,
        formats=[fmt],
    )

    response = {
        "export_path": str(out_dir / f"results.{fmt}"),
        "format": fmt,
        "status": "completed",
        "files": results,
    }
    return [TextContent(type="text", text=json.dumps(response, indent=2))]
