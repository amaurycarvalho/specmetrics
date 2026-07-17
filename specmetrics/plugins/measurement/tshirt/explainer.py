from __future__ import annotations

from .models import FunctionalWorkItem, TShirtMeasurementResult


def build_explanation(
    result: TShirtMeasurementResult,
) -> list[FunctionalWorkItem]:
    return sorted(result.items, key=lambda i: i.story_point_value, reverse=True)


def top_contributors(
    result: TShirtMeasurementResult,
    top_n: int = 10,
) -> list[FunctionalWorkItem]:
    ranked = build_explanation(result)
    return ranked[:top_n]


def distribution_summary(
    result: TShirtMeasurementResult,
) -> dict[str, int]:
    return dict(result.distribution)


def evidence_assembly(
    item: FunctionalWorkItem,
) -> list[dict]:
    return [
        {
            "element_id": ref.element_id,
            "story_point_value": ref.story_point_value,
            "mapping_rule": ref.mapping_rule,
            "document_id": ref.document_id,
        }
        for ref in item.evidence_refs
    ]
