"""Low-level loading and matching helpers for rule packs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from .engine_rule import ExtractionRule

logger = structlog.get_logger(__name__)

try:
    from ruamel.yaml import YAML as YamlLoader

    _yaml = YamlLoader(typ="safe")
except ImportError:
    _yaml = None

_RE_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def validate_version(version: str) -> bool:
    """Return True if the version string matches the expected format."""
    return bool(_RE_VERSION.match(version))


def raw_load(path: str | Path) -> dict[str, Any]:
    """Load a rule pack YAML file and return its mapping."""
    if _yaml is None:
        raise RuntimeError("ruamel.yaml is required for rule pack loading")

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rule pack not found: {path}")

    with open(path) as f:
        raw = _yaml.load(f)

    return raw or {}


def load_document(
    path: str | Path,
) -> tuple[dict[str, Any], Path, str] | None:
    """Load and return (raw_mapping, path, version) from a YAML rule pack."""
    if _yaml is None:
        raise RuntimeError("ruamel.yaml is required for rule pack loading")

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rule pack not found: {path}")

    with open(path) as f:
        raw = _yaml.load(f)

    raw = raw or {}
    version = str(raw.get("version", ""))
    if version and not validate_version(version):
        logger.warning(
            "rule_pack_invalid_version",
            path=str(path),
            version=version,
        )
    return raw, path, version


def heading_matches(rule: ExtractionRule, heading_text: str) -> bool:
    """Return whether the rule's heading pattern matches the given heading."""
    heading_match = rule.pattern.get("heading", "")
    if isinstance(heading_match, str):
        return heading_match.lower() == heading_text.lower()
    if isinstance(heading_match, list):
        return any(
            isinstance(h, str) and h.lower() == heading_text.lower()
            for h in heading_match
        )
    return False


def keyword_matches(rule: ExtractionRule, content: str) -> bool:
    """Return whether the rule's keywords match the given content."""
    keywords = rule.pattern.get("keywords", [])
    min_matches = rule.pattern.get("min_matches", len(keywords))
    matched = sum(1 for kw in keywords if kw.lower() in content.lower())
    return matched >= min_matches


def pick_best_rule(
    rules: list[ExtractionRule], heading_text: str, content: str
) -> ExtractionRule | None:
    """Return the best matching rule for the given heading and content."""
    candidates: list[ExtractionRule] = []
    for rule in rules:
        pat = rule.pattern
        if pat.get("heading", ""):
            if heading_matches(rule, heading_text):
                candidates.append(rule)
            continue
        if pat.get("keywords", []):
            if keyword_matches(rule, content):
                candidates.append(rule)
            continue
        if pat.get("structure"):
            candidates.append(rule)

    if not candidates:
        return None

    candidates.sort(key=lambda r: (-r.priority, r.id))
    return candidates[0]