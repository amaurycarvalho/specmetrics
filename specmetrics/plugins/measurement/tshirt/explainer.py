"""Explanation helpers for T-Shirt sizing."""

from __future__ import annotations

from .models import FunctionalWorkItem, TShirtMeasurementResult


def build_explanation(
    result: TShirtMeasurementResult,
) -> list[FunctionalWorkItem]:
    """Return all items sorted by story point value, highest first."""
    return sorted(result.items, key=lambda i: i.story_point_value, reverse=True)


def top_contributors(
    result: TShirtMeasurementResult,
    top_n: int = 10,
) -> list[FunctionalWorkItem]:
    """Return the top N items by story point value."""
    ranked = build_explanation(result)
    return ranked[:top_n]


def distribution_summary(
    result: TShirtMeasurementResult,
) -> dict[str, int]:
    """Return the t-shirt size distribution of the measurement."""
    return dict(result.distribution)


def evidence_assembly(
    item: FunctionalWorkItem,
) -> list[dict]:
    """Return a serializable list of evidence references for the given item."""
    return [
        {
            "element_id": ref.element_id,
            "story_point_value": ref.story_point_value,
            "mapping_rule": ref.mapping_rule,
            "document_id": ref.document_id,
        }
        for ref in item.evidence_refs
    ]
