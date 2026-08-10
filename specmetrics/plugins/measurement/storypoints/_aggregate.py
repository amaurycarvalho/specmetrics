"""Aggregation helper for Story Points measurements."""
from __future__ import annotations

from ._evidence import MeasurementWarning
from ._metadata import ExecutionMetadata
from ._result import StoryPointMeasurementResult
from ._workitem import WorkItem


def aggregate(
    measurements: list[StoryPointMeasurementResult],
) -> StoryPointMeasurementResult:
    """Aggregate multiple measurements into a single Story Points result."""
    if not measurements:
        raise ValueError("Cannot aggregate empty list of measurements")

    run_ids = [m.run_id for m in measurements]
    all_items: list[WorkItem] = []
    total_raw = 0.0
    total_sp = 0
    total_duration = 0.0
    total_elements = 0
    total_cfm = 0
    total_csm = 0
    total_fps = 0
    total_estimated = 0
    total_merged = 0
    total_no_weight = 0
    total_spec_effort = 0.0
    total_impl_effort = 0.0
    combined_tokens_by_type: dict[str, int] = {}
    all_warnings: list[MeasurementWarning] = []
    combined_dist: dict[int, int] = {}
    content_mult = measurements[0].content_multiplier
    cal_version = measurements[0].calibration_version

    for m in measurements:
        all_items.extend(m.items)
        total_raw += m.total_raw_score
        total_sp += m.total_story_points
        total_duration += m.execution_metadata.duration_ms
        total_elements += m.execution_metadata.total_elements_processed
        total_cfm += m.execution_metadata.cfm_elements_processed
        total_csm += m.execution_metadata.csm_elements_processed
        total_fps += m.execution_metadata.total_fps_processed
        total_estimated += m.execution_metadata.fps_estimated
        total_merged += m.execution_metadata.fps_merged_as_duplicates
        total_no_weight += m.execution_metadata.elements_without_base_weight
        total_spec_effort += m.specification_effort_total
        total_impl_effort += m.implementation_effort_total
        for etype, count in m.content_tokens_by_type.items():
            combined_tokens_by_type[etype] = (
                combined_tokens_by_type.get(etype, 0) + count
            )
        all_warnings.extend(m.warnings)
        for val, cnt in m.distribution.items():
            combined_dist[val] = combined_dist.get(val, 0) + cnt

    return StoryPointMeasurementResult(
        run_id=f"aggregated:{','.join(run_ids)}",
        total_story_points=total_sp,
        total_raw_score=total_raw,
        specification_effort_total=total_spec_effort,
        implementation_effort_total=total_impl_effort,
        content_multiplier=content_mult,
        content_tokens_by_type=combined_tokens_by_type,
        calibration_version=cal_version,
        items=all_items,
        distribution=combined_dist,
        execution_metadata=ExecutionMetadata(
            duration_ms=round(total_duration, 2),
            total_elements_processed=total_elements,
            cfm_elements_processed=total_cfm,
            csm_elements_processed=total_csm,
            total_fps_processed=total_fps,
            fps_estimated=total_estimated,
            fps_merged_as_duplicates=total_merged,
            elements_without_base_weight=total_no_weight,
        ),
        warnings=all_warnings,
    )