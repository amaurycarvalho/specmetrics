from __future__ import annotations

from .models import BCPMeasurementResult, BCPWorkItem


def build_explanation(
    result: BCPMeasurementResult,
) -> list[BCPWorkItem]:
    return sorted(result.items, key=lambda i: i.bcp_score, reverse=True)


def top_contributors(
    result: BCPMeasurementResult,
    top_n: int = 10,
) -> list[BCPWorkItem]:
    ranked = build_explanation(result)
    return ranked[:top_n]


def evidence_assembly(
    item: BCPWorkItem,
) -> list[dict]:
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
    summary: dict[str, float] = {}
    for item in result.items:
        for component, score in item.component_breakdown.items():
            summary[component] = summary.get(component, 0.0) + score
    return summary
