"""Output formatters for measurement explanations and comparisons."""

from __future__ import annotations

from typing import Protocol, Self

from ..models import ExplanationComparison, MeasurementExplanation


class ExplanationFormatter(Protocol):
    """Interface for formatting explanations and comparisons."""

    name: str

    def format(self: Self, explanation: MeasurementExplanation) -> str:
        """Format a single measurement explanation as text."""
        ...

    def format_comparison(self: Self, comparison: ExplanationComparison) -> str:
        """Format a comparison of two explanations as text."""
        ...


def get_formatter(name: str = "text") -> ExplanationFormatter:
    """Return a formatter instance for the given output format name."""
    if name == "json":
        from .json import JsonFormatter

        return JsonFormatter()
    from .text import TextFormatter

    return TextFormatter()
