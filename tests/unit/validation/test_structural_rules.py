from __future__ import annotations

from pathlib import Path

from specmetrics.kernel.validation.models import SpecificationDocument
from specmetrics.kernel.validation.rules.structural import (
    file_not_empty,
    file_readable,
    mandatory_sections_exist,
    no_unknown_sections,
    parseable_markdown,
)


def _doc(path: str, content: str = "") -> SpecificationDocument:
    return SpecificationDocument(
        path=Path(path),
        content=content,
        size_bytes=len(content),
        line_count=len(content.splitlines()),
    )


class TestFileReadable:
    def test_nonexistent_file_fails(self):
        doc = _doc("/nonexistent/spec.md")
        result = file_readable(doc)
        assert not result.passed
        assert result.message.startswith("File does not exist")


class TestFileNotEmpty:
    def test_empty_content_fails(self):
        result = file_not_empty(_doc("test.md", ""))
        assert not result.passed
        assert "empty" in result.message.lower()

    def test_non_empty_passes(self):
        result = file_not_empty(_doc("test.md", "# Title\ncontent"))
        assert result.passed


class TestParseableMarkdown:
    def test_valid_markdown_passes(self):
        result = parseable_markdown(_doc("test.md", "# Title\n\nSome text"))
        assert result.passed


class TestMandatorySectionsExist:
    def test_all_sections_present_passes(self):
        content = (
            "## User Scenarios & Testing\ncontent\n"
            "## Constitution Check\ncontent\n"
            "## Requirements\ncontent\n"
            "## Success Criteria\ncontent\n"
            "## Assumptions\ncontent\n"
        )
        result = mandatory_sections_exist(_doc("test.md", content))
        assert result.passed

    def test_missing_section_fails(self):
        result = mandatory_sections_exist(_doc("test.md", "## Requirements\ncontent\n"))
        assert not result.passed
        assert "Missing" in result.message

    def test_all_missing_sections_reported(self):
        result = mandatory_sections_exist(_doc("test.md", ""))
        assert not result.passed
        for section in ["User Scenarios", "Constitution Check", "Requirements", "Success Criteria", "Assumptions"]:
            assert section in result.message


class TestNoUnknownSections:
    def test_known_sections_no_warning(self):
        content = (
            "## User Scenarios & Testing\n"
            "## Constitution Check\n"
            "## Requirements\n"
            "## Success Criteria\n"
            "## Assumptions\n"
        )
        result = no_unknown_sections(_doc("test.md", content))
        assert result.passed

    def test_unknown_section_flagged(self):
        content = "## User Scenarios & Testing\n## Unknown Section\n## Requirements\n"
        result = no_unknown_sections(_doc("test.md", content))
        assert not result.passed
        assert "Unknown Section" in result.message
