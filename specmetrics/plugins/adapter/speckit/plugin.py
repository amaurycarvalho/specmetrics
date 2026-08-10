"""SpecKit specification adapter plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import structlog

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from ._scan import (
    ScanError,
    ScanResult,
    ScanStats,
    bump_feature_type_count,
    bump_governance_count,
    gather_feature_dirs,
    scan_files,
)
from .metadata import build_metadata
from .normalizer import normalize_document
from .scanner import scan_features, scan_memory

logger = structlog.get_logger(__name__)

FRAMEWORK_NAME = "speckit"
SUPPORTED_DOCUMENT_TYPES = [
    "constitution",
    "specification",
    "plan",
    "tasks",
    "research",
    "data-model",
    "checklist",
    "unknown",
]
PLUGIN_ID = "speckit-adapter"
PLUGIN_VERSION = "0.1.0"


class SpecKitAdapter:
    """Adapter that discovers and normalizes SpecKit artifacts."""

    def __init__(self: Self) -> None:
        """Initialize the adapter."""
        self._supported_document_types = list(SUPPORTED_DOCUMENT_TYPES)

    @property
    def supported_document_types(self: Self) -> list[str]:
        """Return the supported document types."""
        return self._supported_document_types

    @property
    def plugin_id(self: Self) -> str:
        """Return the plugin identifier."""
        return PLUGIN_ID

    @property
    def plugin_version(self: Self) -> str:
        """Return the plugin version."""
        return PLUGIN_VERSION

    @property
    def supported_framework(self: Self) -> str:
        """Return the supported framework name."""
        return FRAMEWORK_NAME

    @property
    def supported_artifact_types(self: Self) -> list[str]:
        """Return the supported artifact types."""
        return list(SUPPORTED_DOCUMENT_TYPES)

    def supports(self: Self, path: Path) -> bool:
        """Return whether the path hosts a SpecKit repository."""
        if not path.is_dir():
            return False
        if (path / ".specify").is_dir():
            return True
        if (path / ".specify" / "memory" / "constitution.md").is_file():
            return True
        return bool((path / "specs").is_dir())

    def scan(self: Self, repository_path: Path) -> list[Document]:
        """Scan the repository and return normalized documents."""
        logger.info("speckit_scan_start", path=str(repository_path))
        result = self._scan_with_result(repository_path)
        logger.info(
            "speckit_scan_complete",
            documents=result.stats.total_documents,
            errors=result.stats.total_errors,
            duration_ms=result.stats.duration_ms,
        )
        return result.documents

    def _scan_with_result(self: Self, repository_path: Path) -> ScanResult:
        start = datetime.now(UTC)
        documents: list[Document] = []
        errors: list[ScanError] = []
        stats = ScanStats()

        memory_files = scan_files(
            self.normalize_document,
            scan_memory(repository_path),
            repository_path,
            documents,
            errors,
            stats,
            on_success=bump_governance_count,
        )
        feature_files = scan_files(
            self.normalize_document,
            scan_features(repository_path),
            repository_path,
            documents,
            errors,
            stats,
            on_success=bump_feature_type_count,
        )

        stats.feature_count = len(
            gather_feature_dirs(feature_files, repository_path)
        )

        elapsed = datetime.now(UTC) - start
        stats.total_files_found = len(memory_files) + len(feature_files)
        stats.total_documents = len(documents)
        stats.total_errors = len(errors)
        stats.duration_ms = int(elapsed.total_seconds() * 1000)

        return ScanResult(
            documents=documents,
            errors=errors,
            stats=stats,
            scanned_at=datetime.now(UTC),
        )

    def scan_memory(self: Self, path: Path) -> list[Document]:
        """Scan and normalize the .specify/memory documents."""
        memory_files = scan_memory(path)
        documents: list[Document] = []
        for f in memory_files:
            try:
                documents.append(self.normalize_document(f, path))
            except UnicodeDecodeError as e:
                logger.error(
                    "speckit_file_error",
                    path=str(f),
                    error_code="ENCODING_ERROR",
                    message=str(e),
                )
            except Exception as e:
                logger.error(
                    "speckit_file_error",
                    path=str(f),
                    error_code="UNREADABLE",
                    message=str(e),
                )
        return documents

    def scan_features(self: Self, path: Path) -> list[Document]:
        """Scan and normalize the specs documents."""
        feature_files = scan_features(path)
        documents: list[Document] = []
        for f in feature_files:
            try:
                documents.append(self.normalize_document(f, path))
            except UnicodeDecodeError as e:
                logger.error(
                    "speckit_file_error",
                    path=str(f),
                    error_code="ENCODING_ERROR",
                    message=str(e),
                )
            except Exception as e:
                logger.error(
                    "speckit_file_error",
                    path=str(f),
                    error_code="UNREADABLE",
                    message=str(e),
                )
        return documents

    def normalize_document(self: Self, file_path: Path, repo_root: Path) -> Document:
        """Normalize a single SpecKit file into a document."""
        return normalize_document(file_path, repo_root)

    def build_metadata(self: Self, file_path: Path, repo_root: Path) -> dict[str, Any]:
        """Build metadata for a SpecKit artifact file."""
        return build_metadata(file_path, repo_root)


def create_speckit_adapter_metadata() -> PluginMetadata:
    """Create metadata for the SpecKit adapter plugin."""
    return PluginMetadata(
        id="speckit-adapter",
        api_version="0.1.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=(),
        handler_factory=lambda: SpecKitAdapter(),
        name="SpecKit Specification Adapter",
        description="Discovers and normalizes SpecKit specification artifacts",
        version="0.1.0",
    )