from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ValidationError

from .schema import ConfigWarning


class ConfigValidationError(Exception):
    def __init__(self, message: str, field: str, value: Any, expected_type: str) -> None:
        self.field = field
        self.value = value
        self.expected_type = expected_type
        super().__init__(message)


class ConfigParseError(Exception):
    def __init__(self, message: str, file_path: str, line_number: int | None = None) -> None:
        self.file_path = file_path
        self.line_number = line_number
        super().__init__(message)


class Validator:
    def __init__(self, schema_model: type[BaseModel]) -> None:
        self._schema_model = schema_model

    def validate(self, data: dict[str, Any]) -> BaseModel:
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
        self,
        data: dict[str, Any],
        known_prefixes: list[str] | None = None,
    ) -> list[ConfigWarning]:
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
