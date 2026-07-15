from __future__ import annotations

from typing import Optional

import structlog

from .extraction_provider import ExtractionResult, ExtractionProvider

logger = structlog.get_logger(__name__)


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
                logger.warning("provider_supports_type_failed", document_type=document_type)
        return None

    def list_providers(self) -> list[ExtractionProvider]:
        seen: set[int] = set()
        result: list[ExtractionProvider] = []
        for p in list(self._providers.values()) + self._default_providers:
            pid = id(p)
            if pid not in seen:
                seen.add(pid)
                result.append(p)
        return result
