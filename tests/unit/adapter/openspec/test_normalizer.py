from __future__ import annotations

from pathlib import Path

import pytest

from specmetrics.plugins.adapter.openspec.normalizer import normalize_document, _parse_sections


class TestNormalizeDocument:
    def test_reads_utf8_content(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth Spec\n\nContent here\n")
        doc = normalize_document(spec, tmp_path)
        assert doc.content == "# Auth Spec\n\nContent here\n"
        assert doc.document_type == "specification"

    def test_section_hierarchy_preserved(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Title\n\nIntro\n## Section 1\n\nBody 1\n## Section 2\n\nBody 2\n")
        doc = normalize_document(spec, tmp_path)
        assert doc.sections is not None
        assert len(doc.sections) >= 1
        assert doc.sections[0].title == "Title"

    def test_document_id_format(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        doc = normalize_document(spec, tmp_path)
        assert doc.id.startswith("openspec:specification:")

    def test_metadata_included(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "auth" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("# Auth")
        doc = normalize_document(spec, tmp_path)
        assert doc.metadata is not None
        assert doc.metadata["framework"] == "openspec"
        assert doc.metadata["artifact_type"] == "specification"

    def test_proposal_document_type(self, tmp_path: Path) -> None:
        prop = tmp_path / "openspec" / "changes" / "add-auth" / "proposal.md"
        prop.parent.mkdir(parents=True)
        prop.write_text("# Proposal")
        doc = normalize_document(prop, tmp_path)
        assert doc.document_type == "proposal"

    def test_design_document_type(self, tmp_path: Path) -> None:
        design = tmp_path / "openspec" / "changes" / "add-auth" / "design.md"
        design.parent.mkdir(parents=True)
        design.write_text("# Design")
        doc = normalize_document(design, tmp_path)
        assert doc.document_type == "design"

    def test_tasks_document_type(self, tmp_path: Path) -> None:
        tasks = tmp_path / "openspec" / "changes" / "add-auth" / "tasks.md"
        tasks.parent.mkdir(parents=True)
        tasks.write_text("# Tasks")
        doc = normalize_document(tasks, tmp_path)
        assert doc.document_type == "tasks"

    def test_unknown_document_type(self, tmp_path: Path) -> None:
        unknown = tmp_path / "openspec" / "specs" / "auth" / "readme.md"
        unknown.parent.mkdir(parents=True)
        unknown.write_text("# Readme")
        doc = normalize_document(unknown, tmp_path)
        assert doc.document_type == "unknown"

    def test_malformed_markdown_returns_raw_content(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("No headings here\n\nJust plain text\n")
        doc = normalize_document(spec, tmp_path)
        assert doc.content == "No headings here\n\nJust plain text\n"
        assert doc.sections is not None

    def test_corrupted_utf8_raises(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_bytes(b"\xff\xfe\x00\x01")
        with pytest.raises(UnicodeDecodeError):
            normalize_document(spec, tmp_path)

    def test_empty_file(self, tmp_path: Path) -> None:
        spec = tmp_path / "openspec" / "specs" / "test" / "spec.md"
        spec.parent.mkdir(parents=True)
        spec.write_text("")
        doc = normalize_document(spec, tmp_path)
        assert doc.content == ""
        assert doc.sections is not None


class TestParseSections:
    def test_atx_headings_parsed(self) -> None:
        sections = _parse_sections("# H1\n\n## H2\n\n### H3\n")
        assert len(sections) >= 1

    def test_levels_up_to_six(self) -> None:
        sections = _parse_sections("\n".join(f"{'#' * i} H{i}" for i in range(1, 7)))
        assert len(sections) == 1
        assert sections[0].title == "H1"
        s = sections[0]
        for expected in ("H2", "H3", "H4", "H5", "H6"):
            assert s.subsections and len(s.subsections) == 1
            s = s.subsections[0]
            assert s.title == expected

    def test_no_headings(self) -> None:
        sections = _parse_sections("Just plain text\nNo headings here")
        assert sections == []

    def test_empty_content(self) -> None:
        assert _parse_sections("") == []
