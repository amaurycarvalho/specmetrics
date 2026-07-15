from __future__ import annotations

from pathlib import Path

from mcp.types import ResourceTemplate

from specmetrics.mcp.server import ToolError

_project_root: Path | None = None


def set_project_root(path: Path) -> None:
    global _project_root
    _project_root = path.resolve()


SPEC_RESOURCE_TEMPLATE = ResourceTemplate(
    uriTemplate="specmetrics://spec/{path}",
    name="Specification Document",
    description="Access specification document content by path",
    mimeType="text/markdown",
)


def handle_spec_resource(uri: str) -> str:
    path_part = uri.replace("specmetrics://spec/", "", 1)
    resolved = Path(path_part).resolve()

    if _project_root is not None:
        try:
            resolved.relative_to(_project_root)
        except ValueError:
            raise ToolError(-32002, "Path traversal denied: path is outside the project directory")

    if not resolved.exists():
        raise ToolError(-32601, f"Spec file not found: {resolved}")
    if not resolved.is_file():
        raise ToolError(-32601, f"Not a file: {resolved}")

    return resolved.read_text(encoding="utf-8")
