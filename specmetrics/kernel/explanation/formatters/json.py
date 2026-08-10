"""JSON output formatter for measurement explanations and comparisons."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Self

from ..models import ExplanationComparison, MeasurementExplanation


class JsonFormatter:
    """Format explanations and comparisons as indented JSON."""

    name = "json"

    def format(self: Self, explanation: MeasurementExplanation) -> str:
        """Format a single measurement explanation as JSON."""
        return format_explanation(explanation)

    def format_comparison(self: Self, comparison: ExplanationComparison) -> str:
        """Format a comparison of two explanations as JSON."""
        return format_comparison(comparison)


def _default_serializer(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def format_explanation(explanation: MeasurementExplanation) -> str:
    """Serialize a measurement explanation to an indented JSON string."""
    return json.dumps(
        explanation.model_dump(mode="json"),
        indent=2,
        default=_default_serializer,
    )


def format_comparison(comparison: ExplanationComparison) -> str:
    """Serialize an explanation comparison to an indented JSON string."""
    return json.dumps(
        comparison.model_dump(mode="json"),
        indent=2,
        default=_default_serializer,
    )
