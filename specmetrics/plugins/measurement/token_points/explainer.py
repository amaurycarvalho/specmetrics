"""Explanation helpers for Token Points measurement."""

from __future__ import annotations

from .models import TokenContribution, TokenPointsMeasurement


def build_explanation(measurement: TokenPointsMeasurement) -> list[TokenContribution]:
    """Return all contributions sorted by partial score, highest first."""
    all_contributions = (
        measurement.specification_cost.contributions
        + measurement.code_generation_cost.contributions
    )
    return sorted(all_contributions, key=lambda c: c.partial_score, reverse=True)


def top_contributors(
    measurement: TokenPointsMeasurement,
    top_n: int = 10,
) -> list[TokenContribution]:
    """Return the top N contributions by partial score."""
    ranked = build_explanation(measurement)
    return ranked[:top_n]


def get_breakdown_by_type(measurement: TokenPointsMeasurement) -> dict[str, dict]:
    """Return contribution totals grouped by element type."""
    breakdown: dict[str, dict] = {}
    for contrib in (
        measurement.specification_cost.contributions
        + measurement.code_generation_cost.contributions
    ):
        etype = contrib.element_type
        if etype not in breakdown:
            breakdown[etype] = {"count": 0, "total": 0.0, "content_tokens": 0}
        breakdown[etype]["count"] += 1
        breakdown[etype]["total"] += contrib.partial_score
        breakdown[etype]["content_tokens"] += contrib.content_token_count
    return breakdown
