"""Bloom taxonomy classifier for Cognitive Points measurement."""

from __future__ import annotations

from typing import Protocol, Self


class BloomClassifier(Protocol):
    """Protocol for classifiers that map specification elements to Bloom levels."""

    def classify(self: Self, element_type: str, element: object = None) -> str:
        """Return the Bloom level for the given element type and optional element."""
        ...


SUB_TYPE_ATTRS: dict[str, str] = {
    "business_rule": "rule_type",
    "operation": "operation_type",
    "specification_activity": "activity_type",
}

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
    "business_rule.constraint": "apply",
    "business_rule.condition": "analyze",
    "business_rule.policy": "evaluate",
    "business_rule.derivation": "evaluate",
    "operation": "apply",
    "operation.standard": "apply",
    "operation.conditional": "analyze",
    "operation.iterative": "analyze",
    "operation.transactional": "create",
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
    """Default Bloom classifier using built-in mappings and weights."""

    def __init__(
        self: Self,
        bloom_mappings: dict[str, str] | None = None,
        bloom_weights: dict[str, float] | None = None,
        default_bloom_level: str = "understand",
    ) -> None:
        """Initialize the classifier with optional custom mappings and weights."""
        self._mappings = _DEFAULT_BLOOM_MAPPINGS.copy()
        if bloom_mappings:
            self._mappings.update(bloom_mappings)
        self._weights = _DEFAULT_BLOOM_WEIGHTS.copy()
        if bloom_weights:
            self._weights.update(bloom_weights)
        self._default_bloom_level = default_bloom_level

    @property
    def mappings(self: Self) -> dict[str, str]:
        """Return a copy of the element type to Bloom level mappings."""
        return dict(self._mappings)

    @property
    def weights(self: Self) -> dict[str, float]:
        """Return a copy of the Bloom level to weight mappings."""
        return dict(self._weights)

    @property
    def default_bloom_level(self: Self) -> str:
        """Return the default Bloom level used for unmapped element types."""
        return self._default_bloom_level

    def classify(self: Self, element_type: str, element: object = None) -> str:
        """Return the Bloom level for the given element type and optional element."""
        if element is not None:
            attr_name = SUB_TYPE_ATTRS.get(element_type)
            if attr_name is not None:
                sub_type_value = getattr(element, attr_name, None)
                if sub_type_value is not None:
                    key = f"{element_type}.{sub_type_value}"
                    if key in self._mappings:
                        return self._mappings[key]
        return self._mappings.get(element_type, self._default_bloom_level)

    def get_weight(self: Self, bloom_level: str) -> float:
        """Return the cognitive weight for the given Bloom level."""
        return self._weights.get(bloom_level, 1.0)
