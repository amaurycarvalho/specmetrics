"""Internal scanning helpers for the OpenSpec adapter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import structlog

from specmetrics.kernel.adapter_interface import Document

logger = structlog.get_logger(__name__)


@dataclass
class ScanError:
    """Error recorded during a repository scan."""

    file_path: str
    error_code: str
    message: str


@dataclass
class ScanStats:
    """Statistics collected during a scan."""

    total_files_found: int = 0
    total_documents: int = 0
    total_errors: int = 0
    specification_count: int = 0
    proposal_count: int = 0
    design_count: int = 0
    tasks_count: int = 0
    unknown_count: int = 0
    active_changes: int = 0
    archived_changes: int = 0
    duration_ms: int = 0


@dataclass
class ScanResult:
    """Result of a repository scan."""

    documents: list[Document] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def record_error(
    file_path: Path,
    repository_path: Path,
    error_code: str,
    e: Exception,
    errors: list[ScanError],
    stats: ScanStats,
) -> None:
    """Log an error and record it in the scan error list."""
    logger.error(
        "openspec_file_error",
        path=str(file_path),
        error_code=error_code,
        message=str(e),
    )
    errors.append(
        ScanError(
            file_path=str(file_path.relative_to(repository_path)),
            error_code=error_code,
            message=str(e),
        )
    )
    stats.total_errors += 1


def scan_files(
    normalize: Callable[[Path, Path], Document],
    files: list[Path],
    repository_path: Path,
    documents: list[Document],
    errors: list[ScanError],
    stats: ScanStats,
    on_success: Callable[[Document, ScanStats], None],
) -> list[Path]:
    """Normalize each file into a document, recording failures as errors."""
    for file_path in files:
        try:
            doc = normalize(file_path, repository_path)
            documents.append(doc)
            on_success(doc, stats)
        except UnicodeDecodeError as e:
            record_error(
                file_path,
                repository_path,
                "ENCODING_ERROR",
                e,
                errors,
                stats,
            )
        except Exception as e:
            record_error(
                file_path,
                repository_path,
                "UNREADABLE",
                e,
                errors,
                stats,
            )
    return files


def scan_change_files(
    normalize: Callable[[Path, Path], Document],
    change_files: list[tuple[Path, str, bool]],
    repository_path: Path,
    documents: list[Document],
    errors: list[ScanError],
    stats: ScanStats,
) -> list[tuple[Path, str, bool]]:
    """Scan change files, bumping per-change-type statistics."""
    for file_path, _change_id, is_archived in change_files:
        try:
            doc = normalize(file_path, repository_path)
            documents.append(doc)
            bump_change_type_count(doc, stats)
            if is_archived:
                stats.archived_changes += 1
            else:
                stats.active_changes += 1
        except UnicodeDecodeError as e:
            record_error(
                file_path,
                repository_path,
                "ENCODING_ERROR",
                e,
                errors,
                stats,
            )
        except Exception as e:
            record_error(
                file_path,
                repository_path,
                "UNREADABLE",
                e,
                errors,
                stats,
            )
    return change_files


def bump_specification_count(doc: Document, stats: ScanStats) -> None:
    """Increment the specification counter when the document is a specification."""
    if doc.document_type == "specification":
        stats.specification_count += 1


def bump_change_type_count(doc: Document, stats: ScanStats) -> None:
    """Increment the count matching the document's change type."""
    dt = doc.document_type
    if dt == "proposal":
        stats.proposal_count += 1
    elif dt == "design":
        stats.design_count += 1
    elif dt == "tasks":
        stats.tasks_count += 1
    elif dt == "specification":
        stats.specification_count += 1
    else:
        stats.unknown_count += 1