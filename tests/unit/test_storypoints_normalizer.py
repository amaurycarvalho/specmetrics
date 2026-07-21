from __future__ import annotations

import pytest

from specmetrics.plugins.measurement.storypoints.normalizer import (
    FibonacciNormalizer,
    RelativeRankingNormalizer,
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
            FibonacciNormalizer(thresholds=[1, 2], output_values=[1, 2, 3, 4])

    def test_thresholds_property(self):
        normalizer = FibonacciNormalizer(thresholds=[1, 2], output_values=[1, 2, 3])
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
            NormalizationProfile(thresholds=[1, 2], output_values=[1, 2, 3, 4])


class TestRelativeRankingNormalizer:
    def test_nine_entities_percentile_bands(self):
        scores = [
            ("a", 1.0), ("b", 2.0), ("c", 3.0), ("d", 5.0), ("e", 8.0),
            ("f", 13.0), ("g", 20.0), ("h", 40.0), ("i", 100.0),
        ]
        normalizer = RelativeRankingNormalizer()
        results = normalizer.normalize_all(scores)
        assert results["a"].output_value == 1
        assert results["i"].output_value == 100
        values = [results[eid].output_value for eid, _ in scores]
        assert values == sorted(values)

    def test_fewer_than_nine_entities(self):
        scores = [
            ("a", 1.0), ("b", 5.0), ("c", 10.0),
        ]
        normalizer = RelativeRankingNormalizer()
        results = normalizer.normalize_all(scores)
        assert results["a"].output_value == 1
        assert results["c"].output_value == 100
        assert results["b"].output_value > 1
        assert results["b"].output_value < 100

    def test_custom_fibonacci_scale(self):
        scores = [
            ("a", 1.0), ("b", 2.0), ("c", 3.0), ("d", 4.0), ("e", 5.0),
        ]
        normalizer = RelativeRankingNormalizer(
            fibonacci_scale=[1, 5, 10, 20, 50],
        )
        results = normalizer.normalize_all(scores)
        assert results["a"].output_value == 1
        assert results["e"].output_value == 50
        values = [results[eid].output_value for eid, _ in scores]
        assert values == sorted(values)

    def test_non_decreasing_output(self):
        scores = [(f"e{i}", float(i * 10)) for i in range(20)]
        normalizer = RelativeRankingNormalizer()
        results = normalizer.normalize_all(scores)
        prev = -1
        for eid, _ in scores:
            curr = results[eid].output_value
            assert curr >= prev
            prev = curr

    def test_rank_positions(self):
        scores = [("low", 1.0), ("mid", 5.0), ("high", 10.0)]
        normalizer = RelativeRankingNormalizer()
        results = normalizer.normalize_all(scores)
        assert results["low"].rank_position == 0
        assert results["mid"].rank_position == 1
        assert results["high"].rank_position == 2
