from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

import structlog

from .extraction_provider import ExtractionProvider

if TYPE_CHECKING:
    from .plugin_registry import PluginRegistry

logger = structlog.get_logger(__name__)

try:
    from ruamel.yaml import YAML as YamlLoader

    _yaml = YamlLoader(typ="safe")
except ImportError:
    _yaml = None


def load_routing_config(
    path: str | Path,
    provider_map: dict[str, ExtractionProvider],
    router: Optional[ProviderRouter] = None,
) -> ProviderRouter:
    """Load provider routing configuration from a YAML file.

    Expects the following structure:

    .. code-block:: yaml

        extraction:
          routing:
            "use_case": "my-provider"
            "business_rule": "my-provider"
            "*": "llm-provider"

    The ``*`` key registers a default (catch-all) provider.
    Returns a new ``ProviderRouter`` if *router* is ``None``, otherwise
    populates the given instance.
    """
    if _yaml is None:
        raise RuntimeError("ruamel.yaml is required for config loading")

    result = router or ProviderRouter()

    with open(path) as f:
        config = _yaml.load(f)

    routing = (config or {}).get("extraction", {}).get("routing", {})
    for doc_type, provider_id in routing.items():
        provider = provider_map.get(provider_id)
        if provider is None:
            logger.warning("provider_not_found_in_map", provider_id=provider_id)
            continue
        if doc_type == "*":
            result.register(provider, provider_id)
        else:
            result.register(provider, provider_id, types=[doc_type])

    return result


class ProviderRouter:
    """Configuration-driven router that maps document types to extraction providers."""

    def __init__(self) -> None:
        self._providers: dict[str, ExtractionProvider] = {}
        self._default_providers: list[ExtractionProvider] = []

    def register(
        self,
        provider: ExtractionProvider,
        provider_id: str,
        types: Optional[list[str]] = None,
    ) -> None:
        if types is None:
            self._default_providers.append(provider)
            return
        for doc_type in types:
            self._providers[doc_type] = provider

    def resolve(self, document_type: str) -> Optional[ExtractionProvider]:
        provider = self._providers.get(document_type)
        if provider is not None:
            return provider
        for p in self._default_providers:
            try:
                if p.supports_type(document_type):
                    return p
            except Exception:
                logger.warning(
                    "provider_supports_type_failed", document_type=document_type
                )
        return None

    def discover_from_registry(self, registry: PluginRegistry) -> None:
        """Discover and register SEMANTIC-type extraction providers from F02 PluginRegistry."""
        from .plugin_metadata import PluginType

        for descriptor in registry.get_by_type(PluginType.SEMANTIC.value):
            factory = descriptor.metadata.handler_factory
            if factory is None:
                continue
            try:
                provider = factory()
                if not hasattr(provider, "extract") or not hasattr(
                    provider, "supports_type"
                ):
                    logger.warning(
                        "discovered_provider_missing_required_methods",
                        plugin_id=descriptor.metadata.id,
                    )
                    continue
                self.register(provider, descriptor.metadata.id)
                logger.info(
                    "discovered_semantic_provider",
                    plugin_id=descriptor.metadata.id,
                )
            except Exception as exc:
                logger.warning(
                    "failed_to_instantiate_semantic_provider",
                    plugin_id=descriptor.metadata.id,
                    error=str(exc),
                )

    def list_providers(self) -> list[ExtractionProvider]:
        seen: set[int] = set()
        result: list[ExtractionProvider] = []
        for p in list(self._providers.values()) + self._default_providers:
            pid = id(p)
            if pid not in seen:
                seen.add(pid)
                result.append(p)
        return result
