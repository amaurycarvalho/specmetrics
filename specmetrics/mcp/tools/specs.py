from __future__ import annotations

import json
from pathlib import Path

from mcp.types import TextContent, Tool


def _discover_specs(project_path: Path) -> list[dict]:
    specs_dir = project_path / "specs"
    if not specs_dir.exists():
        return []

    results = []
    for item in sorted(specs_dir.iterdir()):
        spec_file = item / "spec.md"
        if spec_file.exists():
            stat = spec_file.stat()
            results.append({
                "name": item.name,
                "path": str(spec_file),
                "type": "specification",
                "last_modified": stat.st_mtime,
            })
    return results


LIST_SPECS_TOOL = Tool(
    name="list_specs",
    description="List specification documents in a project",
    inputSchema={
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the SpecMetrics project directory",
            },
        },
        "required": ["project_path"],
    },
)


def handle_list_specs(arguments: dict) -> list[TextContent]:
    project_path = Path(arguments["project_path"]).resolve()
    specs = _discover_specs(project_path)
    return [TextContent(type="text", text=json.dumps(specs, indent=2))]


READ_SPEC_TOOL = Tool(
    name="read_spec",
    description="Read the content of a specification document",
    inputSchema={
        "type": "object",
        "properties": {
            "spec_path": {
                "type": "string",
                "description": "Path to the specification file",
            },
        },
        "required": ["spec_path"],
    },
)


def handle_read_spec(arguments: dict) -> list[TextContent]:
    spec_path = Path(arguments["spec_path"]).resolve()
    if not spec_path.exists():
        raise ValueError(f"Spec file not found: {spec_path}")
    content = spec_path.read_text(encoding="utf-8")
    return [TextContent(type="text", text=content)]
