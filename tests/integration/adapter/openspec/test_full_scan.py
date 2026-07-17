from __future__ import annotations

from pathlib import Path


from specmetrics.plugins.adapter.openspec.plugin import OpenSpecAdapter


def _make_openspec_repo(root: Path) -> None:
    specs = {
        "openspec/specs/auth/spec.md": "# Auth Spec\n\n## Login\n\nLogin page\n",
        "openspec/specs/api/spec.md": "# API Spec\n\n## Endpoints\n\nREST API\n",
        "openspec/specs/payment/spec.md": "# Payment Spec\n\n## Checkout\n\nPayment flow\n",
    }
    changes = {
        "openspec/changes/add-oauth/proposal.md": "# Add OAuth\n\n## Motivation\n\nNeed OAuth\n",
        "openspec/changes/add-oauth/design.md": "# OAuth Design\n\n## Architecture\n\nOAuth flow\n",
        "openspec/changes/add-oauth/tasks.md": "# OAuth Tasks\n\n- [ ] Setup\n",
        "openspec/changes/add-oauth/specs/auth/spec.md": "# Delta Auth\n\n## Changes\n\nModified\n",
        "openspec/changes/audit-log/proposal.md": "# Audit Log\n\n## Motivation\n\nLog everything\n",
    }
    archived = {
        "openspec/changes/archive/old-feature/proposal.md": "# Old Feature\n\n## Legacy\n\nOld\n",
        "openspec/changes/archive/old-feature/specs/api/spec.md": "# Old Delta\n\n## Removed\n\nAPI\n",
    }
    for path_str, content in {**specs, **changes, **archived}.items():
        p = root / path_str
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)


class TestFullScan:
    def test_full_scan_discovers_all_artifacts(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path)
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)
        assert len(docs) == 10

    def test_detects_openspec_repository(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path)
        adapter = OpenSpecAdapter()
        assert adapter.supports(tmp_path) is True

    def test_metadata_preserved_end_to_end(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path)
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)

        for doc in docs:
            assert doc.metadata is not None
            assert doc.metadata["framework"] == "openspec"
            assert doc.metadata["relative_path"] is not None

        spec_docs = [d for d in docs if d.metadata["kind"] == "current-spec"]
        assert len(spec_docs) == 3

        change_docs = [d for d in docs if d.metadata.get("change") == "add-oauth"]
        assert len(change_docs) == 4

        archived_docs = [d for d in docs if d.metadata["status"] == "archived"]
        assert len(archived_docs) == 2

    def test_scan_with_active_and_archived_changes(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path)
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)

        active = [d for d in docs if d.metadata["status"] == "active"]
        archived = [d for d in docs if d.metadata["status"] == "archived"]

        assert len(active) == 8
        assert len(archived) == 2

    def test_scan_empty_openspec(self, tmp_path: Path) -> None:
        (tmp_path / "openspec" / "specs").mkdir(parents=True)
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)
        assert docs == []

    def test_all_documents_have_valid_ids(self, tmp_path: Path) -> None:
        _make_openspec_repo(tmp_path)
        adapter = OpenSpecAdapter()
        docs = adapter.scan(tmp_path)
        for doc in docs:
            assert doc.id.startswith("openspec:")
            assert ":" in doc.id
