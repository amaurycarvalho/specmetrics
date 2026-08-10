from __future__ import annotations

import pytest

from specmetrics.plugins.measurement.cognitive_points.fibonacci_normalizer import (
    FibonacciNormalizer,
    normalize,
)


class TestFibonacciNormalizer:
    def test_below_first_threshold_returns_one(self):
        result = normalize(0.0)
        assert result.output_value == 1

    def test_below_first_threshold_non_zero(self):
        result = normalize(4.0)
        assert result.output_value == 1

    def test_at_threshold_boundary(self):
        result = normalize(5.0)
        assert result.output_value == 3

    def test_mid_range_value(self):
        result = normalize(15.0)
        assert result.output_value == 5

    def test_above_max_threshold_returns_max(self):
        result = normalize(200.0)
        assert result.output_value == 100

    def test_below_next_threshold(self):
        result = normalize(54.0)
        assert result.output_value == 13

    def test_high_boundary(self):
        result = normalize(130.0)
        assert result.output_value == 100

    def test_max_clamping(self):
        result = normalize(1000.0)
        assert result.output_value == 100

    def test_threshold_applied_reported(self):
        result = normalize(10.0)
        assert result.threshold_applied == 12

    def test_raw_score_preserved(self):
        result = normalize(42.5)
        assert result.raw_score == 42.5


class TestFibonacciNormalizerCustom:
    def test_custom_thresholds_and_values(self):
        normalizer = FibonacciNormalizer(
            thresholds=[10, 50, 100], output_values=[1, 5, 10, 20]
        )
        assert normalizer.normalize(5).output_value == 1
        assert normalizer.normalize(25).output_value == 5
        assert normalizer.normalize(75).output_value == 10
        assert normalizer.normalize(150).output_value == 20

    def test_invalid_validation(self):
        with pytest.raises(ValueError, match="len.*must equal"):
            FibonacciNormalizer(thresholds=[1, 2], output_values=[1, 2, 3, 4])

    def test_thresholds_property(self):
        normalizer = FibonacciNormalizer(thresholds=[1, 2], output_values=[1, 2, 3])
        assert normalizer.thresholds == [1, 2]
        assert normalizer.output_values == [1, 2, 3]

    def test_above_all_thresholds_reports_last_threshold(self):
        result = normalize(200.0)
        assert result.output_value == 100
        assert result.threshold_applied == 130.0

    def test_invalid_validation_exact_message(self):
        with pytest.raises(ValueError, match=r"len\(thresholds\) \+ 1 \(3\)"):
            FibonacciNormalizer(thresholds=[1, 2], output_values=[1, 2, 3, 4])
