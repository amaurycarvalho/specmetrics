from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentSection:
    """Represents a section or subsection within a document.

    Enables hierarchy preservation without full semantic parsing.
    """

    id: str
    title: str
    level: int
    content: str
    subsections: list[DocumentSection] | None = None


@dataclass(frozen=True)
class Document:
    """Framework-agnostic representation of a specification document.

    Produced by adapters and consumed by downstream pipeline stages.
    """

    id: str
    path: str
    document_type: str
    content: str
    metadata: dict[str, Any] | None = None
    sections: list[DocumentSection] | None = None


class SpecificationAdapter(Protocol):
    """Structural interface that every SDD framework adapter must implement.

    Adapters discover specification documents in a repository, read them,
    and normalize them into framework-agnostic Document objects.
    """

    def scan(self, repository_path: Path) -> list[Document]:
        """Discover all specification documents in the repository.

        Must be read-only, idempotent, and must not perform semantic
        interpretation of content.
        """

    def supports(self, path: Path) -> bool:
        """Return True if this adapter can handle the given repository path.

        Must be fast (no full scan) and should check for framework markers
        like directory structure or config files.
        """


def discover_documents(
    repository_path: Path,
    patterns: tuple[str, ...] = ("*.md", "*.yml", "*.yaml"),
) -> list[Path]:
    """Recursively discover specification documents matching the given patterns.

    Returns a sorted list of file paths relative to the discovery patterns
    found under the repository path.
    """
    discovered: list[Path] = []
    for pattern in patterns:
        discovered.extend(sorted(repository_path.rglob(pattern)))
    return discovered


def read_document_safe(file_path: Path) -> str | None:
    """Read a file's text content safely, returning None on failure.

    Handles encoding errors, permission errors, and binary file detection,
    logging a warning and returning None for each failure.
    """
    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Skipping %s: %s", file_path, exc)
    return None


CANONICAL_TYPE_MAP: dict[str, str] = {
    "use-cases": "use_case",
    "use_cases": "use_case",
    "business-rules": "business_rule",
    "business_rules": "business_rule",
    "actors": "actor",
    "processes": "process",
    "data": "data_group",
    "glossary": "term",
    "terms": "term",
    "relationships": "relationship",
    "sections": "section",
}


def infer_document_type(file_path: Path) -> str:
    """Infer the canonical document type from the parent directory name.

    Falls back to 'unknown' if the directory name does not match any known
    canonical type.
    """
    parent = file_path.parent.name.lower()
    return CANONICAL_TYPE_MAP.get(parent, "unknown")
