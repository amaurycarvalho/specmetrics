"""Data models for the SFP measurement plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

ComponentType = Literal["functional_process", "logical_function"]


class EvidenceRef(BaseModel):
    """Reference to the evidence supporting a measured component."""

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class MeasurementWarning(BaseModel):
    """A non-fatal warning raised during SFP measurement."""

    code: str
    message: str
    cfm_element_id: str | None = None
    details: dict[str, str] | None = None


class MeasurementError(BaseModel):
    """An error raised during SFP measurement."""

    code: str
    message: str
    cfm_element_id: str | None = None
    recoverable: bool = False


class MeasuredComponent(BaseModel):
    """A single component measured for Simple Function Points."""

    id: str
    name: str
    component_type: ComponentType
    contribution: float
    cfm_element_id: str
    cfm_element_type: str
    evidence_refs: list[EvidenceRef] = []
    rule_applied: str | None = None

    @model_validator(mode="after")
    def validate_component(self: Self) -> MeasuredComponent:
        """Validate that the component contribution is positive."""
        if self.contribution <= 0:
            raise ValueError("contribution must be a positive number")
        return self


class TypeBreakdown(BaseModel):
    """Count and total SFP for a single component type."""

    count: int
    total_sfp: float


class MeasurementSummary(BaseModel):
    """Aggregated summary of an SFP measurement run."""

    total_component_count: int
    total_sfp: float
    by_type: dict[ComponentType, TypeBreakdown] = {}


class MeasurementExplanation(BaseModel):
    """Explanation of how a single component was measured."""

    component_id: str
    cfm_element_id: str
    cfm_element_name: str
    identification_reason: str
    contribution_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class SFPMeasurementResult(BaseModel):
    """Full result of an SFP measurement run."""

    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: str | None = None
    measured_components: list[MeasuredComponent] = []
    summary: MeasurementSummary
    explanations: list[MeasurementExplanation] = []
    warnings: list[MeasurementWarning] = []
    errors: list[MeasurementError] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_consistency(self: Self) -> SFPMeasurementResult:
        """Validate internal consistency of the measurement result."""
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
    """Rule pack that tunes SFP measurement behavior."""

    id: str
    methodology: str = "SFP"
    contribution_overrides: dict[ComponentType, float] | None = None
    excluded_types: list[str] = []
    inclusion_criteria: dict[str, dict[str, list[str]]] | None = None
    element_exclusions: dict[str, list[str]] | None = None
    element_inclusions: dict[str, list[str]] | None = None
