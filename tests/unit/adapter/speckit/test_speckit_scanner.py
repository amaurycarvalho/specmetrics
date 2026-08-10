from __future__ import annotations

from pathlib import Path

from specmetrics.plugins.adapter.speckit.scanner import (
    scan_features,
    scan_memory,
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


class TestScanFilesHelpersSpeckit:
    """Kills survivors in ``speckit/_scan.py`` scan helpers."""

    def test_on_success_receives_doc_and_stats(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.speckit._scan import (
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
        spec = repo / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature")
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

    def test_encoding_error_recorded_with_context(self, tmp_path: Path) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.speckit._scan import (
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
        bad = repo / "specs" / "feature-a" / "spec.md"
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
        assert errors[0].file_path == "specs/feature-a/spec.md"
        assert errors[0].error_code == "ENCODING_ERROR"
        assert stats.total_errors == 1

    def test_generic_exception_recorded_as_unreadable(self, tmp_path: Path) -> None:
        from specmetrics.plugins.adapter.speckit._scan import (
            ScanStats,
            scan_files,
        )

        def _normalize(file_path: Path, repo_root: Path) -> object:
            raise ValueError("boom")

        repo = tmp_path / "repo"
        target = repo / "specs" / "feature-a" / "spec.md"
        target.parent.mkdir(parents=True)
        target.write_text("# Feature")
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


class TestSpeckitBumpHelpers:
    """Kills survivors in ``speckit/_scan.bump_*`` helpers."""

    def test_bump_governance_count_increments_per_document(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.speckit._scan import (
            ScanStats,
            bump_governance_count,
        )

        stats = ScanStats()
        for _ in range(2):
            bump_governance_count(
                Document(id="1", path="x", document_type="constitution", content=""),
                stats,
            )
        assert stats.governance_count == 2

    def test_bump_feature_type_count_routes_known_types(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.speckit._scan import (
            ScanStats,
            bump_feature_type_count,
        )

        counters = (
            "specification_count",
            "plan_count",
            "tasks_count",
            "research_count",
            "data_model_count",
            "checklist_count",
        )
        types = (
            "specification",
            "plan",
            "tasks",
            "research",
            "data-model",
            "checklist",
        )
        for dt, attr in zip(types, counters, strict=True):
            stats = ScanStats()
            for _ in range(2):
                bump_feature_type_count(
                    Document(id="1", path="x", document_type=dt, content=""), stats
                )
            assert getattr(stats, attr) == 2
            others = sum(getattr(stats, c) for c in counters if c != attr)
            assert others == 0
            assert stats.unknown_count == 0

    def test_bump_feature_type_count_unknown_falls_through(self) -> None:
        from specmetrics.kernel.adapter_interface import Document
        from specmetrics.plugins.adapter.speckit._scan import (
            ScanStats,
            bump_feature_type_count,
        )

        stats = ScanStats()
        bump_feature_type_count(
            Document(id="1", path="x", document_type="mystery", content=""), stats
        )
        assert stats.unknown_count == 1
        assert stats.specification_count == 0


class TestGatherFeatureDirs:
    """Kills survivors in ``speckit/_scan.gather_feature_dirs`` (mutmut_4..12)."""

    def test_extracts_feature_under_specs(self, tmp_path: Path) -> None:
        from specmetrics.plugins.adapter.speckit._scan import gather_feature_dirs

        spec = tmp_path / "specs" / "feature-a" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Feature A")
        result = gather_feature_dirs([spec], tmp_path)
        assert result == {"feature-a"}

    def test_specs_top_level_file_is_feature(self, tmp_path: Path) -> None:
        from specmetrics.plugins.adapter.speckit._scan import gather_feature_dirs

        spec = tmp_path / "specs" / "x.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# X")
        result = gather_feature_dirs([spec], tmp_path)
        assert result == {"x.md"}

    def test_ignores_non_specs_files(self, tmp_path: Path) -> None:
        from specmetrics.plugins.adapter.speckit._scan import gather_feature_dirs

        constitution = tmp_path / ".specify" / "memory" / "constitution.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_text("# Constitution")
        result = gather_feature_dirs([constitution], tmp_path)
        assert result == set()
