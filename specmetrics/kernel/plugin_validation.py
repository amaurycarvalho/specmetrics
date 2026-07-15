from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib.metadata import version

from .plugin_metadata import PluginMetadata, PluginType


@dataclass
class ValidationResult:
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
    return (int(match.group("major")), int(match.group("minor")), int(match.group("patch")))


_REQUIRED_TEXT_FIELDS = ["id", "api_version"]


class PluginValidator:
    def __init__(self) -> None:
        try:
            self._platform_api_version = version("specmetrics")
        except Exception:
            self._platform_api_version = "0.0.0"

    def validate(self, metadata: PluginMetadata) -> ValidationResult:
        errors: list[str] = []

        for field_name in _REQUIRED_TEXT_FIELDS:
            value = getattr(metadata, field_name, None)
            if not value or not isinstance(value, str) or not value.strip():
                errors.append(f"Missing or empty required field: {field_name}")

        if metadata.api_version:
            parsed = _parse_semver(metadata.api_version)
            if parsed is None:
                errors.append(f"Unparseable API version: {metadata.api_version}")
            else:
                platform_parsed = _parse_semver(self._platform_api_version)
                if platform_parsed is not None and parsed[0] != platform_parsed[0]:
                    errors.append(
                        f"Incompatible API version: plugin declares {metadata.api_version}, "
                        f"platform is {self._platform_api_version} "
                        f"(major version mismatch)"
                    )

        if metadata.plugin_type == PluginType.UNSPECIFIED:
            errors.append("Plugin type must be specified")

        if metadata.handled_event_types and metadata.handler_factory is None:
            errors.append(
                f"Plugin '{metadata.id}' declares handled_event_types "
                f"but no handler_factory"
            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
