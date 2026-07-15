from __future__ import annotations

from importlib.metadata import entry_points

import structlog

from .base import PublisherPlugin

logger = structlog.get_logger(__name__)


def discover_publishers() -> list[PublisherPlugin]:
    plugins: list[PublisherPlugin] = []
    for ep in entry_points(group="specmetrics.publishers"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, PublisherPlugin):
                instance = cls()
                plugins.append(instance)
                logger.debug(
                    "publisher_discovered", publisher_id=instance.publisher_id()
                )
        except Exception as exc:
            logger.warning(
                "publisher_discovery_failed", entry_point=ep.name, error=str(exc)
            )
    return plugins
