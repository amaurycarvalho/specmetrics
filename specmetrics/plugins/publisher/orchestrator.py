"""Coordination of publisher plugins for a pipeline run."""

from __future__ import annotations

import structlog

from specmetrics.plugins.exporter.models import ExportMetadata, Measurement

from .base import PublisherConfig, PublisherConfiguration
from .discovery import discover_publishers

logger = structlog.get_logger(__name__)


def publish_all(
    measurements: list[Measurement],
    metadata: ExportMetadata,
    configs: dict[str, PublisherConfig] | None = None,
    publisher_configs: list[PublisherConfiguration] | None = None,
) -> list[dict]:
    """Publish measurements through every discovered publisher plugin."""
    configs = configs or {}
    publishers = discover_publishers()
    results: list[dict] = []

    for pub in publishers:
        pid = pub.publisher_id()
        cfg = configs.get(pid, PublisherConfig())

        if publisher_configs and hasattr(pub, "initialize"):
            try:
                pub.initialize(publisher_configs)  # type: ignore[union-attr]
                pub.start()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning(
                    "publisher_initialize_failed", publisher=pid, error=str(exc)
                )

        try:
            result = pub.publish(measurements, metadata, cfg)
            if result.success:
                logger.info(
                    "publish_succeeded", publisher=pid, metrics=result.metrics_count
                )
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

        if hasattr(pub, "stop"):
            try:
                pub.stop()  # type: ignore[union-attr]
            except Exception as exc:
                logger.warning("publisher_stop_failed", publisher=pid, error=str(exc))

    return results
