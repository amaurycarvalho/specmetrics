from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

ComponentType = Literal["functional_process", "logical_function"]


class EvidenceRef(BaseModel):
    graph_node_id: str
    document_id: str
    section_id: Optional[str] = None
    text: str


class MeasurementWarning(BaseModel):
    code: str
    message: str
    cfm_element_id: Optional[str] = None
    details: Optional[dict[str, str]] = None


class MeasurementError(BaseModel):
    code: str
    message: str
    cfm_element_id: Optional[str] = None
    recoverable: bool = False


class MeasuredComponent(BaseModel):
    id: str
    name: str
    component_type: ComponentType
    contribution: float
    cfm_element_id: str
    cfm_element_type: str
    evidence_refs: list[EvidenceRef] = []
    rule_applied: Optional[str] = None

    @model_validator(mode="after")
    def validate_component(self) -> MeasuredComponent:
        if self.contribution <= 0:
            raise ValueError("contribution must be a positive number")
        return self


class TypeBreakdown(BaseModel):
    count: int
    total_sfp: float


class MeasurementSummary(BaseModel):
    total_component_count: int
    total_sfp: float
    by_type: dict[ComponentType, TypeBreakdown] = {}


class MeasurementExplanation(BaseModel):
    component_id: str
    cfm_element_id: str
    cfm_element_name: str
    identification_reason: str
    contribution_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class SFPMeasurementResult(BaseModel):
    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: Optional[str] = None
    measured_components: list[MeasuredComponent] = []
    summary: MeasurementSummary
    explanations: list[MeasurementExplanation] = []
    warnings: list[MeasurementWarning] = []
    errors: list[MeasurementError] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_consistency(self) -> SFPMeasurementResult:
        if self.errors and self.summary.total_sfp is not None:
            raise ValueError("Cannot have total_sfp when errors are present")
        ids = [c.id for c in self.measured_components]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate measured_component ids")
        if self.summary.total_component_count != len(self.measured_components):
            raise ValueError(
                "summary.total_component_count must match len(measured_components)"
            )
        return self


class RulePack(BaseModel):
    id: str
    methodology: str = "SFP"
    contribution_overrides: Optional[dict[ComponentType, float]] = None
    excluded_types: list[str] = []
    inclusion_criteria: Optional[dict[str, dict[str, list[str]]]] = None
    element_exclusions: Optional[dict[str, list[str]]] = None
    element_inclusions: Optional[dict[str, list[str]]] = None
