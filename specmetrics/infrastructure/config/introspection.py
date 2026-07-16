from __future__ import annotations

from typing import Any

from pydantic import SecretStr

from .schema import (
    ConfigurationDump,
    DumpEntry,
    ResolvedConfiguration,
)
from .sources import SourceLevel


def build_dump(config: ResolvedConfiguration) -> ConfigurationDump:
    entries: list[DumpEntry] = []
    for key, prov in config.provenance.items():
        value = _resolve_value(config.values, key)
        is_sensitive = _is_sensitive_value(value)
        entries.append(
            DumpEntry(
                key=key,
                value=_mask_if_sensitive(value, is_sensitive),
                source=prov.source,
                level=prov.level.name.lower(),
                is_default=prov.is_default,
                is_sensitive=is_sensitive,
            )
        )
    if not entries:
        entries = _build_from_model(config.values)
    return ConfigurationDump(
        entries=entries,
        warnings=config.warnings,
        sources_loaded=list({p.source for p in config.provenance.values()}),
    )


def _resolve_value(model: Any, key: str) -> Any:
    parts = key.split(".")
    current = model
    for part in parts:
        if hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


def _is_sensitive_value(value: Any) -> bool:
    return isinstance(value, SecretStr)


def _mask_if_sensitive(value: Any, is_sensitive: bool) -> Any:
    if is_sensitive:
        if isinstance(value, SecretStr):
            return "**********"
        return "**********"
    return value


def _build_from_model(model: Any) -> list[DumpEntry]:
    entries: list[DumpEntry] = []
    _walk_model(model, "", entries)
    return entries


def _walk_model(obj: Any, prefix: str, entries: list[DumpEntry]) -> None:
    cls = obj.__class__ if not isinstance(obj, type) else obj
    if hasattr(cls, "model_fields"):
        for field_name, field_info in cls.model_fields.items():
            full_key = f"{prefix}.{field_name}" if prefix else field_name
            value = getattr(obj, field_name)
            is_sensitive = _is_sensitive_value(value)
            sensitive_extra = field_info.json_schema_extra or {}
            if sensitive_extra.get("sensitive"):
                is_sensitive = True
            entries.append(
                DumpEntry(
                    key=full_key,
                    value=_mask_if_sensitive(value, is_sensitive),
                    source="default",
                    level=SourceLevel.SYSTEM.name.lower(),
                    is_default=True,
                    is_sensitive=is_sensitive,
                )
            )
            if hasattr(value.__class__, "model_fields"):
                _walk_model(value, full_key, entries)
