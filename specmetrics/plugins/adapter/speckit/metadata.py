from __future__ import annotations

from pathlib import Path
from typing import Any

ARTIFACT_TYPE_MAP: dict[str, str] = {
    "constitution.md": "constitution",
    "spec.md": "specification",
    "plan.md": "plan",
    "tasks.md": "tasks",
    "research.md": "research",
    "data-model.md": "data-model",
}

KIND_MAP: dict[str, str] = {
    "constitution": "governance",
    "specification": "specification",
    "plan": "architecture",
    "tasks": "implementation",
    "research": "research",
    "data-model": "data-model",
    "checklist": "checklist",
    "unknown": "unknown",
}

FRAMEWORK = "speckit"


def _infer_artifact_type(file_path: Path) -> str:
    name = file_path.name
    if "checklists" in file_path.parts:
        return "checklist"
    return ARTIFACT_TYPE_MAP.get(name, "unknown")


def _infer_kind(artifact_type: str) -> str:
    return KIND_MAP.get(artifact_type, "unknown")


def _infer_feature(file_path: Path, repo_root: Path) -> str | None:
    try:
        relative = file_path.relative_to(repo_root)
    except ValueError:
        relative = file_path
    parts = relative.parts

    if len(parts) >= 2 and parts[0] == ".specify":
        return None

    if len(parts) >= 2 and parts[0] == "specs":
        return parts[1]

    return None


def _infer_workspace(file_path: Path, repo_root: Path) -> str:
    try:
        relative = file_path.relative_to(repo_root)
    except ValueError:
        relative = file_path
    parts = relative.parts

    if len(parts) >= 2 and parts[0] == ".specify":
        return ".specify/memory"

    if len(parts) >= 3 and parts[0] == "specs":
        return f"specs/{parts[1]}"

    return ""


def build_metadata(file_path: Path, repo_root: Path) -> dict[str, Any]:
    artifact_type = _infer_artifact_type(file_path)
    kind = _infer_kind(artifact_type)
    feature = _infer_feature(file_path, repo_root)
    workspace = _infer_workspace(file_path, repo_root)

    try:
        relative_path = str(file_path.relative_to(repo_root))
    except ValueError:
        relative_path = str(file_path)

    return {
        "framework": FRAMEWORK,
        "artifact_type": artifact_type,
        "kind": kind,
        "feature": feature,
        "workspace": workspace,
        "relative_path": relative_path,
    }
