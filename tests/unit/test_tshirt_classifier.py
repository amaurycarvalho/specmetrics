from __future__ import annotations

import time

import pytest

from specmetrics.plugins.measurement.tshirt.classifier import (
    DEFAULT_MAPPING,
    TShirtClassifier,
    classify_all,
)
from specmetrics.plugins.measurement.tshirt.models import TShirtSize


class TestTShirtClassifier:
    def test_default_mapping(self):
        classifier = TShirtClassifier()
        for size in DEFAULT_MAPPING:
            mn, mx = size.story_point_range
            for sp in range(mn, mx + 1):
                label, _rule = classifier.classify(sp)
                assert label == size.label, (
                    f"SP={sp} should be {size.label}, got {label}"
                )

    def test_sp1_is_xs(self):
        classifier = TShirtClassifier()
        label, _rule = classifier.classify(1)
        assert label == "XS"

    def test_sp2_is_s(self):
        classifier = TShirtClassifier()
        label, _rule = classifier.classify(2)
        assert label == "S"

    def test_sp3_is_s(self):
        classifier = TShirtClassifier()
        label, _rule = classifier.classify(3)
        assert label == "S"

    def test_sp5_is_m(self):
        classifier = TShirtClassifier()
        label, rule = classifier.classify(5)
        assert label == "M"
        assert "default: 5 → M" in rule

    def test_sp8_is_l(self):
        classifier = TShirtClassifier()
        label, rule = classifier.classify(8)
        assert label == "L"
        assert "default: 8-13 → L" in rule

    def test_sp13_is_l(self):
        classifier = TShirtClassifier()
        label, rule = classifier.classify(13)
        assert label == "L"
        assert "default: 8-13 → L" in rule

    def test_sp20_is_xl(self):
        classifier = TShirtClassifier()
        label, rule = classifier.classify(20)
        assert label == "XL"
        assert "default: 20-40 → XL" in rule

    def test_sp40_is_xl(self):
        classifier = TShirtClassifier()
        label, rule = classifier.classify(40)
        assert label == "XL"
        assert "default: 20-40 → XL" in rule

    def test_sp100_is_xxl(self):
        classifier = TShirtClassifier()
        label, _rule = classifier.classify(100)
        assert label == "XXL"


class TestClassifierDeterminism:
    def test_deterministic(self):
        classifier = TShirtClassifier()
        for sp in [1, 2, 5, 8, 13, 20, 40, 100]:
            l1, _ = classifier.classify(sp)
            l2, _ = classifier.classify(sp)
            assert l1 == l2


class TestClassifierValidation:
    def test_overlapping_ranges_rejected(self):
        with pytest.raises(ValueError, match="Overlapping"):
            TShirtClassifier(
                mapping=[
                    TShirtSize(label="S", story_point_range=(1, 5), ordinal=1),
                    TShirtSize(label="M", story_point_range=(3, 8), ordinal=2),
                ]
            )

    def test_incomplete_mapping_allowed(self):
        classifier = TShirtClassifier(
            mapping=[
                TShirtSize(label="S", story_point_range=(1, 3), ordinal=1),
                TShirtSize(label="M", story_point_range=(5, 8), ordinal=2),
            ]
        )
        assert classifier.classify(2)[0] == "S"
        assert classifier.classify(5)[0] == "M"
        assert classifier.classify(4)[0] == "UNKNOWN"

    def test_empty_mapping_rejected(self):
        with pytest.raises(ValueError, match="at least one"):
            TShirtClassifier(mapping=[])

    def test_duplicate_labels_rejected(self):
        with pytest.raises(ValueError, match="duplicate"):
            TShirtClassifier(
                mapping=[
                    TShirtSize(label="S", story_point_range=(1, 3), ordinal=1),
                    TShirtSize(label="S", story_point_range=(4, 8), ordinal=2),
                    TShirtSize(label="M", story_point_range=(9, 13), ordinal=3),
                    TShirtSize(label="L", story_point_range=(14, 20), ordinal=4),
                    TShirtSize(label="XL", story_point_range=(21, 40), ordinal=5),
                    TShirtSize(label="XXL", story_point_range=(41, 100), ordinal=6),
                ]
            )


