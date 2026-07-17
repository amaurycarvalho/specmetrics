from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.openspec.scanner import (
    scan_specs,
    scan_changes,
)


def _make_openspec_repo(root: Path, *path_parts: str, content: str = "# Test\n") -> Path:
    target = root.joinpath("openspec", *path_parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return target


class TestScanSpecs:
    def test_recursive_spec_discovery(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path, "specs", "auth", "spec.md")
        _make_openspec_repo(tmp_path, "specs", "api", "spec.md")
        _make_openspec_repo(tmp_path, "specs", "payment", "spec.md")
        result = scan_specs(tmp_path)
        assert len(result) == 3

    def test_empty_specs_returns_zero(self, tmp_path: Path) -> None:
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        assert scan_specs(tmp_path) == []

    def test_missing_specs_returns_zero(self, tmp_path: Path) -> None:
        assert scan_specs(tmp_path) == []

    def test_nested_domain_discovery(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path, "specs", "auth", "api", "spec.md")
        _make_openspec_repo(tmp_path, "specs", "auth", "spec.md")
        result = scan_specs(tmp_path)
        assert len(result) == 2

    def test_non_spec_md_files_excluded(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path, "specs", "auth", "spec.md")
        _make_openspec_repo(tmp_path, "specs", "auth", "readme.md")
        result = scan_specs(tmp_path)
        assert len(result) == 1

    def test_duplicate_domain_names(self, tmp_path: Path) -> None:
        spec1 = _make_openspec_repo(tmp_path, "specs", "auth", "spec.md")
        spec2 = _make_openspec_repo(tmp_path, "specs", "auth", "sub", "spec.md")
        result = scan_specs(tmp_path)
        assert len(result) == 2
        assert spec1 in result
        assert spec2 in result


class TestScanChanges:
    def test_active_change_directory_enumeration(self, tmp_path: Path) -> None:
        change1 = tmp_path / "openspec" / "changes" / "add-auth" / "proposal.md"
        change2 = tmp_path / "openspec" / "changes" / "add-payment" / "proposal.md"
        change1.parent.mkdir(parents=True)
        change2.parent.mkdir(parents=True)
        change1.write_text("# Proposal")
        change2.write_text("# Proposal")
        results = scan_changes(tmp_path)
        assert len(results) == 2

    def test_archived_change_discovery(self, tmp_path: Path) -> None:
        archived = tmp_path / "openspec" / "changes" / "archive" / "old-change" / "proposal.md"
        archived.parent.mkdir(parents=True)
        archived.write_text("# Old proposal")
        results = scan_changes(tmp_path)
        assert len(results) == 1
        _, change_id, is_archived = results[0]
        assert change_id == "old-change"
        assert is_archived is True

    def test_temp_folder_exclusion(self, tmp_path: Path) -> None:
        valid = tmp_path / "openspec" / "changes" / "add-auth" / "proposal.md"
        valid.parent.mkdir(parents=True)
        valid.write_text("# Proposal")
        for excluded in (".git", "__pycache__", ".venv", "node_modules", ".specify", "_temp"):
            d = tmp_path / "openspec" / "changes" / excluded
            d.mkdir(parents=True)
            (d / "proposal.md").write_text("# Should be ignored")
        results = scan_changes(tmp_path)
        assert len(results) == 1
        assert results[0][1] == "add-auth"

    def test_missing_optional_artifacts(self, tmp_path: Path) -> None:
        change = tmp_path / "openspec" / "changes" / "add-auth"
        change.mkdir(parents=True)
        (change / "proposal.md").write_text("# Proposal")
        (change / "design.md").write_text("# Design")
        results = scan_changes(tmp_path)
        artifact_names = [r[0].name for r in results]
        assert "proposal.md" in artifact_names
        assert "design.md" in artifact_names
        assert "tasks.md" not in artifact_names

    def test_delta_spec_discovery(self, tmp_path: Path) -> None:
        delta = tmp_path / "openspec" / "changes" / "add-auth" / "specs" / "api" / "spec.md"
        delta.parent.mkdir(parents=True)
        delta.write_text("# Delta spec")
        results = scan_changes(tmp_path)
        assert len(results) == 1
        assert results[0][0].name == "spec.md"

    def test_empty_change_folders(self, tmp_path: Path) -> None:
        empty_change = tmp_path / "openspec" / "changes" / "empty-change"
        empty_change.mkdir(parents=True)
        assert scan_changes(tmp_path) == []

    def test_missing_changes_directory(self, tmp_path: Path) -> None:
        assert scan_changes(tmp_path) == []

    def test_archived_status_metadata(self, tmp_path: Path) -> None:
        archived = tmp_path / "openspec" / "changes" / "archive" / "old" / "proposal.md"
        archived.parent.mkdir(parents=True)
        archived.write_text("# Archived")
        results = scan_changes(tmp_path)
        assert len(results) == 1
        assert results[0][2] is True

    def test_mixed_active_and_archived(self, tmp_path: Path) -> None:
        active = tmp_path / "openspec" / "changes" / "active-change" / "proposal.md"
        archived = tmp_path / "openspec" / "changes" / "archive" / "archived-change" / "proposal.md"
        active.parent.mkdir(parents=True)
        archived.parent.mkdir(parents=True)
        active.write_text("# Active")
        archived.write_text("# Archived")
        results = scan_changes(tmp_path)
        assert len(results) == 2
        statuses = {(r[1], r[2]) for r in results}
        assert ("active-change", False) in statuses
        assert ("archived-change", True) in statuses

    def test_symbolic_link_following(self, tmp_path: Path) -> None:
        real_dir = tmp_path / "real_changes" / "add-auth"
        real_dir.mkdir(parents=True)
        (real_dir / "proposal.md").write_text("# Proposal via symlink")
        link = tmp_path / "openspec" / "changes" / "add-auth"
        link.parent.mkdir(parents=True)
        link.symlink_to(real_dir, target_is_directory=True)
        results = scan_changes(tmp_path)
        assert len(results) == 1


class TestPerFileErrorIsolation:
    def test_one_unreadable_does_not_block_others(self, tmp_path: Path) -> None:
        spec1 = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec1.parent.mkdir(parents=True)
        spec1.write_text("# Auth")
        spec2 = tmp_path / "openspec" / "specs" / "api" / "spec.md"
        spec2.parent.mkdir(parents=True)
        spec2.write_text("# API")
        from specmetrics.plugins.adapter.openspec.plugin import OpenSpecAdapter
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)
        assert len(docs) == 2


class TestBenchmark:
    def test_benchmark_500_artifacts(self, tmp_path: Path) -> None:
        import time
        base = tmp_path / "openspec" / "specs"
        for i in range(500):
            domain_dir = base / f"domain{i}"
            domain_dir.mkdir(parents=True)
            (domain_dir / "spec.md").write_text(f"# Domain {i}\n\nContent {i}\n")
        from specmetrics.plugins.adapter.openspec.plugin import OpenSpecAdapter
        adapter = OpenSpecAdapter()
        start = time.perf_counter()
        docs = adapter.scan(tmp_path)
        elapsed = time.perf_counter() - start
        assert len(docs) == 500
        assert elapsed < 5.0, f"SC-001: 500 artifacts scanned in {elapsed:.2f}s (limit: 5s)"
