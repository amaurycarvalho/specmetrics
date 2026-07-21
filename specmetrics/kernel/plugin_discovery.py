from __future__ import annotations

from importlib.metadata import entry_points

import structlog

from .plugin_metadata import PluginMetadata, PluginStatus
from .plugin_registry import PluginDescriptor, PluginRegistry
from .plugin_validation import PluginValidator

logger = structlog.get_logger(__name__)


class PluginDiscovery:
    def scan(self, group: str = "specmetrics.plugins") -> list[PluginDescriptor]:
        eps = entry_points(group=group)
        descriptors: list[PluginDescriptor] = []
        for ep in eps:
            try:
                factory = ep.load()
                metadata: PluginMetadata = factory()
                descriptor = PluginDescriptor(
                    metadata=metadata,
                    entry_point_name=ep.name,
                    status=PluginStatus.PENDING,
                )
                logger.debug(
                    "plugin_discovered", plugin_id=metadata.id, entry_point=ep.name
                )
                descriptors.append(descriptor)
            except Exception as exc:
                logger.warning(
                    "plugin_skipped",
                    entry_point=ep.name,
                    error=str(exc),
                )
        return descriptors


PLUGIN_GROUPS = [
    "specmetrics.plugins",
    "specmetrics.plugins.measurement",
    "specmetrics.plugins.rule_pack",
    "specmetrics.plugins.stage",
    "specmetrics.plugins.adapter",
    "specmetrics.plugins.semantic",
]


def load_plugins(
    registry: PluginRegistry,
    validator: PluginValidator | None = None,
    group: str | None = None,
) -> PluginRegistry:
    discovery = PluginDiscovery()
    descriptors: list[PluginDescriptor] = []

    groups = [group] if group else PLUGIN_GROUPS
    for g in groups:
        descriptors.extend(discovery.scan(group=g))

    if validator is None:
        validator = PluginValidator()

    known_ids = {d.metadata.id for d in descriptors}

    for descriptor in descriptors:
        try:
            result = validator.validate(descriptor.metadata, known_plugin_ids=known_ids)
            if result.is_valid:
                descriptor.status = PluginStatus.REGISTERED
            else:
                descriptor.status = PluginStatus.REJECTED
                descriptor.validation_errors = result.errors
                logger.warning(
                    "plugin_rejected",
                    plugin_id=descriptor.metadata.id,
                    errors=result.errors,
                )
            registry.register(descriptor)
        except Exception as exc:
            logger.warning(
                "plugin_skipped",
                plugin_id=descriptor.metadata.id,
                error=str(exc),
            )

    return registry
