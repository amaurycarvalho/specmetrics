"""Load rule pack definitions from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Self

import structlog
from ruamel.yaml import YAML

from specmetrics.kernel.cfm.models import FileLoadResult, Rule, RuleConfig, RulePack

yaml = YAML(typ="safe")
logger = structlog.get_logger(__name__)

GSC_KEYS: list[str] = [
    "data_communications",
    "distributed_data_processing",
    "performance",
    "heavily_used_configuration",
    "transaction_rate",
    "online_data_entry",
    "end_user_efficiency",
    "online_update",
    "complex_processing",
    "reusability",
    "installation_ease",
    "operational_ease",
    "multiple_sites",
    "facilitate_change",
]


class RulePackLoader:
    """Loads rule pack definitions from a rules directory."""

    def __init__(self: Self, rules_dir: str = ".specmetrics/rules") -> None:
        """Initialize the loader with the rules directory."""
        self._rules_dir = Path(rules_dir)

    def discover_files(self: Self) -> list[Path]:
        """Return the YAML rule pack files in the rules directory."""
        if not self._rules_dir.is_dir():
            logger.info("rule_pack_dir_not_found", path=str(self._rules_dir))
            return []
        files = sorted(self._rules_dir.glob("*.yml"))
        logger.info(
            "rule_pack_files_discovered", count=len(files), path=str(self._rules_dir)
        )
        return files

    def load_file(self: Self, file_path: Path) -> tuple[RulePack | None, FileLoadResult]:
        """Load a single rule pack file and return the pack and load result."""
        result = FileLoadResult(file_path=str(file_path))
        try:
            raw = yaml.load(file_path)
        except Exception as exc:
            result.status = "error"
            result.error = f"Invalid YAML in {file_path.name}: {exc}"
            logger.error("rule_pack_parse_error", file=str(file_path), error=str(exc))
            return None, result

        if not isinstance(raw, dict):
            result.status = "error"
            result.error = f"File {file_path.name} must contain a mapping at root"
            return None, result

        pack_id = raw.get("id")
        if not pack_id or not isinstance(pack_id, str):
            result.status = "error"
            result.error = f"File {file_path.name} is missing required 'id' field"
            return None, result

        rule_pack = RulePack(
            id=pack_id,
            description=raw.get("description", ""),
            methodology=raw.get("methodology", "FPA"),
            glossary_overrides=raw.get("glossary_overrides", {}),
        )

        raw_rules = raw.get("rules")
        if raw_rules and isinstance(raw_rules, list):
            for r in raw_rules:
                config_data = r.get("config", {})
                if isinstance(config_data, dict):
                    rule_config = RuleConfig(**config_data)
                else:
                    rule_config = RuleConfig()
                rule = Rule(
                    id=r.get("id", ""),
                    type=r.get("type", ""),
                    description=r.get("description", ""),
                    config=rule_config,
                )
                rule_pack.rules.append(rule)

        result.rule_pack_id = pack_id
        result.rules_count = len(rule_pack.rules)
        result.status = "loaded"
        return rule_pack, result

    def load_all(self: Self) -> list[tuple[RulePack | None, FileLoadResult]]:
        """Load all discovered rule pack files."""
        files = self.discover_files()
        if not files:
            return []
        results: list[tuple[RulePack | None, FileLoadResult]] = []
        for fpath in files:
            pack, result = self.load_file(fpath)
            results.append((pack, result))
        return results
