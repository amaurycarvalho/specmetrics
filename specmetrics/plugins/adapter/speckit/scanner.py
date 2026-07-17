from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def scan_memory(repository_path: Path) -> list[Path]:
    memory_dir = repository_path / ".specify" / "memory"
    if not memory_dir.is_dir():
        return []
    return sorted(memory_dir.rglob("*.md"))


def scan_features(repository_path: Path) -> list[Path]:
    specs_dir = repository_path / "specs"
    if not specs_dir.is_dir():
        return []
    results: list[Path] = []
    for entry in sorted(specs_dir.iterdir()):
        if entry.is_symlink() and not entry.is_dir():
            logger.warning("speckit_broken_symlink", path=str(entry))
            continue
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        results.extend(sorted(entry.rglob("*.md")))
    return results
