from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.speckit.plugin import (
    SpecKitAdapter,
    ScanError,
    ScanStats,
    ScanResult,
)


class TestSupports:
    def test_supports_returns_true_when_specify_exists(self, tmp_path: Path) -> None:
        (tmp_path / ".specify").mkdir()
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is True

    def test_supports_returns_true_when_constitution_exists(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / ".specify" / "memory").mkdir(parents=True)
        (tmp_path / ".specify" / "memory" / "constitution.md").write_text(
            "# Constitution"
        )
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is True

    def test_supports_returns_true_when_specs_exists(self, tmp_path: Path) -> None:
        (tmp_path / "specs").mkdir()
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is True

    def test_supports_returns_false_when_no_markers(self, tmp_path: Path) -> None:
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is False

    def test_supports_does_not_perform_full_scan(self, tmp_path: Path) -> None:
        (tmp_path / ".specify").mkdir()
        deep = tmp_path / "deep" / "nested" / "dir"
        deep.mkdir(parents=True)
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is True


class TestDataClasses:
    def test_scan_error_creation(self) -> None:
        err = ScanError(
            file_path="test.md", error_code="UNREADABLE", message="Could not read"
        )
        assert err.file_path == "test.md"
        assert err.error_code == "UNREADABLE"
        assert err.message == "Could not read"

    def test_scan_stats_defaults(self) -> None:
        stats = ScanStats()
        assert stats.total_files_found == 0
        assert stats.total_documents == 0
        assert stats.duration_ms == 0

    def test_scan_result_creation(self) -> None:
        result = ScanResult()
        assert result.documents == []
        assert result.errors == []
        assert result.stats.total_files_found == 0


class TestAdapterProperties:
    def test_supported_document_types(self) -> None:
        adapter = SpecKitAdapter()
        types = adapter.supported_document_types
        assert "constitution" in types
        assert "specification" in types
        assert "plan" in types
        assert "tasks" in types
        assert "research" in types
        assert "data-model" in types
        assert "checklist" in types
        assert "unknown" in types

    def test_plugin_id(self) -> None:
        assert SpecKitAdapter().plugin_id == "speckit-adapter"

    def test_plugin_version(self) -> None:
        assert SpecKitAdapter().plugin_version == "0.1.0"

    def test_supported_framework(self) -> None:
        assert SpecKitAdapter().supported_framework == "speckit"

    def test_supported_artifact_types(self) -> None:
        types = SpecKitAdapter().supported_artifact_types
        assert "specification" in types
