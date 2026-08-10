"""Entry point based discovery of exporter plugins."""

from __future__ import annotations

from importlib.metadata import entry_points

import structlog

from .base import ExporterPlugin

logger = structlog.get_logger(__name__)


def discover_exporters() -> list[ExporterPlugin]:
    """Return instantiated exporter plugins registered as entry points."""
    plugins: list[ExporterPlugin] = []
    for ep in entry_points(group="specmetrics.exporters"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, ExporterPlugin):
                instance = cls()
                plugins.append(instance)
                logger.debug("exporter_discovered", format_id=instance.format_id())
        except Exception as exc:
            logger.warning(
                "exporter_discovery_failed", entry_point=ep.name, error=str(exc)
            )
    return plugins
