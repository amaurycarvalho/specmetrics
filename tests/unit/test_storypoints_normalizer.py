from __future__ import annotations

import pytest

from specmetrics.plugins.measurement.storypoints.normalizer import (
    FibonacciNormalizer,
    normalize,
)


class TestFibonacciNormalizer:
    def test_below_first_threshold_returns_one(self):
        result = normalize(0.0)
        assert result.output_value == 1

    def test_below_first_threshold_non_zero(self):
        result = normalize(1.0)
        assert result.output_value == 1

    def test_at_threshold_boundary(self):
        result = normalize(2.0)
        assert result.output_value == 2

    def test_mid_range_value(self):
        result = normalize(6.0)
        assert result.output_value == 3

    def test_above_max_threshold_returns_max(self):
        result = normalize(200.0)
        assert result.output_value == 100

    def test_below_next_threshold(self):
        result = normalize(50.0)
        assert result.output_value == 20

    def test_max_clamping(self):
        result = normalize(1000.0)
        assert result.output_value == 100

    def test_threshold_applied_reported(self):
        result = normalize(10.0)
        assert result.threshold_applied == 14

    def test_raw_score_preserved(self):
        result = normalize(42.5)
        assert result.raw_score == 42.5

    def test_scale_values(self):
        result = normalize(0.5)
        assert result.output_value == 1
        result = normalize(3.0)
        assert result.output_value == 2
        result = normalize(6.0)
        assert result.output_value == 3
        result = normalize(11.0)
        assert result.output_value == 5
        result = normalize(18.0)
        assert result.output_value == 8
        result = normalize(28.0)
        assert result.output_value == 13
        result = normalize(45.0)
        assert result.output_value == 20
        result = normalize(70.0)
        assert result.output_value == 40
        result = normalize(90.0)
        assert result.output_value == 100


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
            FibonacciNormalizer(
                thresholds=[1, 2], output_values=[1, 2, 3, 4]
            )

    def test_thresholds_property(self):
        normalizer = FibonacciNormalizer(
            thresholds=[1, 2], output_values=[1, 2, 3]
        )
        assert normalizer.thresholds == [1, 2]
        assert normalizer.output_values == [1, 2, 3]


class TestNormalizationProfile:
    def test_default_constructor(self):
        from specmetrics.plugins.measurement.storypoints.normalizer import (
            NormalizationProfile,
        )

        profile = NormalizationProfile()
        assert len(profile.output_values) == len(profile.thresholds) + 1

    def test_validation_error(self):
        from specmetrics.plugins.measurement.storypoints.normalizer import (
            NormalizationProfile,
        )

        with pytest.raises(ValueError, match="len.*must equal"):
            NormalizationProfile(
                thresholds=[1, 2], output_values=[1, 2, 3, 4]
            )
