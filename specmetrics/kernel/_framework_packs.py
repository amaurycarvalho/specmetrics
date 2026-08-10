"""Framework-specific rule pack detection for the deterministic engine."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from .adapter_interface import Document

_FRAMEWORK_PACK_NAMES = {
    "openspec": "openspec_rules.yaml",
    "speckit": "speckit_rules.yaml",
}


class FrameworkPackMixin:
    """Provide framework-specific rule pack loading for the engine."""

    def _load_framework_packs(self: Self, documents: list[Document]) -> list[str]:
        detected = self._detect_framework_types(documents)
        rules_dir = Path(__file__).parent / "rules"
        packs: list[str] = []
        for framework, filename in _FRAMEWORK_PACK_NAMES.items():
            if framework in detected:
                path = rules_dir / filename
                if path.exists():
                    self._check_pack_version(path)
                    packs.append(str(path))
        return packs

    def _detect_framework_types(self: Self, documents: list[Document]) -> set[str]:
        detected: set[str] = set()
        for doc in documents:
            dt = (doc.document_type or "").lower()
            if self._is_openspec_type(dt):
                detected.add("openspec")
            if self._is_speckit_type(dt):
                detected.add("speckit")
        return detected

    def _is_openspec_type(self: Self, document_type: str) -> bool:
        return "openspec" in document_type or document_type in (
            "use_case",
            "actor",
            "requirement",
        )

    def _is_speckit_type(self: Self, document_type: str) -> bool:
        return "speckit" in document_type or document_type in (
            "feature",
            "scenario",
            "background",
        )