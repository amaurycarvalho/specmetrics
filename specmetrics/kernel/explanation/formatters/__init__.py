from typing import Protocol

from ..models import ExplanationComparison, MeasurementExplanation


class ExplanationFormatter(Protocol):
    name: str

    def format(self, explanation: MeasurementExplanation) -> str: ...

    def format_comparison(self, comparison: ExplanationComparison) -> str: ...
