from __future__ import annotations

import pytest

from specmetrics.plugins.measurement.storypoints._aggregate import aggregate
from specmetrics.plugins.measurement.storypoints._evidence import MeasurementWarning
from specmetrics.plugins.measurement.storypoints._metadata import ExecutionMetadata
from specmetrics.plugins.measurement.storypoints._result import (
    StoryPointMeasurementResult,
)
from specmetrics.plugins.measurement.storypoints._workitem import WorkItem


def _item(elem_id: str, raw: float, normalized: int) -> WorkItem:
    return WorkItem(
        element_id=elem_id,
        element_name=elem_id,
        element_type="functional_process",
        source_model="CFM",
        raw_score=raw,
        normalized_value=normalized,
        structural_score=raw,
        content_score=0.0,
    )


def _result(
    run_id: str,
    items: list[WorkItem],
    *,
    duration_ms: float = 10.0,
    content_multiplier: float = 0.1,
    calibration_version: str = "1.0",
    csm_elements: int = 0,
    merged: int = 0,
    no_weight: int = 0,
    tokens: dict[str, int] | None = None,
    warnings: list[MeasurementWarning] | None = None,
) -> StoryPointMeasurementResult:
    total_sp = sum(i.normalized_value for i in items)
    total_raw = sum(i.raw_score for i in items)
    fps = sum(1 for i in items if i.element_type == "functional_process")
    spec_effort = float(csm_elements)
    dist: dict[int, int] = {}
    for i in items:
        dist[i.normalized_value] = dist.get(i.normalized_value, 0) + 1
    return StoryPointMeasurementResult(
        run_id=run_id,
        total_story_points=total_sp,
        total_raw_score=total_raw,
        specification_effort_total=spec_effort,
        implementation_effort_total=total_raw - spec_effort,
        content_multiplier=content_multiplier,
        content_tokens_by_type=tokens or {},
        calibration_version=calibration_version,
        items=items,
        distribution=dist,
        execution_metadata=ExecutionMetadata(
            duration_ms=duration_ms,
            total_elements_processed=len(items) + csm_elements,
            cfm_elements_processed=len(items),
            csm_elements_processed=csm_elements,
            total_fps_processed=fps + merged,
            fps_estimated=fps,
            fps_merged_as_duplicates=merged,
            elements_without_base_weight=no_weight,
        ),
        warnings=warnings or [],
    )


def test_aggregate_empty_list_raises_exact_message() -> None:
    """Mutmut 2/3/4/5: empty input raises ValueError with the exact message."""
    with pytest.raises(ValueError) as excinfo:
        aggregate([])
    assert str(excinfo.value) == "Cannot aggregate empty list of measurements"


def test_aggregate_sums_durations_and_counts() -> None:
    """Mutmut 13/27/36/38/44/45/50/51/56/57/58/59/60/61/65/66/70/94/96/97/98/101/102/104/113/114/116/119/120/122/123/124/125."""
    m1 = _result(
        "r1",
        [_item("a", 5.0, 1), _item("b", 7.0, 2)],
        duration_ms=10.125,
        content_multiplier=0.2,
        calibration_version="v1",
        csm_elements=2,
        merged=1,
        no_weight=1,
        tokens={"operation": 3},
        warnings=[MeasurementWarning(code="W1", message="first")],
    )
    m2 = _result(
        "r2",
        [_item("c", 6.0, 2)],
        duration_ms=20.1234,
        content_multiplier=0.3,
        calibration_version="v2",
        csm_elements=3,
        merged=2,
        no_weight=2,
        tokens={"operation": 4},
        warnings=[MeasurementWarning(code="W2", message="second")],
    )
    agg = aggregate([m1, m2])
    assert agg.run_id == "aggregated:r1,r2"
    assert agg.content_multiplier == 0.2
    assert agg.calibration_version == "v1"
    assert agg.execution_metadata.duration_ms == round(10.125 + 20.1234, 2)
    assert agg.execution_metadata.total_elements_processed == 8
    assert agg.execution_metadata.cfm_elements_processed == 3
    assert agg.execution_metadata.csm_elements_processed == 5
    assert agg.execution_metadata.fps_merged_as_duplicates == 3
    assert agg.execution_metadata.elements_without_base_weight == 3
    assert agg.specification_effort_total == 5.0
    assert agg.content_tokens_by_type == {"operation": 7}
    assert [w.code for w in agg.warnings] == ["W1", "W2"]
