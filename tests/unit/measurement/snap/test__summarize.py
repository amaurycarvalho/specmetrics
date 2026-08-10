from __future__ import annotations

from types import SimpleNamespace

from specmetrics.plugins.measurement.snap.assessor import SNAPAssessor
from specmetrics.plugins.measurement.snap.models import (
    AssessedItem,
    AssessmentSummary,
    SNAPMeasurementResult,
)


def _item(
    item_id: str,
    category_id: str,
    contribution: float = 4.0,
    excluded: bool = False,
) -> AssessedItem:
    return AssessedItem(
        id=f"snap-item-{item_id}",
        name=f"name-{item_id}",
        category_id=category_id,  # type: ignore[arg-type]
        contribution=contribution,
        cfm_element_id=f"elem-{item_id}",
        cfm_semantic_marker="presentation_interface",
        excluded=excluded,
    )


def _previous_result(items: list[AssessedItem]) -> SNAPMeasurementResult:
    return SNAPMeasurementResult(
        run_id="previous",
        cfm_run_id="cfm",
        assessed_items=items,
        summary=AssessmentSummary(
            total_item_count=len(items),
            total_active_count=sum(1 for i in items if not i.excluded),
            total_snap=sum(i.contribution for i in items if not i.excluded),
        ),
    )


def _mixin() -> SNAPAssessor:
    return SNAPAssessor()


def test_merge_previous_returns_early_when_previous_is_none() -> None:
    """Mutmut 2: passing previous_result=None must leave items untouched."""
    assessor = _mixin()
    items = [_item("a", "presentation")]
    assessor._merge_previous(items, None, ["b"])
    assert [i.cfm_element_id for i in items] == ["elem-a"]


def test_merge_previous_returns_early_when_modified_ids_none() -> None:
    """Mutmut 1/3: passing modified_element_ids=None must leave items untouched."""
    assessor = _mixin()
    items = [_item("a", "presentation")]
    previous = _previous_result([_item("b", "presentation")])
    assessor._merge_previous(items, previous, None)
    assert [i.cfm_element_id for i in items] == ["elem-a"]


def test_merge_previous_appends_unmodified_existing_items() -> None:
    """Mutmut 8/10: only unmodified items missing from current items are appended."""
    assessor = _mixin()
    items = [_item("a", "presentation")]
    previous = _previous_result([_item("b", "presentation"), _item("c", "presentation")])
    assessor._merge_previous(items, previous, ["elem-b"])
    merged = [i.cfm_element_id for i in items]
    assert merged == ["elem-a", "elem-c"]
    assert all(isinstance(i, AssessedItem) for i in items)


def test_collect_elements_gathers_all_collections() -> None:
    """Mutmut 3/4/5/6: each collection element must be appended as a tuple."""
    cfm = SimpleNamespace(
        operations={"o1": "op"},
        data_groups={"d1": "dg"},
        functional_processes={"f1": "fp"},
        business_rules={"b1": "br"},
        actors={"a1": "act"},
        unclassified={"u1": "un"},
    )
    elements = _mixin()._collect_elements(cfm)
    assert len(elements) == 6
    assert ("o1", "op") in elements
    assert ("u1", "un") in elements
    assert all(isinstance(e, tuple) and len(e) == 2 for e in elements)


def test_build_categories_skips_empty_categories() -> None:
    """Mutmut 8/10: categories with no items must be omitted from the result."""
    cats = _mixin()._build_categories([_item("a", "presentation")])
    assert len(cats) == 1
    assert cats[0].category_id == "presentation"


def test_build_categories_continues_past_empty_categories() -> None:
    """Mutmut 12: an empty category must not stop later categories from being built."""
    item = _item("a", "data_operations")
    cats = _mixin()._build_categories([item])
    assert len(cats) == 1
    assert cats[0].category_id == "data_operations"
    assert cats[0].items == [item]


def test_build_summary_breakdown_counts_and_totals() -> None:
    """Mutmut 14/15/16/17/18/19/20/21/29: summary counts and SNAP totals."""
    items = [
        _item("1", "presentation", 4.0),
        _item("2", "presentation", 4.0),
        _item("3", "data_operations", contribution=0.0, excluded=True),
    ]
    summary = _mixin()._build_summary(items)
    assert summary.total_item_count == 3
    assert summary.total_active_count == 2
    assert summary.total_snap == 8.0
    assert summary.by_category["presentation"].item_count == 2
    assert summary.by_category["presentation"].total_snap == 8.0
    assert summary.by_category["data_operations"].item_count == 1
    assert summary.by_category["data_operations"].total_snap == 0.0
