from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

try:
    from ruamel.yaml import YAML as YamlLoader

    _yaml = YamlLoader(typ="safe")
except ImportError:
    _yaml = None


_VALID_TYPES = frozenset({"fact", "entity", "relationship", "operation"})

_RE_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


class RulePackMeta(BaseModel):
    version: str = Field(default="")
    framework: str = Field(default="")
    document_types: list[str] = Field(default_factory=list)
    description: str = Field(default="")

    @classmethod
    def from_yaml(cls, data: dict[str, Any]) -> RulePackMeta:
        return cls(
            version=str(data.get("version", "")),
            framework=str(data.get("framework", "")),
            document_types=list(data.get("document_types", [])),
            description=str(data.get("description", "")),
        )


class ExtractionRule(BaseModel):
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
    @staticmethod
    def load_meta(path: str | Path) -> RulePackMeta:
        if _yaml is None:
            raise RuntimeError("ruamel.yaml is required for rule pack loading")
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rule pack not found: {path}")
        with open(path) as f:
            raw = _yaml.load(f)
        return RulePackMeta.from_yaml(raw or {})

    @staticmethod
    def validate_version(version: str) -> bool:
        return bool(_RE_VERSION.match(version))

    @staticmethod
    def load(path: str | Path) -> list[ExtractionRule]:
        if _yaml is None:
            raise RuntimeError("ruamel.yaml is required for rule pack loading")

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Rule pack not found: {path}")

        with open(path) as f:
            raw = _yaml.load(f)

        rules_raw = (raw or {}).get("rules", [])
        if not isinstance(rules_raw, list):
            logger.warning("rule_pack_invalid_format", path=str(path))
            return []

        version = str((raw or {}).get("version", ""))
        if version and not RulePackLoader.validate_version(version):
            logger.warning(
                "rule_pack_invalid_version",
                path=str(path),
                version=version,
            )

        rules: list[ExtractionRule] = []
        for i, entry in enumerate(rules_raw):
            if not isinstance(entry, dict):
                logger.warning("rule_entry_not_dict", path=str(path), index=i)
                continue
            try:
                rid = entry.get("rule_id") or entry.get("id", "")
                if not isinstance(rid, str) or not rid.strip():
                    logger.warning("rule_missing_id", path=str(path), index=i)
                    continue

                rtype = entry.get("semantic_type") or entry.get("type", "")
                if rtype not in _VALID_TYPES:
                    logger.warning(
                        "rule_invalid_type",
                        path=str(path),
                        index=i,
                        type=rtype,
                    )
                    continue

                confidence = entry.get("confidence", 0.0)
                if (
                    not isinstance(confidence, (int, float))
                    or confidence < 0
                    or confidence > 1
                ):
                    logger.warning(
                        "rule_invalid_confidence",
                        path=str(path),
                        index=i,
                        confidence=confidence,
                    )
                    continue

                priority = entry.get("priority", 0)
                if not isinstance(priority, int) or priority < 1 or priority > 100:
                    logger.warning(
                        "rule_invalid_priority",
                        path=str(path),
                        index=i,
                        priority=priority,
                    )
                    continue

                pattern_raw = entry.get("pattern", {})
                if isinstance(pattern_raw, str):
                    pattern: dict[str, Any] = {"regex": pattern_raw}
                elif isinstance(pattern_raw, dict):
                    pattern = pattern_raw
                else:
                    logger.warning(
                        "rule_invalid_pattern",
                        path=str(path),
                        index=i,
                    )
                    continue

                rule = ExtractionRule(
                    id=rid.strip(),
                    name=str(entry.get("name", rid)),
                    pattern=pattern,
                    type=rtype,
                    confidence=float(confidence),
                    priority=int(priority),
                    target_sections=list(entry.get("target_sections", [])),
                    capture_groups=dict(entry.get("capture_groups", {})),
                    document_type=str(entry.get("document_type", "")),
                )
                rules.append(rule)
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "rule_validation_error",
                    path=str(path),
                    index=i,
                    error=str(exc),
                )

        logger.info(
            "rule_pack_loaded",
            path=str(path),
            total_rules=len(rules_raw),
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
        candidates: list[ExtractionRule] = []
        for rule in rules:
            pat = rule.pattern

            heading_match = pat.get("heading", "")
            if heading_match:
                if (
                    isinstance(heading_match, str)
                    and heading_match.lower() == heading_text.lower()
                ):
                    candidates.append(rule)
                elif isinstance(heading_match, list):
                    for h in heading_match:
                        if isinstance(h, str) and h.lower() == heading_text.lower():
                            candidates.append(rule)
                            break
                continue

            keywords = pat.get("keywords", [])
            if keywords:
                min_matches = pat.get("min_matches", len(keywords))
                matched = sum(1 for kw in keywords if kw.lower() in content.lower())
                if matched >= min_matches:
                    candidates.append(rule)
                continue

            structure = pat.get("structure")
            if structure:
                candidates.append(rule)

        if not candidates:
            return None

        candidates.sort(key=lambda r: (-r.priority, r.id))
        return candidates[0]
