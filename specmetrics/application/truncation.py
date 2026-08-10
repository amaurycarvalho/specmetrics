"""Reusable helpers for truncating text and entity payloads during result assembly.

Moved verbatim from ``specmetrics.application.orchestrator`` as part of the
orchestrator maintainability refactor (FR-003). This module has no dependencies
on other application units.
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)

_TRUNCATE_TEXT_LENGTH = 200


def _truncate_text(
    text: str | None, max_len: int = _TRUNCATE_TEXT_LENGTH
) -> str | None:
    if text is None:
        return None
    return text[:max_len] if len(text) > max_len else text


def _truncate_entities(
    entities: list[dict],
    max_per_stage: int,
    per_category: bool = False,
) -> list[dict]:
    if len(entities) <= max_per_stage:
        return entities
    logger.info(
        "entities_truncated",
        total=len(entities),
        limit=max_per_stage,
        per_category=per_category,
    )
    if per_category:
        truncated: list[dict] = []
        categories: dict[str, list[dict]] = {}
        for e in entities:
            cat = e.get("type", "_other")
            categories.setdefault(cat, []).append(e)
        for cat_list in categories.values():
            truncated.extend(cat_list[:max_per_stage])
        truncated.append({"_truncated": True, "_total_count": len(entities)})
        return truncated
    truncated = entities[:max_per_stage]
    truncated.append({"_truncated": True, "_total_count": len(entities)})
    return truncated