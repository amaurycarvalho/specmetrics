from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from specmetrics.kernel.validation._loader import load_spec_document


def test_load_spec_document_reads_utf8_file(tmp_path):
    """Kills load_spec_document__mutmut_2/4 (read_text must use the utf-8 encoding)."""
    path = tmp_path / "spec.md"
    path.write_text("café\n", encoding="utf-8")
    with patch("pathlib.Path.read_text", return_value="café\n") as read_text:
        doc = load_spec_document(path)
    read_text.assert_called_once_with(encoding="utf-8")
    assert doc.content == "café\n"
    assert doc.line_count == 1


def test_load_spec_document_success_fields(tmp_path):
    """Kills load_spec_document__mutmut_12/13/40/42/44/46 (path, size_bytes, line_count fields)."""
    path = tmp_path / "spec.md"
    path.write_text("line1\nline2\nline3\n", encoding="utf-8")
    doc = load_spec_document(path)
    assert doc.content == "line1\nline2\nline3\n"
    assert doc.path == path
    assert doc.size_bytes == os.path.getsize(path)
    assert doc.line_count == 3


def test_load_spec_document_missing_file_result(tmp_path):
    """Kills load_spec_document__mutmut_14/15/16/17/18/19/20/21/22/23/24/25/26 (file-not-found result)."""
    path = tmp_path / "missing.md"
    result = load_spec_document(path)
    assert result.rule_name == "file-readable"
    assert result.passed is False
    assert result.message == f"File not found: {path}"
    assert result.severity == "ERROR"


def test_load_spec_document_permission_error_result():
    """Kills load_spec_document__mutmut_27/28/29/30/31/32/33/34/35/36/37/38/39 (permission-denied result)."""
    path = MagicMock()
    path.read_text.side_effect = PermissionError("denied")
    result = load_spec_document(path)
    assert result.rule_name == "file-readable"
    assert result.passed is False
    assert result.message == f"Permission denied: {path}"
    assert result.severity == "ERROR"


def test_load_spec_document_unicode_error_returns_empty_document(tmp_path):
    """Kills load_spec_document__mutmut_41/43/45/47/48/49 (unicode-decode fallback document)."""
    path = tmp_path / "spec.md"
    path.write_bytes(b"\xff\xfe")
    with patch(
        "pathlib.Path.read_text",
        side_effect=UnicodeDecodeError(
            "utf-8", b"\xff\xfe", 0, 2, "invalid start byte"
        ),
    ):
        doc = load_spec_document(path)
    assert doc.path == path
    assert doc.content == ""
    assert doc.size_bytes == 2
    assert doc.line_count == 0


def test_load_spec_document_os_error_result():
    """Kills load_spec_document__mutmut_50/51/52/53/54/55/56/57/58/59/60/61/62 (cannot-read result)."""
    exc = OSError("boom")
    path = MagicMock()
    path.read_text.side_effect = exc
    result = load_spec_document(path)
    assert result.rule_name == "file-readable"
    assert result.passed is False
    assert result.message == f"Cannot read file {path}: {exc}"
    assert result.severity == "ERROR"
