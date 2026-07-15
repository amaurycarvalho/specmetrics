from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path

from mcp.types import TextContent, Tool

from specmetrics.application.enums import OutputFormat, StageName
from specmetrics.application.models import PipelineRequest
from specmetrics.application.orchestrator import PipelineOrchestrator
from specmetrics.plugins.exporter.base import ExporterPlugin
from specmetrics.plugins.exporter.orchestrator import ExportOrchestrator

_orchestrator: PipelineOrchestrator | None = None


def get_orchestrator() -> PipelineOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = PipelineOrchestrator()
    return _orchestrator


MEASURE_TOOL = Tool(
    name="measure",
    description="Execute the SpecMetrics measurement pipeline on a project",
    inputSchema={
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the SpecMetrics project",
            },
            "output_format": {
                "type": "string",
                "description": "Export format: json, csv, xml",
                "enum": ["json", "csv", "xml"],
            },
            "from_stage": {
                "type": "string",
                "description": "Start from this stage: discover, extract, graph, cfm, rule, measure, export",
            },
        },
        "required": ["project_path"],
    },
)

PLUGINS_LIST_TOOL = Tool(
    name="plugins_list",
    description="List installed SpecMetrics plugins",
    inputSchema={
        "type": "object",
        "properties": {},
    },
)

VERSION_TOOL = Tool(
    name="specmetrics_version",
    description="Get SpecMetrics platform and plugin version information",
    inputSchema={
        "type": "object",
        "properties": {},
    },
)


def handle_measure_tool(arguments: dict) -> list[TextContent]:
    project_path = Path(arguments["project_path"])
    output_format_str = arguments.get("output_format", "json")
    from_stage_str = arguments.get("from_stage")

    from_stage = None
    if from_stage_str:
        from_stage = StageName(from_stage_str)

    request = PipelineRequest(
        project_path=project_path.resolve(),
        output_format=OutputFormat(output_format_str),
        from_stage=from_stage,
    )

    orch = get_orchestrator()
    result = orch.execute(request)

    result_dict = {
        "status": result.status.value,
        "project_path": str(result.project_path) if result.project_path else None,
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


def handle_plugins_list_tool(arguments: dict) -> list[TextContent]:
    orch = get_orchestrator()
    orch.discover_plugins()
    plugins = orch.list_plugins()

    plugin_list = [
        {
            "name": p.name,
            "version": p.version,
            "type": p.type,
            "enabled": p.enabled,
            "compatible": p.compatible,
        }
        for p in plugins
    ]
    return [TextContent(type="text", text=json.dumps(plugin_list, indent=2))]


def handle_version_tool(arguments: dict) -> list[TextContent]:
    orch = get_orchestrator()
    orch.discover_plugins()
    vi = orch.get_version_info()

    data = {
        "platform_version": vi.platform_version,
        "python_version": vi.python_version,
        "plugins": [
            {
                "name": p.name,
                "version": p.version,
                "type": p.type,
                "enabled": p.enabled,
            }
            for p in vi.plugins
        ],
    }
    return [TextContent(type="text", text=json.dumps(data, indent=2))]


EXPORT_TOOL = Tool(
    name="export",
    description="Export measurement results to a file format",
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
            "output_dir": {
                "type": "string",
                "description": "Output directory for exported files (default: project_path/exports)",
            },
        },
        "required": ["project_path", "format"],
    },
)


def handle_export_tool(arguments: dict) -> list[TextContent]:
    project_path = Path(arguments["project_path"])
    fmt = arguments.get("format", "json")
    output_dir_str = arguments.get("output_dir")

    from specmetrics.application.orchestrator import PipelineOrchestrator

    orch = PipelineOrchestrator()
    request = PipelineRequest(
        project_path=project_path.resolve(),
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

    out_dir = Path(output_dir_str) if output_dir_str else (project_path / "exports")
    out_dir.mkdir(parents=True, exist_ok=True)

    export_orch = ExportOrchestrator(exporters)
    results = export_orch.export_to_dir(
        cfm=result.canonical_model,
        output_dir=out_dir,
        formats=[fmt],
    )
    return [TextContent(type="text", text=json.dumps(results, indent=2))]


TOOL_HANDLERS = {
    "measure": handle_measure_tool,
    "plugins_list": handle_plugins_list_tool,
    "specmetrics_version": handle_version_tool,
    "export": handle_export_tool,
}
