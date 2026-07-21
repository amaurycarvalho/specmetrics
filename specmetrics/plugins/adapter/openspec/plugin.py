from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .scanner import scan_specs, scan_changes
from .normalizer import normalize_document
from .metadata import build_metadata

logger = structlog.get_logger(__name__)


@dataclass
class ScanError:
    file_path: str
    error_code: str
    message: str


@dataclass
class ScanStats:
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
    documents: list[Document] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


FRAMEWORK_NAME = "openspec"
SUPPORTED_DOCUMENT_TYPES = ["specification", "proposal", "design", "tasks", "unknown"]
PLUGIN_ID = "openspec-adapter"
PLUGIN_VERSION = "0.1.0"


class OpenSpecAdapter:
    def __init__(self) -> None:
        self._supported_document_types = list(SUPPORTED_DOCUMENT_TYPES)

    @property
    def supported_document_types(self) -> list[str]:
        return self._supported_document_types

    @property
    def plugin_id(self) -> str:
        return PLUGIN_ID

    @property
    def plugin_version(self) -> str:
        return PLUGIN_VERSION

    @property
    def supported_framework(self) -> str:
        return FRAMEWORK_NAME

    @property
    def supported_artifact_types(self) -> list[str]:
        return list(SUPPORTED_DOCUMENT_TYPES)

    def supports(self, path: Path) -> bool:
        if not path.is_dir():
            return False
        openspec_dir = path / "openspec"
        if not openspec_dir.is_dir():
            return False
        specs_dir = openspec_dir / "specs"
        return specs_dir.is_dir()

    def scan(self, repository_path: Path) -> list[Document]:
        logger.info("openspec_scan_start", path=str(repository_path))
        result = self._scan_with_result(repository_path)
        logger.info(
            "openspec_scan_complete",
            documents=result.stats.total_documents,
            errors=result.stats.total_errors,
            duration_ms=result.stats.duration_ms,
        )
        return result.documents

    def _scan_with_result(self, repository_path: Path) -> ScanResult:
        start = datetime.now(timezone.utc)
        documents: list[Document] = []
        errors: list[ScanError] = []
        stats = ScanStats()

        spec_files = scan_specs(repository_path)
        for file_path in spec_files:
            try:
                doc = self.normalize_document(file_path, repository_path)
                documents.append(doc)
                if doc.document_type == "specification":
                    stats.specification_count += 1
            except UnicodeDecodeError as e:
                error_code = "ENCODING_ERROR"
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
            except Exception as e:
                error_code = "UNREADABLE"
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

        change_files = scan_changes(repository_path)
        for file_path, change_id, is_archived in change_files:
            try:
                doc = self.normalize_document(file_path, repository_path)
                documents.append(doc)
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
                if is_archived:
                    stats.archived_changes += 1
                else:
                    stats.active_changes += 1
            except UnicodeDecodeError as e:
                error_code = "ENCODING_ERROR"
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
            except Exception as e:
                error_code = "UNREADABLE"
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

        elapsed = datetime.now(timezone.utc) - start
        stats.total_files_found = len(spec_files) + len(change_files)
        stats.total_documents = len(documents)
        stats.total_errors = len(errors)
        stats.duration_ms = int(elapsed.total_seconds() * 1000)

        return ScanResult(
            documents=documents,
            errors=errors,
            stats=stats,
            scanned_at=datetime.now(timezone.utc),
        )

    def scan_specs(self, path: Path) -> list[Document]:
        spec_files = scan_specs(path)
        return [self.normalize_document(f, path) for f in spec_files]

    def scan_changes(self, path: Path) -> list[Document]:
        change_files = scan_changes(path)
        return [self.normalize_document(f, path) for f, _, _ in change_files]

    def normalize_document(self, file_path: Path, repo_root: Path) -> Document:
        return normalize_document(file_path, repo_root)

    def build_metadata(self, file_path: Path, repo_root: Path) -> dict[str, Any]:
        return build_metadata(file_path, repo_root)


def create_openspec_adapter_metadata() -> PluginMetadata:
    return PluginMetadata(
        id="openspec-adapter",
        api_version="0.1.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=(),
        handler_factory=lambda: OpenSpecAdapter(),
        name="OpenSpec Specification Adapter",
        description="Discovers and normalizes OpenSpec specification artifacts",
        version="0.1.0",
    )
