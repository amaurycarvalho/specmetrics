"""Normalization utilities for Story Points measurement."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

DEFAULT_FIBONACCI_SCALE: list[int] = [1, 2, 3, 5, 8, 13, 20, 40, 100]

_DEFAULT_THRESHOLDS: list[float] = [2, 4, 8, 14, 22, 35, 55, 85]
_DEFAULT_OUTPUT_VALUES: list[int] = [1, 2, 3, 5, 8, 13, 20, 40, 100]


class NormalizationResult(BaseModel):
    """Result of normalizing a raw score."""

    raw_score: float
    output_value: int
    rank_position: int = 0
    threshold_applied: float = 0.0


class NormalizationProfile(BaseModel):
    """Thresholds and output values used for normalization."""

    thresholds: list[float] = Field(default_factory=lambda: list(_DEFAULT_THRESHOLDS))
    output_values: list[int] = Field(
        default_factory=lambda: list(_DEFAULT_OUTPUT_VALUES)
    )

    @model_validator(mode="after")
    def validate_lengths(self: Self) -> NormalizationProfile:
        """Validate that output values count equals thresholds count plus one."""
        if len(self.output_values) != len(self.thresholds) + 1:
            raise ValueError(
                f"len(output_values) ({len(self.output_values)}) must equal "
                f"len(thresholds) + 1 ({len(self.thresholds) + 1})"
            )
        return self


class RelativeRankingNormalizer:
    """Normalize raw scores into Fibonacci values using relative ranking."""

    def __init__(
        self: Self,
        fibonacci_scale: list[int] | None = None,
        ranking_strategy: str = "percentile",
    ) -> None:
        """Initialize the normalizer with an optional Fibonacci scale."""
        self._fibonacci_scale = (
            list(fibonacci_scale) if fibonacci_scale else list(DEFAULT_FIBONACCI_SCALE)
        )
        self._ranking_strategy = ranking_strategy

    @property
    def fibonacci_scale(self: Self) -> list[int]:
        """Return a copy of the configured Fibonacci scale."""
        return list(self._fibonacci_scale)

    @property
    def ranking_strategy(self: Self) -> str:
        """Return the configured ranking strategy."""
        return self._ranking_strategy

    def normalize_all(
        self: Self, scores: list[tuple[str, float]]
    ) -> dict[str, NormalizationResult]:
        """Return normalized results for the given element scores."""
        sorted_scores = sorted(scores, key=lambda x: x[1])
        n = len(sorted_scores)
        scale = self._fibonacci_scale
        num_bands = len(scale)
        results: dict[str, NormalizationResult] = {}

        if n == 0:
            return results

        if n <= num_bands:
            for idx, (elem_id, raw) in enumerate(sorted_scores):
                fib_idx = int(idx * (num_bands - 1) / (n - 1)) if n > 1 else 0
                results[elem_id] = NormalizationResult(
                    raw_score=raw,
                    output_value=scale[fib_idx],
                    rank_position=idx,
                )
        else:
            for idx, (elem_id, raw) in enumerate(sorted_scores):
                band = int(idx * num_bands / n)
                if band >= num_bands:
                    band = num_bands - 1
                results[elem_id] = NormalizationResult(
                    raw_score=raw,
                    output_value=scale[band],
                    rank_position=idx,
                )

        return results

    def normalize(self: Self, raw_score: float) -> NormalizationResult:
        """Return a normalization result for the given raw score."""
        return NormalizationResult(
            raw_score=raw_score,
            output_value=self._fibonacci_scale[-1],
        )


class FibonacciNormalizer:
    """Normalize raw scores into Fibonacci output values by thresholds."""

    def __init__(
        self: Self,
        thresholds: list[float] | None = None,
        output_values: list[int] | None = None,
    ) -> None:
        """Initialize the normalizer with optional thresholds and output values."""
        _DEFAULT_THRESHOLDS: list[float] = [2, 4, 8, 14, 22, 35, 55, 85]
        _DEFAULT_OUTPUT_VALUES: list[int] = [1, 2, 3, 5, 8, 13, 20, 40, 100]
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

    def normalize(self: Self, raw_score: float) -> NormalizationResult:
        """Return the normalized result for the given raw score."""
        threshold_applied: float = 0.0
        output_value: int = self._output_values[-1]

        for i, threshold in enumerate(self._thresholds):
            if raw_score < threshold:
                output_value = self._output_values[i]
                threshold_applied = threshold
                break
        else:
            threshold_applied = self._thresholds[-1] if self._thresholds else 0.0

        return NormalizationResult(
            raw_score=raw_score,
            output_value=output_value,
            threshold_applied=threshold_applied,
        )


def normalize(raw_score: float) -> NormalizationResult:
    """Normalize a raw score using the default Fibonacci normalizer."""
    return FibonacciNormalizer().normalize(raw_score)


def normalize_with(
    raw_score: float,
    thresholds: list[float],
    output_values: list[int],
) -> NormalizationResult:
    """Normalize a raw score using the given thresholds and output values."""
    return FibonacciNormalizer(
        thresholds=thresholds, output_values=output_values
    ).normalize(raw_score)
