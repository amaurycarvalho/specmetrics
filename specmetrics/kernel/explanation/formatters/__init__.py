from __future__ import annotations

from typing import Protocol

from ..models import ExplanationComparison, MeasurementExplanation


class ExplanationFormatter(Protocol):
    name: str

    def format(self, explanation: MeasurementExplanation) -> str: ...

    def format_comparison(self, comparison: ExplanationComparison) -> str: ...


def get_formatter(name: str = "text") -> ExplanationFormatter:
    if name == "json":
        from .json import JsonFormatter

        return JsonFormatter()
    from .text import TextFormatter

    return TextFormatter()
