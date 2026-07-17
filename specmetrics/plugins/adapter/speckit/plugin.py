from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from specmetrics.kernel.adapter_interface import Document
from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginType

from .scanner import scan_memory, scan_features
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
    governance_count: int = 0
    feature_count: int = 0
    specification_count: int = 0
    plan_count: int = 0
    tasks_count: int = 0
    research_count: int = 0
    data_model_count: int = 0
    checklist_count: int = 0
    unknown_count: int = 0
    duration_ms: int = 0


@dataclass
class ScanResult:
    documents: list[Document] = field(default_factory=list)
    errors: list[ScanError] = field(default_factory=list)
    stats: ScanStats = field(default_factory=ScanStats)
    scanned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


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
        if (path / ".specify").is_dir():
            return True
        if (path / ".specify" / "memory" / "constitution.md").is_file():
            return True
        if (path / "specs").is_dir():
            return True
        return False

    def scan(self, repository_path: Path) -> list[Document]:
        logger.info("speckit_scan_start", path=str(repository_path))
        result = self._scan_with_result(repository_path)
        logger.info(
            "speckit_scan_complete",
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

        memory_files = scan_memory(repository_path)
        for file_path in memory_files:
            try:
                doc = self.normalize_document(file_path, repository_path)
                documents.append(doc)
                stats.governance_count += 1
            except UnicodeDecodeError as e:
                error_code = "ENCODING_ERROR"
                logger.error("speckit_file_error", path=str(file_path), error_code=error_code, message=str(e))
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
                logger.error("speckit_file_error", path=str(file_path), error_code=error_code, message=str(e))
                errors.append(
                    ScanError(
                        file_path=str(file_path.relative_to(repository_path)),
                        error_code=error_code,
                        message=str(e),
                    )
                )
                stats.total_errors += 1

        feature_files = scan_features(repository_path)
        for file_path in feature_files:
            try:
                doc = self.normalize_document(file_path, repository_path)
                documents.append(doc)
                dt = doc.document_type
                if dt == "specification":
                    stats.specification_count += 1
                elif dt == "plan":
                    stats.plan_count += 1
                elif dt == "tasks":
                    stats.tasks_count += 1
                elif dt == "research":
                    stats.research_count += 1
                elif dt == "data-model":
                    stats.data_model_count += 1
                elif dt == "checklist":
                    stats.checklist_count += 1
                else:
                    stats.unknown_count += 1
            except UnicodeDecodeError as e:
                error_code = "ENCODING_ERROR"
                logger.error("speckit_file_error", path=str(file_path), error_code=error_code, message=str(e))
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
                logger.error("speckit_file_error", path=str(file_path), error_code=error_code, message=str(e))
                errors.append(
                    ScanError(
                        file_path=str(file_path.relative_to(repository_path)),
                        error_code=error_code,
                        message=str(e),
                    )
                )
                stats.total_errors += 1

        feature_dirs = set()
        for fp in feature_files:
            try:
                rel = fp.relative_to(repository_path)
                if len(rel.parts) >= 2 and rel.parts[0] == "specs":
                    feature_dirs.add(rel.parts[1])
            except ValueError:
                pass
        stats.feature_count = len(feature_dirs)

        elapsed = datetime.now(timezone.utc) - start
        stats.total_files_found = len(memory_files) + len(feature_files)
        stats.total_documents = len(documents)
        stats.total_errors = len(errors)
        stats.duration_ms = int(elapsed.total_seconds() * 1000)

        return ScanResult(
            documents=documents,
            errors=errors,
            stats=stats,
            scanned_at=datetime.now(timezone.utc),
        )

    def scan_memory(self, path: Path) -> list[Document]:
        memory_files = scan_memory(path)
        documents: list[Document] = []
        for f in memory_files:
            try:
                documents.append(self.normalize_document(f, path))
            except UnicodeDecodeError as e:
                logger.error("speckit_file_error", path=str(f), error_code="ENCODING_ERROR", message=str(e))
            except Exception as e:
                logger.error("speckit_file_error", path=str(f), error_code="UNREADABLE", message=str(e))
        return documents

    def scan_features(self, path: Path) -> list[Document]:
        feature_files = scan_features(path)
        documents: list[Document] = []
        for f in feature_files:
            try:
                documents.append(self.normalize_document(f, path))
            except UnicodeDecodeError as e:
                logger.error("speckit_file_error", path=str(f), error_code="ENCODING_ERROR", message=str(e))
            except Exception as e:
                logger.error("speckit_file_error", path=str(f), error_code="UNREADABLE", message=str(e))
        return documents

    def normalize_document(self, file_path: Path, repo_root: Path) -> Document:
        return normalize_document(file_path, repo_root)

    def build_metadata(self, file_path: Path, repo_root: Path) -> dict[str, Any]:
        return build_metadata(file_path, repo_root)


def create_speckit_adapter_metadata() -> PluginMetadata:
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
