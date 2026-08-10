"""Validation of configuration data against pydantic schemas."""

from __future__ import annotations

from typing import Any, Self

from pydantic import BaseModel, ValidationError

from .schema import ConfigWarning


class ConfigValidationError(Exception):
    """Raised when configuration fails validation."""

    def __init__(
        self: Self, message: str, field: str, value: object, expected_type: str
    ) -> None:
        """Initialize the error with validation details."""
        self.message = message
        self.field = field
        self.value = value
        self.expected_type = expected_type
        super().__init__(message, field, value, expected_type)


class ConfigParseError(Exception):
    """Raised when a configuration file cannot be parsed."""

    def __init__(
        self: Self, message: str, file_path: str, line_number: int | None = None
    ) -> None:
        """Initialize the error with parse details."""
        self.message = message
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(message, file_path, line_number)


class Validator:
    """Validates configuration data against a pydantic schema."""

    def __init__(self: Self, schema_model: type[BaseModel]) -> None:
        """Initialize the validator with the target schema model."""
        self._schema_model = schema_model

    def validate(self: Self, data: dict[str, Any]) -> BaseModel:
        """Validate the data and return the parsed model, or raise on failure."""
        try:
            return self._schema_model.model_validate(data)
        except ValidationError as exc:
            error = exc.errors()[0]
            field_path = ".".join(str(loc) for loc in error["loc"])
            msg = (
                f"Validation error in field '{field_path}': "
                f"got {error.get('input')!r}, expected {error.get('type', 'unknown type')}"
            )
            raise ConfigValidationError(
                message=msg,
                field=field_path,
                value=error.get("input"),
                expected_type=str(error.get("type", "unknown")),
            ) from exc

    def check_unrecognized_keys(
        self: Self,
        data: dict[str, Any],
        known_prefixes: list[str] | None = None,
    ) -> list[ConfigWarning]:
        """Return warnings for configuration keys not recognized by the schema."""
        warnings: list[ConfigWarning] = []
        known = known_prefixes or []
        for key in data:
            parts = key.split(".")
            top_level = parts[0]
            if not hasattr(self._schema_model, top_level) and top_level not in known:
                warnings.append(
                    ConfigWarning(
                        message=f"Unrecognized configuration key: '{key}' — using default value",
                        key=key,
                    )
                )
        return warnings
