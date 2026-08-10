"""Tool parameter validation helpers for the MCP server."""

from __future__ import annotations

from ._support import ToolError


def check_required_params(required: list, params: dict, properties: dict) -> None:
    """Raise on missing required parameters."""
    for field in required:
        if field not in params or params[field] is None:
            raise ToolError(
                -32602,
                f"Missing required parameter: {field}",
                {"field": field, "expected": properties.get(field, {})},
            )


def check_param_value(field: str, value: object, prop: dict) -> None:
    """Raise on a parameter whose value violates the property schema."""
    if "enum" in prop and value not in prop["enum"]:
        raise ToolError(
            -32602,
            f"Invalid value for {field}: {value}",
            {"field": field, "value": value, "expected": prop["enum"]},
        )
    if prop.get("type") == "string" and not isinstance(value, str):
        raise ToolError(
            -32602,
            f"Invalid type for {field}: expected string, got {type(value).__name__}",
            {
                "field": field,
                "expected_type": "string",
                "received_type": type(value).__name__,
            },
        )


def check_param_schemas(params: dict, properties: dict) -> None:
    """Raise on unknown or schema-violating parameters."""
    for field, value in params.items():
        if field not in properties:
            raise ToolError(
                -32602,
                f"Unknown parameter: {field}",
                {"field": field, "valid_params": list(properties.keys())},
            )
        check_param_value(field, value, properties[field])