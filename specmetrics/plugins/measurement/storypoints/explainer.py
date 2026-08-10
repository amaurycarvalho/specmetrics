"""Explanation helpers for Story Points measurement."""

from __future__ import annotations

from .models import FunctionalWorkItem, StoryPointMeasurementResult


def build_explanation(
    result: StoryPointMeasurementResult,
) -> list[FunctionalWorkItem]:
    """Return all work items sorted by raw score, highest first."""
    return sorted(result.items, key=lambda i: i.raw_score, reverse=True)


def top_contributors(
    result: StoryPointMeasurementResult,
    top_n: int = 10,
) -> list[FunctionalWorkItem]:
    """Return the top N work items by raw score."""
    ranked = build_explanation(result)
    return ranked[:top_n]


def factor_breakdown_summary(
    result: StoryPointMeasurementResult,
) -> dict[str, float]:
    """Return the summed factor and content scores across all work items."""
    summary: dict[str, float] = {}
    total_content = 0.0
    for item in result.items:
        for factor, score in item.factor_breakdown.items():
            summary[factor] = summary.get(factor, 0.0) + score
        total_content += item.content_score
    if total_content > 0.0:
        summary["content_score"] = total_content
    return summary


def evidence_assembly(
    item: FunctionalWorkItem,
) -> list[dict]:
    """Return a serializable list of evidence references for the given item."""
    return [
        {
            "graph_node_id": ref.graph_node_id,
            "document_id": ref.document_id,
            "section_id": ref.section_id,
            "text": ref.text,
        }
        for ref in item.evidence_refs
    ]
