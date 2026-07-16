from __future__ import annotations

import json
from datetime import datetime

from ..models import ExplanationComparison, MeasurementExplanation


class JsonFormatter:
    name = "json"

    def format(self, explanation: MeasurementExplanation) -> str:
        return format_explanation(explanation)

    def format_comparison(self, comparison: ExplanationComparison) -> str:
        return format_comparison(comparison)


def _default_serializer(obj: object) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def format_explanation(explanation: MeasurementExplanation) -> str:
    return json.dumps(
        explanation.model_dump(mode="json"),
        indent=2,
        default=_default_serializer,
    )


def format_comparison(comparison: ExplanationComparison) -> str:
    return json.dumps(
        comparison.model_dump(mode="json"),
        indent=2,
        default=_default_serializer,
    )
