from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.speckit.metadata import (
    build_metadata,
)


class TestBuildMetadata:
    def test_minimum_metadata_completeness(self, tmp_path: Path) -> None:
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")
        meta = build_metadata(spec, tmp_path)
        required = {"framework", "artifact_type", "kind", "feature", "workspace", "relative_path"}
        assert required.issubset(meta.keys())

    def test_feature_identifier_from_parent_directory(self, tmp_path: Path) -> None:
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")
        meta = build_metadata(spec, tmp_path)
        assert meta["feature"] == "feature-a"

    def test_artifact_type_mapping(self, tmp_path: Path) -> None:
        mapping = {
            "constitution.md": "constitution",
            "spec.md": "specification",
            "plan.md": "plan",
            "tasks.md": "tasks",
            "research.md": "research",
            "data-model.md": "data-model",
        }
        for filename, expected_type in mapping.items():
            f = tmp_path / filename
            f.write_text("# Test")
            meta = build_metadata(f, tmp_path)
            assert meta["artifact_type"] == expected_type, f"{filename} should map to {expected_type}"

    def test_unknown_file_handling(self, tmp_path: Path) -> None:
        unknown = tmp_path / "specs" / "feature-a" / "notes.md"
        unknown.parent.mkdir(parents=True)
        unknown.write_text("# Notes")
        meta = build_metadata(unknown, tmp_path)
        assert meta["artifact_type"] == "unknown"
        assert meta["kind"] == "unknown"

    def test_data_model_kind(self, tmp_path: Path) -> None:
        dm = tmp_path / "specs" / "feature-a" / "data-model.md"
        dm.parent.mkdir(parents=True)
        dm.write_text("# Data Model")
        meta = build_metadata(dm, tmp_path)
        assert meta["kind"] == "data-model"
        assert meta["artifact_type"] == "data-model"

    def test_governance_vs_feature_distinction(self, tmp_path: Path) -> None:
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution")
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")

        gov_meta = build_metadata(constitution, tmp_path)
        feat_meta = build_metadata(spec, tmp_path)

        assert gov_meta["feature"] is None
        assert feat_meta["feature"] == "feature-a"
        assert gov_meta["kind"] == "governance"
        assert feat_meta["kind"] == "specification"

    def test_kind_mapping(self, tmp_path: Path) -> None:
        cases = [
            ("constitution.md", "governance"),
            ("spec.md", "specification"),
            ("plan.md", "architecture"),
            ("tasks.md", "implementation"),
            ("research.md", "research"),
            ("data-model.md", "data-model"),
        ]
        for filename, expected_kind in cases:
            f = tmp_path / filename
            f.write_text("# Test")
            meta = build_metadata(f, tmp_path)
            assert meta["kind"] == expected_kind, f"{filename} should have kind {expected_kind}"

    def test_framework_always_speckit(self, tmp_path: Path) -> None:
        f = tmp_path / "any.md"
        f.write_text("# Test")
        meta = build_metadata(f, tmp_path)
        assert meta["framework"] == "speckit"

    def test_relative_path(self, tmp_path: Path) -> None:
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")
        meta = build_metadata(spec, tmp_path)
        assert meta["relative_path"] == "specs/feature-a/spec.md"

    def test_workspace_for_governance(self, tmp_path: Path) -> None:
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution")
        meta = build_metadata(constitution, tmp_path)
        assert meta["workspace"] == ".specify/memory"

    def test_workspace_for_feature(self, tmp_path: Path) -> None:
        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")
        meta = build_metadata(spec, tmp_path)
        assert meta["workspace"] == "specs/feature-a"

    def test_feature_null_for_governance(self, tmp_path: Path) -> None:
        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution")
        meta = build_metadata(constitution, tmp_path)
        assert meta["feature"] is None

    def test_checklist_artifact_type(self, tmp_path: Path) -> None:
        cl = tmp_path / "specs" / "feature-a" / "checklists" / "ux.md"
        cl.parent.mkdir(parents=True)
        cl.write_text("# UX Checklist")
        meta = build_metadata(cl, tmp_path)
        assert meta["artifact_type"] == "checklist"
        assert meta["kind"] == "checklist"
