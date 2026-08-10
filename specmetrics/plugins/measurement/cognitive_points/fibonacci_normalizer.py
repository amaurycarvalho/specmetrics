"""Fibonacci normalization for Cognitive Points measurement."""

from __future__ import annotations

from typing import Self

from .models import FibonacciNormalizationResult

_DEFAULT_THRESHOLDS: list[float] = [5, 12, 22, 35, 55, 85, 130]
_DEFAULT_OUTPUT_VALUES: list[int] = [1, 3, 5, 8, 13, 20, 40, 100]


class FibonacciNormalizer:
    """Normalize raw scores into Fibonacci output values."""

    def __init__(
        self: Self,
        thresholds: list[float] | None = None,
        output_values: list[int] | None = None,
    ) -> None:
        """Initialize the normalizer with optional thresholds and output values."""
        self._thresholds = list(thresholds) if thresholds else list(_DEFAULT_THRESHOLDS)
        self._output_values = (
            list(output_values) if output_values else list(_DEFAULT_OUTPUT_VALUES)
        )

        if len(self._output_values) != len(self._thresholds) + 1:
            raise ValueError(
                f"len(output_values) ({len(self._output_values)}) must equal "
                f"len(thresholds) + 1 ({len(self._thresholds) + 1})"
            )

    @property
    def thresholds(self: Self) -> list[float]:
        """Return a copy of the configured thresholds."""
        return list(self._thresholds)

    @property
    def output_values(self: Self) -> list[int]:
        """Return a copy of the configured output values."""
        return list(self._output_values)

    def normalize(self: Self, raw_score: float) -> FibonacciNormalizationResult:
        """Return the Fibonacci result for the given raw score."""
        threshold_applied: float = 0.0
        output_value: int = self._output_values[-1]

        for i, threshold in enumerate(self._thresholds):
            if raw_score < threshold:
                output_value = self._output_values[i]
                threshold_applied = threshold
                break
        else:
            threshold_applied = self._thresholds[-1] if self._thresholds else 0.0

        return FibonacciNormalizationResult(
            raw_score=raw_score,
            threshold_applied=threshold_applied,
            output_value=output_value,
        )


def normalize(raw_score: float) -> FibonacciNormalizationResult:
    """Normalize a raw score using the default Fibonacci normalizer."""
    return FibonacciNormalizer().normalize(raw_score)


def normalize_with(
    raw_score: float,
    thresholds: list[float],
    output_values: list[int],
) -> FibonacciNormalizationResult:
    """Normalize a raw score using the given thresholds and output values."""
    return FibonacciNormalizer(
        thresholds=thresholds, output_values=output_values
    ).normalize(raw_score)
