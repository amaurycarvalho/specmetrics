from __future__ import annotations

from .models import TokenContribution, TokenPointsMeasurement


def build_explanation(measurement: TokenPointsMeasurement) -> list[TokenContribution]:
    all_contributions = (
        measurement.specification_cost.contributions
        + measurement.code_generation_cost.contributions
    )
    return sorted(all_contributions, key=lambda c: c.partial_score, reverse=True)


def top_contributors(
    measurement: TokenPointsMeasurement,
    top_n: int = 10,
) -> list[TokenContribution]:
    ranked = build_explanation(measurement)
    return ranked[:top_n]


def get_breakdown_by_type(measurement: TokenPointsMeasurement) -> dict[str, dict]:
    breakdown: dict[str, dict] = {}
    for contrib in (
        measurement.specification_cost.contributions
        + measurement.code_generation_cost.contributions
    ):
        etype = contrib.element_type
        if etype not in breakdown:
            breakdown[etype] = {"count": 0, "total": 0.0}
        breakdown[etype]["count"] += 1
        breakdown[etype]["total"] += contrib.partial_score
    return breakdown
