from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator


class EvidenceRef(BaseModel):
    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class MeasurementWarning(BaseModel):
    code: str
    message: str
    element_id: str | None = None


class MeasurementEvidence(BaseModel):
    element_id: str
    document_id: str
    section_id: str | None = None
    applied_rule: str = ""
    text: str = ""


class RawEffortScore(BaseModel):
    value: float
    factor_breakdown: dict[str, float]
    factor_coefficients: dict[str, float]


class StoryPointEstimate(BaseModel):
    value: int
    raw_score: float
    normalization_rule: str = "default_threshold_v1"


class WorkItem(BaseModel):
    element_id: str
    element_name: str
    element_type: str = "functional_process"
    source_model: str = "CFM"
    raw_score: float
    normalized_value: int
    rank_position: int = 0
    structural_score: float = 0.0
    content_tokens: int = 0
    content_score: float = 0.0
    factor_breakdown: dict[str, float] = Field(default_factory=dict)
    base_weight: float | None = None
    applied_rules: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_raw_score(self) -> WorkItem:
        expected = self.structural_score + self.content_score
        if abs(self.raw_score - expected) > 0.001:
            raise ValueError(
                f"raw_score ({self.raw_score}) must equal structural_score "
                f"({self.structural_score}) + content_score ({self.content_score}) "
                f"= {expected}"
            )
        return self

    @model_validator(mode="after")
    def validate_factor_or_base_weight(self) -> WorkItem:
        is_fp = self.element_type == "functional_process"
        if is_fp and self.factor_breakdown and self.base_weight is not None:
            raise ValueError(
                "functional_process items must not have base_weight"
            )
        if is_fp and self.factor_breakdown:
            fb_sum = sum(self.factor_breakdown.values())
            if abs(fb_sum - self.structural_score) > 0.001:
                raise ValueError(
                    f"sum of factor_breakdown ({fb_sum}) must equal "
                    f"structural_score ({self.structural_score})"
                )
        if not is_fp and self.base_weight is not None and self.factor_breakdown:
            raise ValueError(
                "non-FP items must not have factor_breakdown"
            )
        return self


class ExecutionMetadata(BaseModel):
    duration_ms: float = 0.0
    total_elements_processed: int = 0
    cfm_elements_processed: int = 0
    csm_elements_processed: int = 0
    total_fps_processed: int = 0
    fps_estimated: int = 0
    fps_merged_as_duplicates: int = 0
    elements_without_base_weight: int = 0
    version: str = "1.0"

    @model_validator(mode="after")
    def validate_counts(self) -> ExecutionMetadata:
        if (
            self.total_fps_processed
            != self.fps_estimated + self.fps_merged_as_duplicates
        ):
            raise ValueError(
                f"total_fps_processed ({self.total_fps_processed}) must equal "
                f"fps_estimated ({self.fps_estimated}) + "
                f"fps_merged_as_duplicates ({self.fps_merged_as_duplicates})"
            )
        if (
            self.cfm_elements_processed + self.csm_elements_processed
            != self.total_elements_processed
        ):
            if self.total_elements_processed != 0:
                raise ValueError(
                    f"total_elements_processed ({self.total_elements_processed}) "
                    f"must equal cfm_elements_processed + csm_elements_processed "
                    f"({self.cfm_elements_processed} + {self.csm_elements_processed})"
                )
        if self.total_elements_processed > 0:
            expected_total = self.cfm_elements_processed + self.csm_elements_processed
            if self.total_elements_processed != expected_total:
                raise ValueError(
                    f"total_elements_processed ({self.total_elements_processed}) "
                    f"must equal cfm_elements_processed + csm_elements_processed "
                    f"({expected_total})"
                )
        return self


class StoryPointMeasurementResult(BaseModel):
    run_id: str
    method: str = "StoryPoints"
    scale: str = "ModifiedFibonacci"
    total_story_points: int = 0
    total_raw_score: float = 0.0
    specification_effort_total: float = 0.0
    implementation_effort_total: float = 0.0
    content_multiplier: float = 0.1
    content_tokens_by_type: dict[str, int] = Field(default_factory=dict)
    calibration_version: str = "1.0"
    items: list[WorkItem] = Field(default_factory=list)
    distribution: dict[int, int] = Field(default_factory=dict)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    warnings: list[MeasurementWarning] = Field(default_factory=list)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_total_story_points(self) -> StoryPointMeasurementResult:
        expected = sum(item.normalized_value for item in self.items)
        if self.total_story_points != expected:
            raise ValueError(
                f"total_story_points ({self.total_story_points}) must equal "
                f"sum of item normalized values ({expected})"
            )
        return self

    @model_validator(mode="after")
    def validate_distribution(self) -> StoryPointMeasurementResult:
        expected: dict[int, int] = {}
        for item in self.items:
            nv = item.normalized_value
            expected[nv] = expected.get(nv, 0) + 1
        if self.distribution != expected:
            raise ValueError(
                f"distribution ({self.distribution}) must match "
                f"aggregated item values ({expected})"
            )
        return self

    @model_validator(mode="after")
    def validate_raw_totals(self) -> StoryPointMeasurementResult:
        expected_raw = sum(item.raw_score for item in self.items)
        if abs(self.total_raw_score - expected_raw) > 0.001:
            raise ValueError(
                f"total_raw_score ({self.total_raw_score}) must equal "
                f"sum of item raw scores ({expected_raw})"
            )
        return self

    @model_validator(mode="after")
    def validate_effort_totals(self) -> StoryPointMeasurementResult:
        if abs(
            self.specification_effort_total + self.implementation_effort_total
            - self.total_raw_score
        ) > 0.001:
            raise ValueError(
                f"specification_effort_total + implementation_effort_total "
                f"({self.specification_effort_total} + {self.implementation_effort_total}) "
                f"must equal total_raw_score ({self.total_raw_score})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self) -> StoryPointMeasurementResult:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self


FunctionalWorkItem = WorkItem


def aggregate(
    measurements: list[StoryPointMeasurementResult],
) -> StoryPointMeasurementResult:
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
