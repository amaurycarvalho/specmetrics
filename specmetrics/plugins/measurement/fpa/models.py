"""Data models for the FPA measurement plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

FunctionType = Literal["ILF", "EIF", "EI", "EO", "EQ"]
ComplexityRating = Literal["Low", "Average", "High"]


class EvidenceRef(BaseModel):
    """Reference to the evidence supporting a measured function."""

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class MeasurementWarning(BaseModel):
    """A non-fatal warning raised during FPA measurement."""

    code: str
    message: str
    cfm_element_id: str | None = None
    details: dict[str, str] | None = None


class MeasurementError(BaseModel):
    """An error raised during FPA measurement."""

    code: str
    message: str
    cfm_element_id: str | None = None
    recoverable: bool = False


class MeasuredFunction(BaseModel):
    """A single function measured in Function Point Analysis."""

    id: str
    name: str
    function_type: FunctionType
    complexity: ComplexityRating
    det_count: int
    ret_count: int | None = None
    ftr_count: int | None = None
    ufp_weight: int
    cfm_element_id: str
    cfm_element_type: str
    evidence_refs: list[EvidenceRef] = []
    rule_applied: str | None = None

    @model_validator(mode="after")
    def validate_counts_by_type(self: Self) -> MeasuredFunction:
        """Validate that ret/ftr counts match the function type."""
        if self.function_type in ("ILF", "EIF") and self.ret_count is None:
            raise ValueError(
                f"Data function {self.function_type} requires ret_count"
            )
        if self.function_type in ("EI", "EO", "EQ") and self.ftr_count is None:
            raise ValueError(
                f"Transactional function {self.function_type} requires ftr_count"
            )
        if self.det_count < 1:
            raise ValueError("det_count must be >= 1")
        return self


class TypeBreakdown(BaseModel):
    """Count and total UFP for a single function type."""

    count: int
    total_ufp: int


class ComplexityDistributionRow(BaseModel):
    """UFP distribution for a single type/complexity combination."""

    function_type: FunctionType
    complexity: ComplexityRating
    count: int
    ufp_per_function: int
    total_ufp: int


class MeasurementSummary(BaseModel):
    """Aggregated summary of an FPA measurement run."""

    total_function_count: int
    total_ufp: int
    adjusted_fp: int | None = None
    vaf: float | None = None
    by_type: dict[FunctionType, TypeBreakdown] = {}
    by_complexity: dict[ComplexityRating, int] = {}
    complexity_distribution: list[ComplexityDistributionRow] = []


class MeasurementExplanation(BaseModel):
    """Explanation of how a single function was measured."""

    function_id: str
    cfm_element_id: str
    cfm_element_name: str
    classification_reason: str
    complexity_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class FPAMeasurementResult(BaseModel):
    """Full result of an FPA measurement run."""

    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: str | None = None
    measured_functions: list[MeasuredFunction] = []
    summary: MeasurementSummary
    explanations: list[MeasurementExplanation] = []
    warnings: list[MeasurementWarning] = []
    errors: list[MeasurementError] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_consistency(self: Self) -> FPAMeasurementResult:
        """Validate internal consistency of the measurement result."""
        if self.errors and self.summary.total_ufp is not None:
            raise ValueError("Cannot have total_ufp when errors are present")
        ids = [f.id for f in self.measured_functions]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate measured_function ids")
        if self.summary.total_function_count != len(self.measured_functions):
            raise ValueError(
                "summary.total_function_count must match len(measured_functions)"
            )
        return self


class RulePack(BaseModel):
    """Rule pack that tunes FPA measurement behavior."""

    id: str
    methodology: str = "FPA"
    complexity_overrides: dict[str, dict[str, list[int]]] | None = None
    weight_overrides: dict[str, dict[str, int]] | None = None
    excluded_types: list[FunctionType] = []
    element_exclusions: dict[str, list[str]] | None = None
    vaf: dict[str, int] | None = None
