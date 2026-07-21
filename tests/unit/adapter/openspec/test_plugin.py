from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.openspec.plugin import (
    OpenSpecAdapter,
    ScanError,
    ScanStats,
    ScanResult,
)


class TestSupports:
    def test_supports_returns_true_when_openspec_specs_exists(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        adapter = OpenSpecAdapter()
        assert adapter.supports(tmp_path) is True

    def test_supports_returns_false_when_openspec_missing(self, tmp_path: Path) -> None:
        adapter = OpenSpecAdapter()
        assert adapter.supports(tmp_path) is False

    def test_supports_returns_false_when_specs_missing(self, tmp_path: Path) -> None:
        (tmp_path / "openspec").mkdir()
        adapter = OpenSpecAdapter()
        assert adapter.supports(tmp_path) is False

    def test_supports_does_not_perform_full_scan(self, tmp_path: Path) -> None:
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        deep = tmp_path / "deep" / "nested" / "dir"
        deep.mkdir(parents=True)
        adapter = OpenSpecAdapter()
        assert adapter.supports(tmp_path) is True

    def test_supports_returns_false_for_file_path(self, tmp_path: Path) -> None:
        f = tmp_path / "some_file.txt"
        f.write_text("hello")
        adapter = OpenSpecAdapter()
        assert adapter.supports(f) is False


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
        adapter = OpenSpecAdapter()
        types = adapter.supported_document_types
        assert "specification" in types
        assert "proposal" in types
        assert "design" in types
        assert "tasks" in types
        assert "unknown" in types

    def test_plugin_id(self) -> None:
        assert OpenSpecAdapter().plugin_id == "openspec-adapter"

    def test_plugin_version(self) -> None:
        assert OpenSpecAdapter().plugin_version == "0.1.0"

    def test_supported_framework(self) -> None:
        assert OpenSpecAdapter().supported_framework == "openspec"

    def test_supported_artifact_types(self) -> None:
        types = OpenSpecAdapter().supported_artifact_types
        assert "specification" in types
