from __future__ import annotations

from .models import CognitiveContribution, CognitivePointsMeasurement


def build_explanation(
    measurement: CognitivePointsMeasurement,
) -> list[CognitiveContribution]:
    all_contributions = (
        measurement.specification_review_effort.contributions
        + measurement.functional_validation_effort.contributions
    )
    return sorted(all_contributions, key=lambda c: c.partial_score, reverse=True)


def top_contributors(
    measurement: CognitivePointsMeasurement,
    top_n: int = 10,
) -> list[CognitiveContribution]:
    ranked = build_explanation(measurement)
    return ranked[:top_n]


def bloom_breakdown(
    measurement: CognitivePointsMeasurement,
) -> dict[str, dict[str, int]]:
    return {
        "specification_review_effort": dict(
            measurement.specification_review_effort.bloom_breakdown
        ),
        "functional_validation_effort": dict(
            measurement.functional_validation_effort.bloom_breakdown
        ),
    }
