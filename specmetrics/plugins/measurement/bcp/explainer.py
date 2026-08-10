"""Explanation helpers for BCP measurement results."""

from __future__ import annotations

from .models import BCPMeasurementResult, BCPWorkItem


def build_explanation(
    result: BCPMeasurementResult,
) -> list[BCPWorkItem]:
    """Return measured items ranked by BCP score descending."""
    return sorted(result.items, key=lambda i: i.bcp_score, reverse=True)


def top_contributors(
    result: BCPMeasurementResult,
    top_n: int = 10,
) -> list[BCPWorkItem]:
    """Return the top ``top_n`` contributing items by BCP score."""
    ranked = build_explanation(result)
    return ranked[:top_n]


def evidence_assembly(
    item: BCPWorkItem,
) -> list[dict]:
    """Return a flattened evidence reference list for a work item."""
    return [
        {
            "element_id": ref.element_id,
            "document_id": ref.document_id,
            "section_id": ref.section_id,
            "text": ref.text,
        }
        for ref in item.evidence_refs
    ]


def component_breakdown_summary(
    result: BCPMeasurementResult,
) -> dict[str, float]:
    """Aggregate component breakdown scores across all measured items."""
    summary: dict[str, float] = {}
    for item in result.items:
        for component, score in item.component_breakdown.items():
            summary[component] = summary.get(component, 0.0) + score
    return summary