class TestClassifierCustomMapping:
    def test_custom_5_level_scale(self):
        custom = [
            TShirtSize(label="XS", story_point_range=(1, 2), ordinal=1),
            TShirtSize(label="S", story_point_range=(3, 5), ordinal=2),
            TShirtSize(label="M", story_point_range=(6, 13), ordinal=3),
            TShirtSize(label="L", story_point_range=(14, 40), ordinal=4),
            TShirtSize(label="XL", story_point_range=(41, 100), ordinal=5),
        ]
        classifier = TShirtClassifier(mapping=custom)
        assert classifier.classify(1)[0] == "XS"
        assert classifier.classify(4)[0] == "S"
        assert classifier.classify(8)[0] == "M"
        assert classifier.classify(20)[0] == "L"
        assert classifier.classify(50)[0] == "XL"

    def test_invalid_custom_override_overlap(self):
        with pytest.raises(ValueError, match="Overlapping"):
            TShirtClassifier(
                mapping=[
                    TShirtSize(label="S", story_point_range=(1, 10), ordinal=1),
                    TShirtSize(label="M", story_point_range=(5, 20), ordinal=2),
                ]
            )

    def test_custom_override_with_gaps_allowed(self):
        classifier = TShirtClassifier(
            mapping=[
                TShirtSize(label="S", story_point_range=(1, 10), ordinal=1),
                TShirtSize(label="M", story_point_range=(21, 100), ordinal=2),
            ]
        )
        assert classifier.classify(5)[0] == "S"
        assert classifier.classify(25)[0] == "M"
        assert classifier.classify(15)[0] == "UNKNOWN"


class TestClassifyAll:
    def test_classify_all_from_sp_result(self):
        sp_items = [
            {"element_id": "fp-001", "element_name": "A", "normalized_value": 3},
            {"element_id": "fp-002", "element_name": "B", "normalized_value": 8},
            {"element_id": "fp-003", "element_name": "C", "normalized_value": 20},
        ]
        items, _warnings = classify_all(sp_items)
        assert len(items) == 3
        assert items[0].tshirt_size == "S"
        assert items[1].tshirt_size == "L"
        assert items[2].tshirt_size == "XL"

    def test_missing_sp_skipped_with_warning(self):
        sp_items = [
            {"element_id": "fp-001", "element_name": "A"},
        ]
        items, warnings = classify_all(sp_items)
        assert len(items) == 0
        assert len(warnings) == 1
        assert warnings[0].code == "MISSING_SP_VALUE"


class TestFullCoverage:
    def test_all_9_fibonacci_values_mapped_to_6_sizes(self):
        classifier = TShirtClassifier()
        seen: set[str] = set()
        for sp in [1, 2, 3, 5, 8, 13, 20, 40, 100]:
            label, _ = classifier.classify(sp)
            assert label != "UNKNOWN", f"SP={sp} produced UNKNOWN"
            seen.add(label)
        assert seen == {"XS", "S", "M", "L", "XL", "XXL"}

    def test_m_range_is_exactly_5(self):
        classifier = TShirtClassifier()
        assert classifier.classify(5)[0] == "M"
        assert classifier.classify(3)[0] != "M"
        assert classifier.classify(8)[0] != "M"


class TestPerformance:
    @pytest.mark.slow
    def test_performance_500_fps(self):
        sp_items = [
            {
                "element_id": f"fp-{i:04d}",
                "element_name": f"Process {i}",
                "normalized_value": (i % 9) + 1,
            }
            for i in range(500)
        ]
        start = time.monotonic()
        items, _warnings = classify_all(sp_items)
        elapsed = time.monotonic() - start
        assert len(items) == 500
        assert elapsed < 1.0


class TestValidationMessages:
    def test_empty_mapping_error_message_exact(self):
        """Kills _validate_mapping__mutmut_3/4 (empty mapping message literal)."""
        with pytest.raises(
            ValueError, match="Mapping must contain at least one size"
        ):
            TShirtClassifier(mapping=[])

    def test_duplicate_labels_error_message_exact(self):
        """Kills _validate_mapping__mutmut_9/10 (duplicate labels message literal)."""
        with pytest.raises(
            ValueError, match="Mapping contains duplicate size labels"
        ):
            TShirtClassifier(
                mapping=[
                    TShirtSize(label="S", story_point_range=(1, 3), ordinal=1),
                    TShirtSize(label="S", story_point_range=(4, 8), ordinal=2),
                ]
            )


class TestValidationSorting:
    def test_mapping_sorted_by_range_min_not_max(self):
        """Kills _validate_mapping__mutmut_20 (sort key uses range[1] instead of [0])."""
        classifier = TShirtClassifier(
            mapping=[
                TShirtSize(label="S", story_point_range=(5, 5), ordinal=2),
                TShirtSize(label="XS", story_point_range=(1, 1), ordinal=1),
            ]
        )
        assert classifier.classify(1)[0] == "XS"
        assert classifier.classify(5)[0] == "S"

    def test_adjacent_ranges_with_equal_boundary_rejected(self):
        """Kills _validate_mapping__mutmut_30 (>= narrowed to >)."""
        with pytest.raises(ValueError, match="Overlapping"):
            TShirtClassifier(
                mapping=[
                    TShirtSize(label="S", story_point_range=(1, 3), ordinal=1),
                    TShirtSize(label="M", story_point_range=(3, 5), ordinal=2),
                ]
            )
