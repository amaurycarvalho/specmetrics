from __future__ import annotations

from typing import Protocol


class BloomClassifier(Protocol):
    def classify(self, element_type: str) -> str: ...


_DEFAULT_BLOOM_MAPPINGS: dict[str, str] = {
    "exploration": "understand",
    "clarification": "analyze",
    "refinement": "apply",
    "review": "evaluate",
    "validation": "evaluate",
    "decision": "evaluate",
    "assumption": "understand",
    "constraint": "apply",
    "risk": "analyze",
    "open_question": "analyze",
    "acceptance_criterion": "apply",
    "glossary_term": "remember",
    "functional_process": "create",
    "business_rule": "apply",
    "operation": "apply",
    "data_group": "understand",
    "relationship": "understand",
    "actor": "remember",
}


_DEFAULT_BLOOM_WEIGHTS: dict[str, float] = {
    "remember": 1.0,
    "understand": 2.0,
    "apply": 3.0,
    "analyze": 4.0,
    "evaluate": 5.0,
    "create": 8.0,
}


class DefaultBloomClassifier:
    def __init__(
        self,
        bloom_mappings: dict[str, str] | None = None,
        bloom_weights: dict[str, float] | None = None,
        default_bloom_level: str = "analyze",
    ) -> None:
        self._mappings = _DEFAULT_BLOOM_MAPPINGS.copy()
        if bloom_mappings:
            self._mappings.update(bloom_mappings)
        self._weights = _DEFAULT_BLOOM_WEIGHTS.copy()
        if bloom_weights:
            self._weights.update(bloom_weights)
        self._default_bloom_level = default_bloom_level

    @property
    def mappings(self) -> dict[str, str]:
        return dict(self._mappings)

    @property
    def weights(self) -> dict[str, float]:
        return dict(self._weights)

    @property
    def default_bloom_level(self) -> str:
        return self._default_bloom_level

    def classify(self, element_type: str) -> str:
        return self._mappings.get(element_type, self._default_bloom_level)

    def get_weight(self, bloom_level: str) -> float:
        return self._weights.get(bloom_level, 1.0)
