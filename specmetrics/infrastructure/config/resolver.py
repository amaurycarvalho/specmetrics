"""Resolution of merged configuration values by source precedence."""

from __future__ import annotations

from typing import Any, Self

from .schema import ConfigWarning, SourceProvenance
from .sources import ConfigurationSource


class ConfigCircularRefError(Exception):
    """Raised when configuration references form a circular dependency."""

    def __init__(self: Self, involved_keys: list[str]) -> None:
        """Initialize the error with the keys forming the reference cycle."""
        self.involved_keys = involved_keys
        keys_str = " -> ".join(involved_keys)
        super().__init__(f"Circular reference detected: {keys_str}")


class Resolver:
    """Merges configuration values from multiple sources by precedence."""

    def __init__(self: Self) -> None:
        """Initialize the resolver with an empty raw value registry."""
        self._raw: dict[str, tuple[Any, ConfigurationSource]] = {}

    def add_source(self: Self, source: ConfigurationSource, data: dict[str, Any]) -> None:
        """Add source data, keeping the highest-precedence value per key."""
        for key, value in data.items():
            existing = self._raw.get(key)
            if existing is None or source.precedence > existing[1].precedence:
                self._raw[key] = (value, source)

    def resolve(
        self: Self,
    ) -> tuple[dict[str, Any], dict[str, SourceProvenance], list[ConfigWarning]]:
        """Resolve merged values into a flat mapping with provenance."""
        resolved: dict[str, Any] = {}
        provenance: dict[str, SourceProvenance] = {}
        warnings: list[ConfigWarning] = []

        self._detect_circular_refs()

        for key, (value, source) in self._raw.items():
            resolved[key] = value
            provenance[key] = SourceProvenance(
                key=key,
                source=source.name,
                level=source.precedence,
                is_default=False,
            )

        return resolved, provenance, warnings

    def _detect_circular_refs(self: Self) -> None:
        """Raise if environment variable references contain a cycle."""
        env_values: dict[str, str] = {}
        for key, (value, _source) in self._raw.items():
            if isinstance(value, str):
                env_values[key] = value

        visited: set[str] = set()
        in_stack: set[str] = set()

        def dfs(key: str, path: list[str]) -> None:
            if key in in_stack:
                cycle = path[path.index(key) :] + [key]
                raise ConfigCircularRefError(cycle)
            if key in visited:
                return
            visited.add(key)
            in_stack.add(key)
            path.append(key)

            value = env_values.get(key, "")
            refs = _extract_refs(value)
            for ref in refs:
                if ref in env_values:
                    dfs(ref, path)

            path.pop()
            in_stack.discard(key)

        for key in env_values:
            if key not in visited:
                dfs(key, [])


def _extract_refs(value: str) -> list[str]:
    """Extract ``${KEY}`` references from a string value."""
    refs: list[str] = []
    parts = value.split("${")
    for part in parts[1:]:
        ref_key = part.split("}")[0]
        if ref_key:
            refs.append(ref_key)
    return refs
