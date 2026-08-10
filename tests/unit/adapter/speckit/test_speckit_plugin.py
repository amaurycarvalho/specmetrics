from __future__ import annotations

from pathlib import Path

from specmetrics.plugins.adapter.speckit.plugin import (
    ScanError,
    ScanResult,
    ScanStats,
    SpecKitAdapter,
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


class TestSpecKitScanWithResultStats:
    """Kills survivors in ``SpecKitAdapter._scan_with_result`` (mutmut_13,29,38..58)."""

    def test_stats_after_full_scan(self, tmp_path: Path, monkeypatch) -> None:
        from datetime import UTC
        from datetime import datetime as real_datetime

        import specmetrics.plugins.adapter.speckit.plugin as plugin_mod

        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution")
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")

        t0 = real_datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        t1 = real_datetime(2024, 1, 1, 0, 0, 1, tzinfo=UTC)
        calls = {"n": 0}

        class FakeDatetime:
            @classmethod
            def now(cls, tz=None):
                calls["n"] += 1
                return t0 if calls["n"] == 1 else t1

        monkeypatch.setattr(plugin_mod, "datetime", FakeDatetime)

        adapter = SpecKitAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert result.stats.total_files_found == 2
        assert result.stats.total_documents == 2
        assert result.stats.total_errors == 0
        assert result.stats.duration_ms == 1000
        assert result.stats.governance_count == 1
        assert result.stats.specification_count == 1
        assert result.stats.feature_count == 1
        assert result.errors == []
        assert result.scanned_at == t1

    def test_error_scan_records_errors_and_stats(self, tmp_path: Path) -> None:
        bad = tmp_path / "specs" / "feature-a" / "spec.md"
        bad.parent.mkdir(parents=True)
        bad.write_bytes(b"\xff\xfe\x00\x01")
        adapter = SpecKitAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "ENCODING_ERROR"
        assert result.stats.total_errors == 1
        assert result.stats.total_documents == 0

    def test_scanned_at_is_utc_aware(self, tmp_path: Path) -> None:
        (tmp_path / ".specify" / "memory").mkdir(parents=True)
        adapter = SpecKitAdapter()
        result = adapter._scan_with_result(tmp_path)
        assert result.scanned_at is not None
        assert result.scanned_at.tzinfo is not None


class TestCreateSpecKitAdapterMetadata:
    """Kills survivors in ``create_speckit_adapter_metadata``."""

    def test_full_metadata(self) -> None:
        from specmetrics.kernel.plugin_metadata import PluginType
        from specmetrics.plugins.adapter.speckit.plugin import (
            create_speckit_adapter_metadata,
        )

        meta = create_speckit_adapter_metadata()
        assert meta.id == "speckit-adapter"
        assert meta.api_version == "0.1.0"
        assert meta.plugin_type == PluginType.ADAPTER
        assert meta.handled_event_types == ()
        assert isinstance(meta.handler_factory(), SpecKitAdapter)
        assert meta.name == "SpecKit Specification Adapter"
        assert meta.description == (
            "Discovers and normalizes SpecKit specification artifacts"
        )
        assert meta.version == "0.1.0"
