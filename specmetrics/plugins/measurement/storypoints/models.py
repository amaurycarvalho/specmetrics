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


class FunctionalWorkItem(BaseModel):
    element_id: str
    element_name: str
    raw_score: float
    normalized_value: int
    factor_breakdown: dict[str, float]
    applied_rules: list[str] = []
    evidence_refs: list[EvidenceRef] = []

    @model_validator(mode="after")
    def validate_raw_score(self) -> FunctionalWorkItem:
        expected = sum(self.factor_breakdown.values())
        if abs(self.raw_score - expected) > 0.001:
            raise ValueError(
                f"raw_score ({self.raw_score}) must equal sum of factor_breakdown "
                f"({expected})"
            )
        return self


class ExecutionMetadata(BaseModel):
    duration_ms: float = 0.0
    total_fps_processed: int = 0
    fps_estimated: int = 0
    fps_merged_as_duplicates: int = 0
    version: str = "1.0"

    @model_validator(mode="after")
    def validate_counts(self) -> ExecutionMetadata:
        if self.total_fps_processed != self.fps_estimated + self.fps_merged_as_duplicates:
            raise ValueError(
                f"total_fps_processed ({self.total_fps_processed}) must equal "
                f"fps_estimated ({self.fps_estimated}) + "
                f"fps_merged_as_duplicates ({self.fps_merged_as_duplicates})"
            )
        return self


class StoryPointMeasurementResult(BaseModel):
    run_id: str
    method: str = "StoryPoints"
    scale: str = "ModifiedFibonacci"
    total_story_points: int
    items: list[FunctionalWorkItem]
    distribution: dict[int, int] = {}
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_total(self) -> StoryPointMeasurementResult:
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
    def validate_run_id(self) -> StoryPointMeasurementResult:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self


def aggregate(
    measurements: list[StoryPointMeasurementResult],
) -> StoryPointMeasurementResult:
    if not measurements:
        raise ValueError("Cannot aggregate empty list of measurements")

    run_ids = [m.run_id for m in measurements]
    all_items: list[FunctionalWorkItem] = []
    total_duration = 0.0
    total_processed = 0
    total_estimated = 0
    total_merged = 0
    all_warnings: list[MeasurementWarning] = []

    for m in measurements:
        all_items.extend(m.items)
        total_duration += m.execution_metadata.duration_ms
        total_processed += m.execution_metadata.total_fps_processed
        total_estimated += m.execution_metadata.fps_estimated
        total_merged += m.execution_metadata.fps_merged_as_duplicates
        all_warnings.extend(m.warnings)

    total_sp = sum(i.normalized_value for i in all_items)
    dist: dict[int, int] = {}
    for i in all_items:
        dist[i.normalized_value] = dist.get(i.normalized_value, 0) + 1

    return StoryPointMeasurementResult(
        run_id=f"aggregated:{','.join(run_ids)}",
        total_story_points=total_sp,
        items=all_items,
        distribution=dist,
        execution_metadata=ExecutionMetadata(
            duration_ms=total_duration,
            total_fps_processed=total_processed,
            fps_estimated=total_estimated,
            fps_merged_as_duplicates=total_merged,
        ),
        warnings=all_warnings,
    )
