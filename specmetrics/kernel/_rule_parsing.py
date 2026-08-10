"""Rule entry validation and construction helpers for rule packs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from pydantic import ValidationError

logger = structlog.get_logger(__name__)

_VALID_TYPES = frozenset({"fact", "entity", "relationship", "operation"})


def build_rule(entry: dict[str, Any], index: int, path: Path) -> Any | None:
    """Build an ExtractionRule from a raw entry mapping, or None if invalid."""
    if not isinstance(entry, dict):
        logger.warning("rule_entry_not_dict", path=str(path), index=index)
        return None

    rid = _validated_rid(entry, index, path)
    rtype = _validated_type(entry, index, path)
    confidence = _validated_confidence(entry, index, path)
    priority = _validated_priority(entry, index, path)
    pattern = _pattern_from(entry, index, path)

    if None in (rid, rtype, confidence, priority, pattern):
        return None

    try:
        from .engine_rule import ExtractionRule

        return ExtractionRule(
            id=rid,
            name=str(entry.get("name", rid)),
            pattern=pattern,
            type=rtype,
            confidence=confidence,
            priority=priority,
            target_sections=list(entry.get("target_sections", [])),
            capture_groups=dict(entry.get("capture_groups", {})),
            document_type=str(entry.get("document_type", "")),
        )
    except (ValidationError, ValueError, TypeError) as exc:
        logger.warning(
            "rule_validation_error",
            path=str(path),
            index=index,
            error=str(exc),
        )
        return None


def _validated_rid(
    entry: dict[str, Any], index: int, path: Path
) -> str | None:
    rid = entry.get("rule_id") or entry.get("id", "")
    ok = isinstance(rid, str) and bool(rid.strip())
    if not ok:
        logger.warning("rule_missing_id", path=str(path), index=index)
        return None
    return rid.strip()


def _validated_type(
    entry: dict[str, Any], index: int, path: Path
) -> str | None:
    rtype = entry.get("semantic_type") or entry.get("type", "")
    if rtype not in _VALID_TYPES:
        logger.warning(
            "rule_invalid_type", path=str(path), index=index, type=rtype
        )
        return None
    return rtype


def _validated_confidence(
    entry: dict[str, Any], index: int, path: Path
) -> float | None:
    confidence = entry.get("confidence", 0.0)
    ok = (
        isinstance(confidence, (int, float))
        and confidence >= 0
        and confidence <= 1
    )
    if not ok:
        logger.warning(
            "rule_invalid_confidence",
            path=str(path),
            index=index,
            confidence=confidence,
        )
        return None
    return float(confidence)


def _validated_priority(
    entry: dict[str, Any], index: int, path: Path
) -> int | None:
    priority = entry.get("priority", 0)
    ok = isinstance(priority, int) and priority >= 1 and priority <= 100
    if not ok:
        logger.warning(
            "rule_invalid_priority",
            path=str(path),
            index=index,
            priority=priority,
        )
        return None
    return int(priority)


def _pattern_from(
    entry: dict[str, Any], index: int, path: Path
) -> dict[str, Any] | None:
    pattern_raw = entry.get("pattern", {})
    if isinstance(pattern_raw, str):
        return {"regex": pattern_raw}
    if isinstance(pattern_raw, dict):
        return pattern_raw
    logger.warning("rule_invalid_pattern", path=str(path), index=index)
    return None