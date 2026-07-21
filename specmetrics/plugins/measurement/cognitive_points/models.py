from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EvidenceRef(BaseModel):
    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class MeasurementWarning(BaseModel):
    code: str
    message: str
    details: dict[str, str] | None = None


class MeasurementMetadata(BaseModel):
    total_elements_processed: int = 0
    csm_element_count: int = 0
    cfm_element_count: int = 0
    bloom_distribution: dict[str, int] = {}
    duration_ms: float = 0.0
    warnings: list[MeasurementWarning] = []
    calibration_profile_applied: str = "built-in"


class CognitiveContribution(BaseModel):
    element_id: str
    element_type: str
    element_name: str
    model_source: Literal["cfm", "csm"]
    bloom_level: str
    cognitive_weight: float
    content_token_count: int = 0
    content_score: float = 0.0
    partial_score: float
    evidence_ref: EvidenceRef | None = None

    @model_validator(mode="after")
    def validate_partial_score(self) -> CognitiveContribution:
        expected = self.cognitive_weight + self.content_score
        if abs(self.partial_score - expected) > 0.001:
            raise ValueError(
                f"partial_score ({self.partial_score}) must equal "
                f"cognitive_weight ({self.cognitive_weight}) + content_score ({self.content_score}) = {expected}"
            )
        return self


class SpecificationReviewEffort(BaseModel):
    total_raw: float = 0.0
    contributions: list[CognitiveContribution] = []
    bloom_breakdown: dict[str, int] = {}


class FunctionalValidationEffort(BaseModel):
    total_raw: float = 0.0
    contributions: list[CognitiveContribution] = []
    bloom_breakdown: dict[str, int] = {}


class FibonacciNormalizationResult(BaseModel):
    raw_score: float
    threshold_applied: float
    output_value: int


class CognitivePointsMeasurement(BaseModel):
    run_id: str
    total_cognitive_points: int
    raw_score: float
    specification_review_effort: SpecificationReviewEffort
    functional_validation_effort: FunctionalValidationEffort
    fibonacci_normalization: FibonacciNormalizationResult
    calibration_version: str = "1.0"
    measurement_metadata: MeasurementMetadata
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_raw_score(self) -> CognitivePointsMeasurement:
        expected_raw = (
            self.specification_review_effort.total_raw
            + self.functional_validation_effort.total_raw
        )
        if abs(self.raw_score - expected_raw) > 0.001:
            raise ValueError(
                f"raw_score ({self.raw_score}) must equal specification_review_effort.total_raw "
                f"({self.specification_review_effort.total_raw}) + "
                f"functional_validation_effort.total_raw "
                f"({self.functional_validation_effort.total_raw})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self) -> CognitivePointsMeasurement:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self


def aggregate(
    measurements: list[CognitivePointsMeasurement],
) -> CognitivePointsMeasurement:
    if not measurements:
        raise ValueError("Cannot aggregate empty list of measurements")

    run_ids = [m.run_id for m in measurements]
    total_spec = sum(m.specification_review_effort.total_raw for m in measurements)
    total_func = sum(m.functional_validation_effort.total_raw for m in measurements)
    total_raw = total_spec + total_func

    all_spec_contribs: list[CognitiveContribution] = []
    all_func_contribs: list[CognitiveContribution] = []
    total_csm = 0
    total_cfm = 0
    merged_bloom_dist: dict[str, int] = {}
    all_warnings: list[MeasurementWarning] = []

    for m in measurements:
        all_spec_contribs.extend(m.specification_review_effort.contributions)
        all_func_contribs.extend(m.functional_validation_effort.contributions)
        total_csm += m.measurement_metadata.csm_element_count
        total_cfm += m.measurement_metadata.cfm_element_count
        for level, count in m.measurement_metadata.bloom_distribution.items():
            merged_bloom_dist[level] = merged_bloom_dist.get(level, 0) + count
        all_warnings.extend(m.measurement_metadata.warnings)

    combined_spec_breakdown: dict[str, int] = {}
    for m in measurements:
        for level, count in m.specification_review_effort.bloom_breakdown.items():
            combined_spec_breakdown[level] = (
                combined_spec_breakdown.get(level, 0) + count
            )

    combined_func_breakdown: dict[str, int] = {}
    for m in measurements:
        for level, count in m.functional_validation_effort.bloom_breakdown.items():
            combined_func_breakdown[level] = (
                combined_func_breakdown.get(level, 0) + count
            )

    from .fibonacci_normalizer import normalize

    fib_result = normalize(total_raw)

    return CognitivePointsMeasurement(
        run_id=f"aggregated:{','.join(run_ids)}",
        total_cognitive_points=fib_result.output_value,
        raw_score=total_raw,
        specification_review_effort=SpecificationReviewEffort(
            total_raw=total_spec,
            contributions=all_spec_contribs,
            bloom_breakdown=combined_spec_breakdown,
        ),
        functional_validation_effort=FunctionalValidationEffort(
            total_raw=total_func,
            contributions=all_func_contribs,
            bloom_breakdown=combined_func_breakdown,
        ),
        fibonacci_normalization=fib_result,
        measurement_metadata=MeasurementMetadata(
            total_elements_processed=total_csm + total_cfm,
            csm_element_count=total_csm,
            cfm_element_count=total_cfm,
            bloom_distribution=merged_bloom_dist,
            warnings=all_warnings,
        ),
    )
