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
    unknown_csm_element_count: int = 0
    unknown_cfm_element_count: int = 0
    duration_ms: float = 0.0
    warnings: list[MeasurementWarning] = []
    calibration_profile_applied: str = "built-in"


class TokenContribution(BaseModel):
    element_id: str
    element_type: str
    element_name: str
    model_source: Literal["cfm", "csm"]
    applied_weight: float
    content_token_count: int = 0
    content_score: float = 0.0
    partial_score: float
    evidence_ref: EvidenceRef | None = None

    @model_validator(mode="after")
    def validate_partial_score(self) -> TokenContribution:
        expected = self.applied_weight + self.content_score
        if abs(self.partial_score - expected) > 1e-9:
            raise ValueError(
                f"partial_score ({self.partial_score}) must equal "
                f"applied_weight ({self.applied_weight}) + content_score ({self.content_score}) = {expected}"
            )
        return self


class SpecificationCost(BaseModel):
    total: float = 0.0
    contributions: list[TokenContribution] = []


class CodeGenerationCost(BaseModel):
    total: float = 0.0
    contributions: list[TokenContribution] = []


class TokenPointsMeasurement(BaseModel):
    run_id: str
    total_score: float
    specification_cost: SpecificationCost
    code_generation_cost: CodeGenerationCost
    calibration_version: str = "1.0"
    measurement_metadata: MeasurementMetadata
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_total(self) -> TokenPointsMeasurement:
        if (
            self.total_score
            != self.specification_cost.total + self.code_generation_cost.total
        ):
            raise ValueError(
                f"total_score ({self.total_score}) must equal specification_cost.total "
                f"({self.specification_cost.total}) + code_generation_cost.total "
                f"({self.code_generation_cost.total})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self) -> TokenPointsMeasurement:
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self


def aggregate(measurements: list[TokenPointsMeasurement]) -> TokenPointsMeasurement:
    if not measurements:
        raise ValueError("Cannot aggregate empty list of measurements")

    run_ids = [m.run_id for m in measurements]
    total_spec = sum(m.specification_cost.total for m in measurements)
    total_code = sum(m.code_generation_cost.total for m in measurements)

    all_spec_contribs: list[TokenContribution] = []
    all_code_contribs: list[TokenContribution] = []
    total_csm = 0
    total_cfm = 0
    total_unknown_csm = 0
    total_unknown_cfm = 0
    all_warnings: list[MeasurementWarning] = []

    for m in measurements:
        all_spec_contribs.extend(m.specification_cost.contributions)
        all_code_contribs.extend(m.code_generation_cost.contributions)
        total_csm += m.measurement_metadata.csm_element_count
        total_cfm += m.measurement_metadata.cfm_element_count
        total_unknown_csm += m.measurement_metadata.unknown_csm_element_count
        total_unknown_cfm += m.measurement_metadata.unknown_cfm_element_count
        all_warnings.extend(m.measurement_metadata.warnings)

    return TokenPointsMeasurement(
        run_id=f"aggregated:{','.join(run_ids)}",
        total_score=total_spec + total_code,
        specification_cost=SpecificationCost(
            total=total_spec, contributions=all_spec_contribs
        ),
        code_generation_cost=CodeGenerationCost(
            total=total_code, contributions=all_code_contribs
        ),
        measurement_metadata=MeasurementMetadata(
            total_elements_processed=total_csm + total_cfm,
            csm_element_count=total_csm,
            cfm_element_count=total_cfm,
            unknown_csm_element_count=total_unknown_csm,
            unknown_cfm_element_count=total_unknown_cfm,
            warnings=all_warnings,
        ),
    )
