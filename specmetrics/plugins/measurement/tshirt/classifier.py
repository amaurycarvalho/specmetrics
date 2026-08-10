"""T-Shirt size classifier."""

from __future__ import annotations

from typing import Self

from .models import TShirtSize

DEFAULT_MAPPING: list[TShirtSize] = [
    TShirtSize(label="XS", story_point_range=(1, 1), ordinal=1),
    TShirtSize(label="S", story_point_range=(2, 3), ordinal=2),
    TShirtSize(label="M", story_point_range=(5, 5), ordinal=3),
    TShirtSize(label="L", story_point_range=(8, 13), ordinal=4),
    TShirtSize(label="XL", story_point_range=(20, 40), ordinal=5),
    TShirtSize(label="XXL", story_point_range=(100, 100), ordinal=6),
]


def _validate_mapping(sizes: list[TShirtSize]) -> None:
    if not sizes:
        raise ValueError("Mapping must contain at least one size")

    labels = [s.label for s in sizes]
    if len(labels) != len(set(labels)):
        raise ValueError("Mapping contains duplicate size labels")

    if len(sizes) >= 2:
        sorted_sizes = sorted(sizes, key=lambda s: s.story_point_range[0])
        for i in range(len(sorted_sizes) - 1):
            current_max = sorted_sizes[i].story_point_range[1]
            next_min = sorted_sizes[i + 1].story_point_range[0]
            if current_max >= next_min:
                raise ValueError(
                    f"Overlapping ranges: {sorted_sizes[i].label} "
                    f"({sorted_sizes[i].story_point_range}) overlaps "
                    f"{sorted_sizes[i + 1].label} "
                    f"({sorted_sizes[i + 1].story_point_range})"
                )


class TShirtClassifier:
    """Classify story point values into t-shirt sizes using a mapping."""

    def __init__(self: Self, mapping: list[TShirtSize] | None = None) -> None:
        """Initialize the classifier with an optional size mapping."""
        self._mapping = list(mapping) if mapping is not None else list(DEFAULT_MAPPING)
        _validate_mapping(self._mapping)

    @property
    def mapping(self: Self) -> list[TShirtSize]:
        """Return a copy of the configured size mapping."""
        return list(self._mapping)

    def classify(self: Self, story_point_value: int) -> tuple[str, str]:
        """Return the t-shirt size label and matching rule for the given value."""
        for size in self._mapping:
            mn, mx = size.story_point_range
            if mn <= story_point_value <= mx:
                rule = (
                    f"default: {mn}-{mx} → {size.label}"
                    if mn != mx
                    else f"default: {mn} → {size.label}"
                )
                return size.label, rule
        return "UNKNOWN", "default: no matching range"


def classify_all(
    sp_items: list,
    mapping: list[TShirtSize] | None = None,
) -> tuple[list, list]:
    """Classify all story point items and return classified items and warnings."""
    from .models import (
        FunctionalWorkItem as TWItem,
    )
    from .models import (
        MeasurementEvidence,
        MeasurementWarning,
    )

    classifier = (
        TShirtClassifier(mapping=mapping) if mapping is not None else TShirtClassifier()
    )
    result_items: list[TWItem] = []
    warnings: list[MeasurementWarning] = []

    for item in sp_items:
        sp_value = getattr(item, "normalized_value", None)
        if sp_value is None:
            sp_value = item.get("normalized_value") if isinstance(item, dict) else None
        if sp_value is None:
            warnings.append(
                MeasurementWarning(
                    code="MISSING_SP_VALUE",
                    message="Work item has no Story Point value, skipping",
                    element_id=getattr(item, "element_id", None)
                    or item.get("element_id"),
                )
            )
            continue

        tshirt_size, rule = classifier.classify(int(sp_value))

        element_id = getattr(item, "element_id", None) or item.get("element_id", "")
        element_name = getattr(item, "element_name", None) or item.get(
            "element_name", ""
        )

        evidence = MeasurementEvidence(
            element_id=element_id,
            story_point_value=int(sp_value),
            mapping_rule=rule,
        )

        result_items.append(
            TWItem(
                element_id=element_id,
                element_name=element_name,
                story_point_value=int(sp_value),
                tshirt_size=tshirt_size,
                mapping_rule=rule,
                evidence_refs=[evidence],
            )
        )

    return result_items, warnings
