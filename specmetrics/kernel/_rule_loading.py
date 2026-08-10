"""Rule pack loading and merging for the deterministic extraction engine."""

from __future__ import annotations

from pathlib import Path
from typing import Self

import structlog

from .engine_rule import ExtractionRule, RulePackLoader

logger = structlog.get_logger(__name__)

_EXPECTED_RULE_PACK_MAJOR_VERSION = 1


def _parse_major_version(version: str) -> int | None:
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError):
        return None


class RuleLoadingMixin:
    """Provide rule pack loading and conflict resolution for the engine."""

    _default_rule_pack: str | None
    _extra_rule_packs: list[str]

    def _load_rules(self: Self) -> list[ExtractionRule]:
        result, conflict_count = self._merge_rule_packs(self._collect_rule_packs())
        logger.info(
            "rules_loaded",
            total_rules=len(result),
            conflicts_detected=conflict_count,
        )
        return result

    def _collect_rule_packs(self: Self) -> list[list[ExtractionRule]]:
        from pathlib import Path

        packs: list[list[ExtractionRule]] = []
        default_path = self._default_rule_pack
        if default_path is None:
            default_path = str(Path(__file__).parent / "rules" / "default_rule_pack.yaml")
        self._load_pack_safely(packs, default_path)
        for extra in self._extra_rule_packs:
            self._load_pack_safely(packs, extra, log_path=extra)
        return packs

    def _load_pack_safely(
        self: Self,
        packs: list[list[ExtractionRule]],
        path: str,
        log_path: str | None = None,
    ) -> None:
        try:
            packs.append(RulePackLoader.load(path))
        except (FileNotFoundError, RuntimeError) as exc:
            if log_path is None:
                logger.warning("default_rule_pack_not_loaded", error=str(exc))
            else:
                logger.warning(
                    "extra_rule_pack_not_loaded", path=log_path, error=str(exc)
                )

    def _merge_rule_packs(
        self: Self, packs: list[list[ExtractionRule]]
    ) -> tuple[list[ExtractionRule], int]:
        merged: dict[str, ExtractionRule] = {}
        conflict_count = 0
        for pack in packs:
            for rule in pack:
                existing = merged.get(rule.id)
                if existing is None:
                    merged[rule.id] = rule
                else:
                    conflict_count += 1
                    self._resolve_rule_conflict(merged, rule, existing)
        return sorted(merged.values(), key=lambda r: (-r.priority, r.id)), conflict_count

    def _resolve_rule_conflict(
        self: Self,
        merged: dict[str, ExtractionRule],
        rule: ExtractionRule,
        existing: ExtractionRule,
    ) -> None:
        if rule.priority > existing.priority:
            logger.info(
                "rule_conflict_resolved",
                rule_id=rule.id,
                winner=rule.name,
                winner_priority=rule.priority,
                loser_priority=existing.priority,
            )
            merged[rule.id] = rule
        elif rule.priority == existing.priority and rule.id < existing.id:
            merged[rule.id] = rule

    def _check_pack_version(self: Self, path: str | Path) -> None:
        try:
            meta = RulePackLoader.load_meta(path)
            if meta.version:
                if not RulePackLoader.validate_version(meta.version):
                    logger.warning(
                        "rule_pack_invalid_version",
                        path=str(path),
                        version=meta.version,
                    )
                else:
                    major = _parse_major_version(meta.version)
                    if major is not None and major != _EXPECTED_RULE_PACK_MAJOR_VERSION:
                        logger.warning(
                            "rule_pack_major_version_mismatch",
                            path=str(path),
                            version=meta.version,
                            expected_major=_EXPECTED_RULE_PACK_MAJOR_VERSION,
                        )
        except (FileNotFoundError, RuntimeError) as exc:
            logger.warning(
                "rule_pack_version_check_failed", path=str(path), error=str(exc)
            )