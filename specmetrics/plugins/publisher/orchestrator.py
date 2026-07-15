from __future__ import annotations

from importlib.metadata import entry_points

import structlog

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement

from .base import PublisherConfig, PublisherPlugin

logger = structlog.get_logger(__name__)


def discover_publishers() -> list[PublisherPlugin]:
    publishers: list[PublisherPlugin] = []
    for ep in entry_points(group="specmetrics.publishers"):
        try:
            cls = ep.load()
            if isinstance(cls, type) and issubclass(cls, PublisherPlugin):
                publishers.append(cls())
        except Exception as exc:
            logger.warning("publisher_load_failed", entry_point=ep.name, error=str(exc))
    return publishers


def publish_all(
    measurements: list[Measurement],
    metadata: ExportMetadata,
    configs: dict[str, PublisherConfig] | None = None,
) -> list[dict]:
    configs = configs or {}
    publishers = discover_publishers()
    results: list[dict] = []

    for pub in publishers:
        pid = pub.publisher_id()
        cfg = configs.get(pid, PublisherConfig())
        try:
            result = pub.publish(measurements, metadata, cfg)
            if result.success:
                logger.info("publish_succeeded", publisher=pid, metrics=result.metrics_count)
            else:
                logger.warning("publish_failed", publisher=pid, message=result.message)
            results.append(
                {
                    "publisher": pid,
                    "success": result.success,
                    "message": result.message,
                    "metrics_count": result.metrics_count,
                }
            )
        except Exception as exc:
            logger.error("publish_error", publisher=pid, error=str(exc))
            results.append(
                {
                    "publisher": pid,
                    "success": False,
                    "message": str(exc),
                    "metrics_count": 0,
                }
            )

    return results
