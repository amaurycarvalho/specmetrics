from __future__ import annotations

from .models import FunctionalWorkItem, StoryPointMeasurementResult


def build_explanation(
    result: StoryPointMeasurementResult,
) -> list[FunctionalWorkItem]:
    return sorted(result.items, key=lambda i: i.raw_score, reverse=True)


def top_contributors(
    result: StoryPointMeasurementResult,
    top_n: int = 10,
) -> list[FunctionalWorkItem]:
    ranked = build_explanation(result)
    return ranked[:top_n]


def factor_breakdown_summary(
    result: StoryPointMeasurementResult,
) -> dict[str, float]:
    summary: dict[str, float] = {}
    for item in result.items:
        for factor, score in item.factor_breakdown.items():
            summary[factor] = summary.get(factor, 0.0) + score
    return summary


def evidence_assembly(
    item: FunctionalWorkItem,
) -> list[dict]:
    return [
        {
            "graph_node_id": ref.graph_node_id,
            "document_id": ref.document_id,
            "section_id": ref.section_id,
            "text": ref.text,
        }
        for ref in item.evidence_refs
    ]
