from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.speckit.plugin import SpecKitAdapter


def _make_repo(root: Path) -> None:
    (root / ".specify" / "memory").mkdir(parents=True)
    (root / ".specify" / "memory" / "constitution.md").write_text(
        "# Constitution\n\nWe the people...\n"
    )
    (root / "specs" / "feature-a").mkdir(parents=True)
    (root / "specs" / "feature-a" / "spec.md").write_text(
        "# Feature A\n\n## Overview\n\nThis is feature A\n"
    )
    (root / "specs" / "feature-a" / "plan.md").write_text(
        "# Plan\n\n## Steps\n\n1. Do thing\n"
    )
    (root / "specs" / "feature-a" / "tasks.md").write_text("# Tasks\n\n- [ ] Task 1\n")
    (root / "specs" / "feature-a" / "research.md").write_text(
        "# Research\n\n## Findings\n\nInteresting...\n"
    )
    (root / "specs" / "feature-a" / "data-model.md").write_text(
        "# Data Model\n\n## Entities\n\nUser\n"
    )
    (root / "specs" / "feature-a" / "checklists").mkdir()
    (root / "specs" / "feature-a" / "checklists" / "ux.md").write_text(
        "# UX Checklist\n\n- [ ] Login\n"
    )
    (root / "specs" / "feature-a" / "notes.md").write_text(
        "# Notes\n\nRandom thoughts\n"
    )
    (root / "specs" / "feature-b").mkdir(parents=True)
    (root / "specs" / "feature-b" / "spec.md").write_text(
        "# Feature B\n\n## Details\n\nThis is feature B\n"
    )


class TestFullScan:
    def test_repository_detection(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        assert adapter.supports(tmp_path) is True

    def test_governance_scan(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        docs = adapter.scan_memory(tmp_path)
        assert len(docs) == 1
        assert docs[0].document_type == "constitution"
        assert docs[0].metadata["kind"] == "governance"
        assert docs[0].metadata["feature"] is None

    def test_feature_scan(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        docs = adapter.scan_features(tmp_path)
        assert len(docs) == 8

    def test_full_scan_returns_all_documents(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        docs = adapter.scan(tmp_path)
        assert len(docs) == 9

    def test_artifact_types_in_full_scan(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        docs = adapter.scan(tmp_path)
        types = {d.document_type for d in docs}
        assert "constitution" in types
        assert "specification" in types
        assert "plan" in types
        assert "tasks" in types
        assert "research" in types
        assert "data-model" in types
        assert "checklist" in types
        assert "unknown" in types

    def test_metadata_preservation_end_to_end(self, tmp_path: Path) -> None:
        _make_repo(tmp_path)
        adapter = SpecKitAdapter()
        docs = adapter.scan(tmp_path)

        for doc in docs:
            assert doc.metadata is not None
            assert doc.metadata["framework"] == "speckit"
            assert "artifact_type" in doc.metadata
            assert "kind" in doc.metadata
            assert "feature" in doc.metadata
            assert "workspace" in doc.metadata
            assert "relative_path" in doc.metadata

        gov_docs = [d for d in docs if d.metadata["kind"] == "governance"]
        feat_docs = [d for d in docs if d.metadata["kind"] != "governance"]
        assert len(gov_docs) == 1
        assert all(d.metadata["feature"] is None for d in gov_docs)
        assert all(d.metadata["feature"] is not None for d in feat_docs)
