from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.speckit.scanner import (
    scan_memory,
    scan_features,
)


def _make_file(root: Path, *path_parts: str, content: str = "# Test\n") -> Path:
    target = root.joinpath(*path_parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return target


class TestScanMemory:
    def test_governance_document_discovery(self, tmp_path: Path) -> None:
        _make_file(tmp_path, ".specify", "memory", "constitution.md")
        result = scan_memory(tmp_path)
        assert len(result) == 1
        assert result[0].name == "constitution.md"

    def test_missing_memory_returns_zero(self, tmp_path: Path) -> None:
        assert scan_memory(tmp_path) == []

    def test_only_md_files_included(self, tmp_path: Path) -> None:
        _make_file(tmp_path, ".specify", "memory", "constitution.md")
        _make_file(tmp_path, ".specify", "memory", "notes.md")
        _make_file(tmp_path, ".specify", "memory", "script.py")
        _make_file(tmp_path, ".specify", "memory", "config.yml")
        result = scan_memory(tmp_path)
        assert len(result) == 2
        assert all(p.suffix == ".md" for p in result)

    def test_nested_memory_files(self, tmp_path: Path) -> None:
        _make_file(tmp_path, ".specify", "memory", "sub", "nested.md")
        _make_file(tmp_path, ".specify", "memory", "constitution.md")
        result = scan_memory(tmp_path)
        assert len(result) == 2


class TestScanFeatures:
    def test_feature_workspace_discovery(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "spec.md")
        _make_file(tmp_path, "specs", "feature-b", "spec.md")
        result = scan_features(tmp_path)
        assert len(result) == 2

    def test_recursive_checklist_discovery(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "checklists", "requirements.md")
        _make_file(tmp_path, "specs", "feature-a", "checklists", "sub", "nested.md")
        result = scan_features(tmp_path)
        assert len(result) == 2
        assert all("checklists" in str(p) for p in result)

    def test_feature_with_only_spec_md(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "spec.md")
        result = scan_features(tmp_path)
        assert len(result) == 1

    def test_missing_optional_artifacts(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "spec.md")
        result = scan_features(tmp_path)
        names = [p.name for p in result]
        assert "spec.md" in names
        assert "plan.md" not in names
        assert "tasks.md" not in names

    def test_empty_specs_returns_zero(self, tmp_path: Path) -> None:
        (tmp_path / "specs").mkdir()
        assert scan_features(tmp_path) == []

    def test_duplicate_feature_directories(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "spec.md")
        _make_file(tmp_path, "specs", "feature-a", "plan.md")
        _make_file(tmp_path, "specs", "feature-b", "spec.md")
        result = scan_features(tmp_path)
        assert len(result) == 3

    def test_missing_specs_returns_zero(self, tmp_path: Path) -> None:
        assert scan_features(tmp_path) == []

    def test_all_artifact_types_discovered(self, tmp_path: Path) -> None:
        _make_file(tmp_path, "specs", "feature-a", "spec.md")
        _make_file(tmp_path, "specs", "feature-a", "plan.md")
        _make_file(tmp_path, "specs", "feature-a", "tasks.md")
        _make_file(tmp_path, "specs", "feature-a", "research.md")
        _make_file(tmp_path, "specs", "feature-a", "data-model.md")
        _make_file(tmp_path, "specs", "feature-a", "checklists", "ux.md")
        result = scan_features(tmp_path)
        assert len(result) == 6
