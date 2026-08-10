"""Rule pack models and loading for the semantic extraction engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field

from ._rule_lib import (
    load_document,
    pick_best_rule,
    raw_load,
    validate_version,
)
from ._rule_parsing import build_rule

logger = structlog.get_logger(__name__)


class RulePackMeta(BaseModel):
    """Metadata describing a rule pack."""

    version: str = Field(default="")
    framework: str = Field(default="")
    document_types: list[str] = Field(default_factory=list)
    description: str = Field(default="")

    @classmethod
    def from_yaml(cls: type[RulePackMeta], data: dict[str, Any]) -> RulePackMeta:
        """Build rule pack metadata from a parsed YAML mapping."""
        return cls(
            version=str(data.get("version", "")),
            framework=str(data.get("framework", "")),
            document_types=list(data.get("document_types", [])),
            description=str(data.get("description", "")),
        )


class ExtractionRule(BaseModel):
    """A single extraction rule with a match pattern and output type."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    pattern: dict[str, Any]
    type: Literal["fact", "entity", "relationship", "operation"]
    confidence: float = Field(ge=0.0, le=1.0)
    priority: int = Field(ge=1, le=100)
    target_sections: list[str] = Field(default_factory=list)
    capture_groups: dict[str, int] = Field(default_factory=dict)
    document_type: str = Field(default="")


class RulePackLoader:
    """Load and validate rule pack YAML files."""

    @staticmethod
    def load_meta(path: str | Path) -> RulePackMeta:
        """Load rule pack metadata from a YAML file."""
        raw = raw_load(path)
        return RulePackMeta.from_yaml(raw)

    @staticmethod
    def validate_version(version: str) -> bool:
        """Return True if the version string matches the expected format."""
        return validate_version(version)

    @staticmethod
    def load(path: str | Path) -> list[ExtractionRule]:
        """Load and validate all extraction rules from a YAML rule pack."""
        loaded = load_document(path)
        if loaded is None:
            return []
        raw, path, version = loaded

        rules = []
        for i, entry in enumerate(raw.get("rules", [])):
            rule = build_rule(entry, i, path)
            if rule is not None:
                rules.append(rule)

        logger.info(
            "rule_pack_loaded",
            path=str(path),
            total_rules=len(raw.get("rules", [])),
            valid_rules=len(rules),
            version=version or "none",
        )
        return rules

    @staticmethod
    def match_rules(
        rules: list[ExtractionRule],
        heading_text: str,
        content: str,
    ) -> ExtractionRule | None:
        """Return the best matching rule for the given heading and content."""
        return pick_best_rule(rules, heading_text, content)