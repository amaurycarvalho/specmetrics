from __future__ import annotations

import pytest
from structlog.testing import capture_logs

from specmetrics.kernel import _rule_lib


def _write_pack(tmp_path, content: str, name: str = "pack.yaml"):
    path = tmp_path / name
    path.write_text(content)
    return path


def test_raw_load_requires_ruamel(monkeypatch):
    """Kills raw_load__mutmut_2/3/4 (RuntimeError message when ruamel.yaml is unavailable)."""
    monkeypatch.setattr(_rule_lib, "_yaml", None)
    with pytest.raises(RuntimeError) as excinfo:
        _rule_lib.raw_load("x.yaml")
    assert str(excinfo.value) == "ruamel.yaml is required for rule pack loading"


def test_load_document_requires_ruamel(monkeypatch):
    """Kills load_document__mutmut_2/3/4 (RuntimeError message when ruamel.yaml is unavailable)."""
    monkeypatch.setattr(_rule_lib, "_yaml", None)
    with pytest.raises(RuntimeError) as excinfo:
        _rule_lib.load_document("x.yaml")
    assert str(excinfo.value) == "ruamel.yaml is required for rule pack loading"


def test_raw_load_missing_file_raises_file_not_found():
    """Kills raw_load__mutmut_8 (FileNotFoundError message must include the path)."""
    with pytest.raises(FileNotFoundError) as excinfo:
        _rule_lib.raw_load("/nonexistent/rules.yaml")
    assert str(excinfo.value) == "Rule pack not found: /nonexistent/rules.yaml"


def test_load_document_missing_file_raises_file_not_found():
    """Kills load_document__mutmut_8 (FileNotFoundError message must include the path)."""
    with pytest.raises(FileNotFoundError) as excinfo:
        _rule_lib.load_document("/nonexistent/rules.yaml")
    assert str(excinfo.value) == "Rule pack not found: /nonexistent/rules.yaml"


def test_load_document_version_defaults_to_empty(tmp_path):
    """Kills load_document__mutmut_14/15 (missing version must default to empty string)."""
    path = _write_pack(tmp_path, "rules: []\n")
    raw, _loaded_path, version = _rule_lib.load_document(path)
    assert version == ""
    assert raw == {"rules": []}


def test_load_document_valid_version_no_warning(tmp_path):
    """Kills load_document__mutmut_24 (valid version must not log a warning)."""
    path = _write_pack(tmp_path, "version: 1.2.3\nrules: []\n")
    with capture_logs() as logs:
        _rule_lib.load_document(path)
    assert logs == []


def test_load_document_empty_version_no_warning(tmp_path):
    """Kills load_document__mutmut_23 (empty version must not log a warning)."""
    path = _write_pack(tmp_path, "rules: []\n")
    with capture_logs() as logs:
        _rule_lib.load_document(path)
    assert logs == []


def test_load_document_invalid_version_logs_context(tmp_path):
    """Kills load_document__mutmut_27/28/29/30/31/34 (invalid version warning event, path, version)."""
    path = _write_pack(tmp_path, "version: abc\nrules: []\n")
    with capture_logs() as logs:
        _raw, _loaded_path, version = _rule_lib.load_document(path)
    assert version == "abc"
    assert logs[0]["event"] == "rule_pack_invalid_version"
    assert logs[0]["path"] == str(path)
    assert logs[0]["version"] == "abc"
