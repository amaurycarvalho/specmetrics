from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


_DEFAULT_THRESHOLDS: list[float] = [2, 4, 8, 14, 22, 35, 55, 85]
_DEFAULT_OUTPUT_VALUES: list[int] = [1, 2, 3, 5, 8, 13, 20, 40, 100]


class NormalizationResult(BaseModel):
    raw_score: float
    threshold_applied: float
    output_value: int


class NormalizationProfile(BaseModel):
    thresholds: list[float] = Field(default_factory=lambda: list(_DEFAULT_THRESHOLDS))
    output_values: list[int] = Field(default_factory=lambda: list(_DEFAULT_OUTPUT_VALUES))

    @model_validator(mode="after")
    def validate_lengths(self) -> NormalizationProfile:
        if len(self.output_values) != len(self.thresholds) + 1:
            raise ValueError(
                f"len(output_values) ({len(self.output_values)}) must equal "
                f"len(thresholds) + 1 ({len(self.thresholds) + 1})"
            )
        return self


class FibonacciNormalizer:
    def __init__(
        self,
        thresholds: list[float] | None = None,
        output_values: list[int] | None = None,
    ) -> None:
        self._thresholds = list(thresholds) if thresholds else list(_DEFAULT_THRESHOLDS)
        self._output_values = list(output_values) if output_values else list(_DEFAULT_OUTPUT_VALUES)

        if len(self._output_values) != len(self._thresholds) + 1:
            raise ValueError(
                f"len(output_values) ({len(self._output_values)}) must equal "
                f"len(thresholds) + 1 ({len(self._thresholds) + 1})"
            )

    @property
    def thresholds(self) -> list[float]:
        return list(self._thresholds)

    @property
    def output_values(self) -> list[int]:
        return list(self._output_values)

    def normalize(self, raw_score: float) -> NormalizationResult:
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
            threshold_applied=threshold_applied,
            output_value=output_value,
        )


def normalize(raw_score: float) -> NormalizationResult:
    return FibonacciNormalizer().normalize(raw_score)


def normalize_with(
    raw_score: float,
    thresholds: list[float],
    output_values: list[int],
) -> NormalizationResult:
    return FibonacciNormalizer(
        thresholds=thresholds, output_values=output_values
    ).normalize(raw_score)
