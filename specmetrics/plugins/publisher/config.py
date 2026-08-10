"""Loading of publisher configuration from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
from ruamel.yaml import YAML

from .base import PublisherConfiguration

logger = structlog.get_logger(__name__)

yaml = YAML(typ="safe")


def load_publisher_configs(config_path: Path | str) -> list[PublisherConfiguration]:
    """Load publisher configurations from the given YAML config file."""
    path = Path(config_path)
    if not path.exists():
        logger.warning("publisher_config_not_found", path=str(path))
        return []

    with open(path) as f:
        data: dict[str, Any] = yaml.load(f)

    endpoints = data.get("publisher", {}).get("endpoints", [])
    if not isinstance(endpoints, list):
        logger.warning("invalid_publisher_config_structure", path=str(path))
        return []

    configs: list[PublisherConfiguration] = []
    errors: list[str] = []

    for i, ep in enumerate(endpoints):
        if not isinstance(ep, dict):
            errors.append(f"endpoint[{i}]: expected a mapping, got {type(ep).__name__}")
            continue
        try:
            cfg = PublisherConfiguration(**ep)
            configs.append(cfg)
        except Exception as exc:
            errors.append(f"endpoint[{i}]: {exc}")

    if errors:
        for err in errors:
            logger.error("publisher_config_error", detail=err)
        from .base import PublisherConfigError

        raise PublisherConfigError("\n".join(errors))

    enabled = [c for c in configs if c.enabled]
    logger.info("publisher_configs_loaded", total=len(configs), enabled=len(enabled))
    return configs
