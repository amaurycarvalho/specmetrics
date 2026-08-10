"""Validation of plugin metadata against platform requirements."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Self

from .plugin_metadata import PluginMetadata, PluginType


@dataclass
class ValidationResult:
    """Outcome of validating a plugin against platform requirements."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


def _parse_semver(version_str: str) -> tuple[int, int, int] | None:
    match = _SEMVER_RE.match(version_str)
    if not match:
        return None
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
    )


_REQUIRED_TEXT_FIELDS = ["id", "api_version"]


class PluginValidator:
    """Validates plugin metadata against platform version requirements."""

    def __init__(self: Self) -> None:
        """Initialize the validator with the installed platform API version."""
        try:
            self._platform_api_version = version("specmetrics")
        except Exception:
            self._platform_api_version = "0.0.0"

    def validate(
        self: Self,
        metadata: PluginMetadata,
        known_plugin_ids: set[str] | None = None,
    ) -> ValidationResult:
        """Validate the given plugin metadata and return the result."""
        errors: list[str] = []

        self._check_required_fields(metadata, errors)
        self._check_api_version(metadata, errors)
        self._check_plugin_type(metadata, errors)
        self._check_handler(metadata, errors)
        self._check_dependencies(metadata, known_plugin_ids, errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @staticmethod
    def _check_required_fields(metadata: PluginMetadata, errors: list[str]) -> None:
        """Append errors for missing or empty required text fields."""
        for field_name in _REQUIRED_TEXT_FIELDS:
            value = getattr(metadata, field_name, None)
            if not value or not isinstance(value, str) or not value.strip():
                errors.append(f"Missing or empty required field: {field_name}")

    def _check_api_version(self: Self, metadata: PluginMetadata, errors: list[str]) -> None:
        """Append errors for unparseable or incompatible API versions."""
        if not metadata.api_version:
            return
        parsed = _parse_semver(metadata.api_version)
        if parsed is None:
            errors.append(f"Unparseable API version: {metadata.api_version}")
            return
        platform_parsed = _parse_semver(self._platform_api_version)
        if platform_parsed is not None and parsed[0] != platform_parsed[0]:
            errors.append(
                f"Incompatible API version: plugin declares {metadata.api_version}, "
                f"platform is {self._platform_api_version} "
                f"(major version mismatch)"
            )

    @staticmethod
    def _check_plugin_type(metadata: PluginMetadata, errors: list[str]) -> None:
        """Append an error when the plugin type is unspecified."""
        if metadata.plugin_type == PluginType.UNSPECIFIED:
            errors.append("Plugin type must be specified")

    @staticmethod
    def _check_handler(metadata: PluginMetadata, errors: list[str]) -> None:
        """Append an error when handlers are declared without a factory."""
        if metadata.handled_event_types and metadata.handler_factory is None:
            errors.append(
                f"Plugin '{metadata.id}' declares handled_event_types "
                f"but no handler_factory"
            )

    @staticmethod
    def _check_dependencies(
        metadata: PluginMetadata,
        known_plugin_ids: set[str] | None,
        errors: list[str],
    ) -> None:
        """Append errors for plugin dependencies missing from known ids."""
        if not metadata.dependencies:
            return
        if known_plugin_ids is None:
            return
        for dep_id in metadata.dependencies:
            if dep_id not in known_plugin_ids:
                errors.append(f"Missing plugin dependency: {dep_id}")
