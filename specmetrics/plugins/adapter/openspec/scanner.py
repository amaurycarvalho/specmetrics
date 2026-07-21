from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

TEMP_EXCLUSIONS = frozenset(
    {
        ".git",
        "__pycache__",
        ".venv",
        "node_modules",
        ".specify",
    }
)


def _is_temp_dir(name: str) -> bool:
    return name in TEMP_EXCLUSIONS or name.startswith("_")


def scan_specs(repository_path: Path) -> list[Path]:
    openspec_specs = repository_path / "openspec" / "specs"
    if not openspec_specs.is_dir():
        return []
    return sorted(openspec_specs.rglob("spec.md"))


def _discover_change_artifacts(change_dir: Path) -> list[Path]:
    artifacts: list[Path] = []
    recognized = {"proposal.md", "design.md", "tasks.md"}
    for name in recognized:
        candidate = change_dir / name
        if candidate.is_file():
            artifacts.append(candidate)
    delta_specs = sorted(change_dir.rglob("spec.md"))
    artifacts.extend(delta_specs)
    return artifacts


def _list_change_dirs(changes_root: Path) -> list[Path]:
    if not changes_root.is_dir():
        return []
    result: list[Path] = []
    for p in sorted(changes_root.iterdir()):
        if _is_temp_dir(p.name):
            continue
        if p.is_dir():
            result.append(p)
        elif p.is_symlink():
            logger.warning("openspec_broken_symlink", path=str(p))
    return result


def scan_changes(
    repository_path: Path,
) -> list[tuple[Path, str, bool]]:
    changes_root = repository_path / "openspec" / "changes"
    results: list[tuple[Path, str, bool]] = []

    for change_dir in _list_change_dirs(changes_root):
        if change_dir.name == "archive":
            continue
        artifacts = _discover_change_artifacts(change_dir)
        for ap in artifacts:
            results.append((ap, change_dir.name, False))

    archive_root = changes_root / "archive"
    for archived_dir in _list_change_dirs(archive_root):
        artifacts = _discover_change_artifacts(archived_dir)
        for ap in artifacts:
            results.append((ap, archived_dir.name, True))

    return results
