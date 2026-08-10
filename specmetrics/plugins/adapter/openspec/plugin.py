"""OpenSpec specification adapter plugin."""

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
    bump_specification_count,
    scan_change_files,
    scan_files,
)
from .metadata import build_metadata
from .normalizer import normalize_document
from .scanner import scan_changes, scan_specs

logger = structlog.get_logger(__name__)

FRAMEWORK_NAME = "openspec"
SUPPORTED_DOCUMENT_TYPES = ["specification", "proposal", "design", "tasks", "unknown"]
PLUGIN_ID = "openspec-adapter"
PLUGIN_VERSION = "0.1.0"


class OpenSpecAdapter:
    """Adapter that discovers and normalizes OpenSpec artifacts."""

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
        """Return whether the path hosts an OpenSpec repository."""
        if not path.is_dir():
            return False
        openspec_dir = path / "openspec"
        if not openspec_dir.is_dir():
            return False
        specs_dir = openspec_dir / "specs"
        return specs_dir.is_dir()

    def scan(self: Self, repository_path: Path) -> list[Document]:
        """Scan the repository and return normalized documents."""
        logger.info("openspec_scan_start", path=str(repository_path))
        result = self._scan_with_result(repository_path)
        logger.info(
            "openspec_scan_complete",
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

        spec_files = scan_files(
            self.normalize_document,
            scan_specs(repository_path),
            repository_path,
            documents,
            errors,
            stats,
            on_success=bump_specification_count,
        )
        change_files = scan_change_files(
            self.normalize_document,
            scan_changes(repository_path),
            repository_path,
            documents,
            errors,
            stats,
        )

        elapsed = datetime.now(UTC) - start
        stats.total_files_found = len(spec_files) + len(change_files)
        stats.total_documents = len(documents)
        stats.total_errors = len(errors)
        stats.duration_ms = int(elapsed.total_seconds() * 1000)

        return ScanResult(
            documents=documents,
            errors=errors,
            stats=stats,
            scanned_at=datetime.now(UTC),
        )

    def scan_specs(self: Self, path: Path) -> list[Document]:
        """Scan and normalize the openspec/specs documents."""
        spec_files = scan_specs(path)
        return [self.normalize_document(f, path) for f in spec_files]

    def scan_changes(self: Self, path: Path) -> list[Document]:
        """Scan and normalize the openspec/changes documents."""
        change_files = scan_changes(path)
        return [self.normalize_document(f, path) for f, _, _ in change_files]

    def normalize_document(self: Self, file_path: Path, repo_root: Path) -> Document:
        """Normalize a single OpenSpec file into a document."""
        return normalize_document(file_path, repo_root)

    def build_metadata(self: Self, file_path: Path, repo_root: Path) -> dict[str, Any]:
        """Build metadata for an OpenSpec artifact file."""
        return build_metadata(file_path, repo_root)


def create_openspec_adapter_metadata() -> PluginMetadata:
    """Create metadata for the OpenSpec adapter plugin."""
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