from __future__ import annotations

from pathlib import Path

from specmetrics.plugins.adapter.openspec.plugin import (
    OpenSpecAdapter,
    ScanError,
    ScanResult,
    ScanStats,
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


class TestScanWithResultStats:
    """Kills survivors in ``OpenSpecAdapter._scan_with_result`` (mutmut_13,39..55)."""

    def test_stats_after_full_scan(self, tmp_path: Path, monkeypatch) -> None:
        from datetime import UTC
        from datetime import datetime as real_datetime

        import specmetrics.plugins.adapter.openspec.plugin as plugin_mod

        (tmp_path / "openspec" / "specs" / "auth" / "spec.md").parent.mkdir(
            parents=True
        )
        (tmp_path / "openspec" / "specs" / "auth" / "spec.md").write_text("# Auth")
        (tmp_path / "openspec" / "specs" / "api" / "spec.md").parent.mkdir(
            parents=True
        )
        (tmp_path / "openspec" / "specs" / "api" / "spec.md").write_text("# API")
        change = tmp_path / "openspec" / "changes" / "add" / "proposal.md"
        change.parent.mkdir(parents=True)
        change.write_text("# Proposal")

        t0 = real_datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        t1 = real_datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC)
        calls = {"n": 0}

        class FakeDatetime:
            @classmethod
            def now(cls, tz=None):
                calls["n"] += 1
                return t0 if calls["n"] == 1 else t1

        monkeypatch.setattr(plugin_mod, "datetime", FakeDatetime)

        adapter = OpenSpecAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert result.stats.total_files_found == 3
        assert result.stats.total_documents == 3
        assert result.stats.total_errors == 0
        assert result.stats.duration_ms == 1000
        assert result.stats.specification_count == 2
        assert result.stats.proposal_count == 1
        assert result.stats.active_changes == 1
        assert result.errors == []
        assert result.scanned_at == t1

    def test_error_scan_records_errors_and_stats(self, tmp_path: Path) -> None:
        bad = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        bad.parent.mkdir(parents=True)
        bad.write_bytes(b"\xff\xfe\x00\x01")
        adapter = OpenSpecAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "ENCODING_ERROR"
        assert result.stats.total_errors == 1
        assert result.stats.total_documents == 0

    def test_scanned_at_is_utc_aware(self, tmp_path: Path) -> None:
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        adapter = OpenSpecAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert result.scanned_at is not None
        assert result.scanned_at.tzinfo is not None


class TestCreateOpenSpecAdapterMetadata:
    """Kills survivors in ``create_openspec_adapter_metadata``."""

    def test_full_metadata(self) -> None:
        from specmetrics.kernel.plugin_metadata import PluginType
        from specmetrics.plugins.adapter.openspec.plugin import (
            create_openspec_adapter_metadata,
        )

        meta = create_openspec_adapter_metadata()
        assert meta.id == "openspec-adapter"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.ADAPTER
        assert meta.handled_event_types == ()
        assert isinstance(meta.handler_factory(), OpenSpecAdapter)
        assert meta.name == "OpenSpec Specification Adapter"
        assert meta.description == (
            "Discovers and normalizes OpenSpec specification artifacts"
        )
        assert meta.version == "0.1.0"
