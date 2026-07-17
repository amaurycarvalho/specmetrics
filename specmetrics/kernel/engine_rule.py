from __future__ import annotations

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


class ExtractionRule(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    pattern: dict[str, Any]
    type: Literal["fact", "entity", "relationship", "operation"]
    confidence: float = Field(ge=0.0, le=1.0)
    priority: int = Field(ge=1, le=100)


class RulePackLoader:
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

        rules: list[ExtractionRule] = []
        for i, entry in enumerate(rules_raw):
            if not isinstance(entry, dict):
                logger.warning("rule_entry_not_dict", path=str(path), index=i)
                continue
            try:
                rid = entry.get("id", "")
                if not isinstance(rid, str) or not rid.strip():
                    logger.warning("rule_missing_id", path=str(path), index=i)
                    continue

                rtype = entry.get("type", "")
                if rtype not in _VALID_TYPES:
                    logger.warning(
                        "rule_invalid_type",
                        path=str(path),
                        index=i,
                        type=rtype,
                    )
                    continue

                confidence = entry.get("confidence", 0.0)
                if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
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

                pattern = entry.get("pattern", {})
                if not isinstance(pattern, dict) or not (
                    "keywords" in pattern or "heading" in pattern or "structure" in pattern
                ):
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
                if isinstance(heading_match, str) and heading_match.lower() == heading_text.lower():
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
