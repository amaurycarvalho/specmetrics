"""Metadata inference for OpenSpec specification artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

ARTIFACT_TYPE_MAP: dict[str, str] = {
    "spec.md": "specification",
    "proposal.md": "proposal",
    "design.md": "design",
    "tasks.md": "tasks",
}

KIND_MAP: dict[str, str] = {
    "specification": "current-spec",
    "proposal": "proposal",
    "design": "design",
    "tasks": "tasks",
}

FRAMEWORK = "openspec"


def _infer_kind(file_path: Path, artifact_type: str) -> str:
    if artifact_type == "specification":
        parts = file_path.parts
        if "changes" in parts:
            return "delta-spec"
        return "current-spec"
    return KIND_MAP.get(artifact_type, "unknown")


def _infer_domain(file_path: Path) -> str | None:
    parts = file_path.parts
    try:
        idx = parts.index("specs")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return None


def _infer_change(file_path: Path) -> str | None:
    parts = file_path.parts
    try:
        idx = parts.index("changes")
        if idx + 1 < len(parts) and parts[idx + 1] != "archive":
            return parts[idx + 1]
        if idx + 2 < len(parts) and parts[idx + 1] == "archive":
            return parts[idx + 2]
    except ValueError:
        pass
    return None


def _infer_status(file_path: Path) -> str:
    parts = file_path.parts
    if "archive" in parts:
        return "archived"
    return "active"


def build_metadata(file_path: Path, repo_root: Path) -> dict[str, Any]:
    """Build metadata describing the given OpenSpec artifact file."""
    artifact_type = ARTIFACT_TYPE_MAP.get(file_path.name, "unknown")
    kind = _infer_kind(file_path, artifact_type)
    domain = _infer_domain(file_path)
    change = _infer_change(file_path)
    status = _infer_status(file_path)

    try:
        relative_path = str(file_path.relative_to(repo_root))
    except ValueError:
        relative_path = str(file_path)

    return {
        "framework": FRAMEWORK,
        "repository_root": str(repo_root.resolve()),
        "artifact_type": artifact_type,
        "kind": kind,
        "domain": domain,
        "change": change,
        "status": status,
        "relative_path": relative_path,
    }
