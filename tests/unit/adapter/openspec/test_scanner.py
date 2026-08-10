from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from specmetrics.kernel.adapter_interface import Document
from specmetrics.plugins.adapter.openspec.scanner import (
    scan_changes,
    scan_specs,
)


def _make_openspec_repo(
    root: Path, *path_parts: str, content: str = "# Test\n"
) -> Path:
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
        archived = (
            tmp_path / "openspec" / "changes" / "archive" / "old-change" / "proposal.md"
        )
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
        for excluded in (
            ".git",
            "__pycache__",
            ".venv",
            "node_modules",
            ".specify",
            "_temp",
        ):
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
        delta = (
            tmp_path / "openspec" / "changes" / "add-auth" / "specs" / "api" / "spec.md"
        )
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
        archived = (
            tmp_path
            / "openspec"
            / "changes"
            / "archive"
            / "archived-change"
            / "proposal.md"
        )
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
    @pytest.mark.slow
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
        assert elapsed < 5.0, (
            f"SC-001: 500 artifacts scanned in {elapsed:.2f}s (limit: 5s)"
        )


class TestScanFilesHelpers:
    """Mutation-killing tests for ``openspec/_scan.py`` scan helpers.

    Targets survivors: scan_files__mutmut_7..36, scan_change_files__mutmut_7..42,
    bump_specification_count__mutmut_1..6, bump_change_type_count__mutmut_1..28.
    """

    def test_on_success_receives_doc_and_stats(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            scan_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            return Document(
                id=str(file_path),
                path=str(file_path.relative_to(repo_root)),
                document_type="specification",
                content=file_path.read_text(encoding="utf-8"),
            )

        repo = tmp_path / "repo"
        spec = repo / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        documents = []
        errors = []
        stats = ScanStats()
        calls = []
        scan_files(
            _normalize,
            [spec],
            repo,
            documents,
            errors,
            stats,
            on_success=lambda doc, st: calls.append((doc, st)),
        )
        assert len(calls) == 1
        assert calls[0][0] is documents[0]
        assert calls[0][1] is stats
        assert errors == []

    def test_bump_specification_count_callback_counts_only_specs(
        self, tmp_path: Path
    ) -> None:
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            bump_specification_count,
            scan_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            return Document(
                id=str(file_path),
                path=str(file_path.relative_to(repo_root)),
                document_type="proposal",
                content="",
            )

        repo = tmp_path / "repo"
        prop = repo / "changes" / "add" / "proposal.md"
        prop.parent.mkdir(parents=True)
        prop.write_text("# P")
        documents = []
        errors = []
        stats = ScanStats()
        scan_files(
            _normalize,
            [prop],
            repo,
            documents,
            errors,
            stats,
            on_success=bump_specification_count,
        )
        assert stats.specification_count == 0
        assert errors == []

    def test_encoding_error_recorded_with_context(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            scan_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            return Document(
                id=str(file_path),
                path=str(file_path.relative_to(repo_root)),
                document_type="specification",
                content=file_path.read_text(encoding="utf-8"),
            )

        repo = tmp_path / "repo"
        bad = repo / "specs" / "auth" / "spec.md"
        bad.parent.mkdir(parents=True)
        bad.write_bytes(b"\xff\xfe\x00\x01")
        documents = []
        errors = []
        stats = ScanStats()
        scan_files(
            _normalize,
            [bad],
            repo,
            documents,
            errors,
            stats,
            on_success=lambda doc, st: None,
        )
        assert len(errors) == 1
        err = errors[0]
        assert err.file_path == "specs/auth/spec.md"
        assert err.error_code == "ENCODING_ERROR"
        assert "bytes" in err.message or err.message
        assert stats.total_errors == 1
        assert documents == []

    def test_generic_exception_recorded_as_unreadable(self, tmp_path: Path) -> None:
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            scan_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            raise ValueError("boom")

        repo = tmp_path / "repo"
        target = repo / "specs" / "auth" / "spec.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Auth")
        documents = []
        errors = []
        stats = ScanStats()
        scan_files(
            _normalize,
            [target],
            repo,
            documents,
            errors,
            stats,
            on_success=lambda doc, st: None,
        )
        assert len(errors) == 1
        assert errors[0].error_code == "UNREADABLE"
        assert errors[0].message == "boom"
        assert stats.total_errors == 1

    def test_scan_change_files_counts_archived_and_active(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            scan_change_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            return Document(
                id=str(file_path),
                path=str(file_path.relative_to(repo_root)),
                document_type="proposal",
                content=file_path.read_text(encoding="utf-8"),
            )

        repo = tmp_path / "repo"
        change_files = []
        for i in range(2):
            active = repo / "changes" / f"active-{i}" / "proposal.md"
            active.parent.mkdir(parents=True)
            active.write_text("# Active")
            change_files.append((active, f"active-{i}", False))
        for i in range(2):
            archived = repo / "changes" / "archive" / f"old-{i}" / "proposal.md"
            archived.parent.mkdir(parents=True)
            archived.write_text("# Old")
            change_files.append((archived, f"old-{i}", True))
        documents = []
        errors = []
        stats = ScanStats()
        scan_change_files(
            _normalize, change_files, repo, documents, errors, stats
        )
        assert stats.active_changes == 2
        assert stats.archived_changes == 2
        assert stats.proposal_count == 4
        assert errors == []

    def test_scan_change_files_bumps_type_without_errors(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            scan_change_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> Document:
            return Document(
                id=str(file_path),
                path=str(file_path.relative_to(repo_root)),
                document_type="design",
                content=file_path.read_text(encoding="utf-8"),
            )

        repo = tmp_path / "repo"
        design = repo / "changes" / "add" / "design.md"
        design.parent.mkdir(parents=True)
        design.write_text("# Design")
        documents = []
        errors = []
        stats = ScanStats()
        scan_change_files(
            _normalize, [(design, "add", True)], repo, documents, errors, stats
        )
        assert stats.design_count == 1
        assert stats.unknown_count == 0
        assert errors == []


class TestBumpCountHelpers:
    """Mutation-killing tests for openspec ``_scan.bump_*`` helpers."""

    def test_bump_specification_count_increments_per_spec(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            bump_specification_count,
        )

        stats = ScanStats()
        for _ in range(2):
            bump_specification_count(
                Document(id="1", path="x", document_type="specification", content=""),
                stats,
            )
        assert stats.specification_count == 2

    def test_bump_specification_count_ignores_other_types(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            bump_specification_count,
        )

        stats = ScanStats()
        bump_specification_count(
            Document(id="1", path="x", document_type="proposal", content=""), stats
        )
        assert stats.specification_count == 0

    def test_bump_change_type_count_routes_known_types(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            bump_change_type_count,
        )

        counters = (
            "proposal_count",
            "design_count",
            "tasks_count",
            "specification_count",
        )
        for dt, attr in zip(
            ("proposal", "design", "tasks", "specification"), counters, strict=True
        ):
            stats = ScanStats()
            for _ in range(2):
                bump_change_type_count(
                    Document(id="1", path="x", document_type=dt, content=""), stats
                )
            assert getattr(stats, attr) == 2
            others = sum(getattr(stats, c) for c in counters if c != attr)
            assert others == 0
            assert stats.unknown_count == 0

    def test_bump_change_type_count_unknown_falls_through(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.openspec._scan import (
            ScanStats,
            bump_change_type_count,
        )

        stats = ScanStats()
        bump_change_type_count(
            Document(id="1", path="x", document_type="mystery", content=""), stats
        )
        assert stats.unknown_count == 1
        assert stats.proposal_count == 0


class TestListChangeDirsBrokenSymlink:
    """Mutation-killing tests for ``openspec/scanner._list_change_dirs``."""

    def test_broken_symlink_warns_with_event(self, tmp_path: Path, monkeypatch) -> None:
        import specmetrics.plugins.adapter.openspec.scanner as scanner_mod
        from specmetrics.plugins.adapter.openspec.scanner import _list_change_dirs

        changes_root = tmp_path / "openspec" / "changes"
        changes_root.mkdir(parents=True)
        link = changes_root / "broken"
        link.symlink_to(tmp_path / "gone", target_is_directory=True)
        mock_logger = mock.MagicMock()
        monkeypatch.setattr(scanner_mod, "logger", mock_logger)
        result = _list_change_dirs(changes_root)
        assert result == []
        mock_logger.warning.assert_called_once_with(
            "openspec_broken_symlink", path=str(link)
        )
