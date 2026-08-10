"""Tests for specmetrics.mcp._params parameter validation helpers."""

from __future__ import annotations

import pytest

from specmetrics.mcp._params import (
    check_param_schemas,
    check_param_value,
    check_required_params,
)
from specmetrics.mcp._support import ToolError


class TestCheckRequiredParams:
    def test_missing_required_raises(self) -> None:
        with pytest.raises(ToolError) as exc:
            check_required_params(["a", "b"], {"a": 1}, {"a": {}, "b": {}})
        assert exc.value.code == -32602
        assert "b" in exc.value.message
        assert exc.value.details["field"] == "b"

    def test_none_required_raises(self) -> None:
        with pytest.raises(ToolError):
            check_required_params(["a"], {"a": None}, {"a": {}})

    def test_all_present_passes(self) -> None:
        check_required_params(["a", "b"], {"a": 1, "b": 2}, {"a": {}, "b": {}})

    def test_empty_required_list_passes(self) -> None:
        check_required_params([], {}, {})


class TestCheckParamValue:
    def test_enum_violation_raises(self) -> None:
        with pytest.raises(ToolError) as exc:
            check_param_value("format", "xml", {"enum": ["json", "csv"]})
        assert exc.value.code == -32602
        assert exc.value.details["expected"] == ["json", "csv"]

    def test_valid_enum_passes(self) -> None:
        check_param_value("format", "json", {"enum": ["json", "csv"]})

    def test_wrong_type_raises(self) -> None:
        with pytest.raises(ToolError) as exc:
            check_param_value("path", 42, {"type": "string"})
        assert exc.value.details["expected_type"] == "string"
        assert exc.value.details["received_type"] == "int"

    def test_valid_string_passes(self) -> None:
        check_param_value("path", "/tmp/x", {"type": "string"})

    def test_untyped_value_passes(self) -> None:
        check_param_value("anything", object(), {})


class TestCheckParamSchemas:
    def test_unknown_param_raises(self) -> None:
        with pytest.raises(ToolError) as exc:
            check_param_schemas({"nope": 1}, {"known": {}})
        assert exc.value.code == -32602
        assert exc.value.details["valid_params"] == ["known"]

    def test_known_params_pass(self) -> None:
        check_param_schemas({"format": "json"}, {"format": {"enum": ["json", "csv"]}})

    def test_violating_known_param_raises(self) -> None:
        with pytest.raises(ToolError):
            check_param_schemas({"format": "xml"}, {"format": {"enum": ["json", "csv"]}})  # type: ignore[arg-type]

    def test_empty_params_passes(self) -> None:
        check_param_schemas({}, {"anything": {}})