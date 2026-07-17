from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.openspec.metadata import (
    build_metadata,
)


class TestBuildMetadata:
    def test_minimum_metadata_completeness(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        meta = build_metadata(spec, tmp_path)
        required = {"framework", "repository_root", "artifact_type", "domain", "change", "status", "relative_path"}
        assert required.issubset(meta.keys())

    def test_spec_domain_metadata(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        meta = build_metadata(spec, tmp_path)
        assert meta["domain"] == "auth"
        assert meta["artifact_type"] == "specification"
        assert meta["kind"] == "current-spec"

    def test_change_identifier_metadata(self, tmp_path: Path) -> None:
        prop = tmp_path / "openspec" / "changes" / "add-user-auth" / "proposal.md"
        prop.parent.mkdir(parents=True)
        prop.write_text("# Proposal")
        meta = build_metadata(prop, tmp_path)
        assert meta["change"] == "add-user-auth"
        assert meta["artifact_type"] == "proposal"
        assert meta["kind"] == "proposal"

    def test_artifact_type_mapping(self, tmp_path: Path) -> None:
        mapping = {
            "spec.md": "specification",
            "proposal.md": "proposal",
            "design.md": "design",
            "tasks.md": "tasks",
        }
        for filename, expected_type in mapping.items():
            f = tmp_path / filename
            f.write_text("# Test")
            meta = build_metadata(f, tmp_path)
            assert meta["artifact_type"] == expected_type, f"{filename} should map to {expected_type}"

    def test_unknown_file_handling(self, tmp_path: Path) -> None:
        unknown = tmp_path / "openspec" / "specs" / "auth" / "readme.md"
        unknown.parent.mkdir(parents=True)
        unknown.write_text("# Readme")
        meta = build_metadata(unknown, tmp_path)
        assert meta["artifact_type"] == "unknown"
        assert meta["kind"] == "unknown"

    def test_archived_status(self, tmp_path: Path) -> None:
        archived = tmp_path / "openspec" / "changes" / "archive" / "old" / "proposal.md"
        archived.parent.mkdir(parents=True)
        archived.write_text("# Old")
        meta = build_metadata(archived, tmp_path)
        assert meta["status"] == "archived"

    def test_active_status(self, tmp_path: Path) -> None:
        active = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        active.parent.mkdir(parents=True)
        active.write_text("# Auth")
        meta = build_metadata(active, tmp_path)
        assert meta["status"] == "active"

    def test_delta_spec_kind(self, tmp_path: Path) -> None:
        delta = tmp_path / "openspec" / "changes" / "add-auth" / "specs" / "api" / "spec.md"
        delta.parent.mkdir(parents=True)
        delta.write_text("# Delta")
        meta = build_metadata(delta, tmp_path)
        assert meta["kind"] == "delta-spec"
        assert meta["artifact_type"] == "specification"

    def test_framework_always_openspec(self, tmp_path: Path) -> None:
        f = tmp_path / "any.md"
        f.write_text("# Test")
        meta = build_metadata(f, tmp_path)
        assert meta["framework"] == "openspec"

    def test_repository_root_absolute(self, tmp_path: Path) -> None:
        f = tmp_path / "spec.md"
        f.write_text("# Test")
        meta = build_metadata(f, tmp_path)
        assert meta["repository_root"] == str(tmp_path.resolve())

    def test_relative_path(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        meta = build_metadata(spec, tmp_path)
        assert meta["relative_path"] == "openspec/specs/auth/spec.md"

    def test_change_null_for_baseline_spec(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        meta = build_metadata(spec, tmp_path)
        assert meta["change"] is None

    def test_domain_null_for_change_artifacts(self, tmp_path: Path) -> None:
        prop = tmp_path / "openspec" / "changes" / "add-auth" / "proposal.md"
        prop.parent.mkdir(parents=True)
        prop.write_text("# Proposal")
        meta = build_metadata(prop, tmp_path)
        assert meta["domain"] is None

    def test_domain_for_delta_spec(self, tmp_path: Path) -> None:
        delta = tmp_path / "openspec" / "changes" / "add-auth" / "specs" / "api" / "spec.md"
        delta.parent.mkdir(parents=True)
        delta.write_text("# Delta")
        meta = build_metadata(delta, tmp_path)
        assert meta["domain"] == "api"
