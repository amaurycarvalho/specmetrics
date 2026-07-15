from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

FunctionType = Literal["ILF", "EIF", "EI", "EO", "EQ"]
ComplexityRating = Literal["Low", "Average", "High"]


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


class MeasuredFunction(BaseModel):
    id: str
    name: str
    function_type: FunctionType
    complexity: ComplexityRating
    det_count: int
    ret_count: Optional[int] = None
    ftr_count: Optional[int] = None
    ufp_weight: int
    cfm_element_id: str
    cfm_element_type: str
    evidence_refs: list[EvidenceRef] = []
    rule_applied: Optional[str] = None

    @model_validator(mode="after")
    def validate_counts_by_type(self) -> "MeasuredFunction":
        if self.function_type in ("ILF", "EIF"):
            if self.ret_count is None:
                raise ValueError(f"Data function {self.function_type} requires ret_count")
        if self.function_type in ("EI", "EO", "EQ"):
            if self.ftr_count is None:
                raise ValueError(f"Transactional function {self.function_type} requires ftr_count")
        if self.det_count < 1:
            raise ValueError("det_count must be >= 1")
        return self


class TypeBreakdown(BaseModel):
    count: int
    total_ufp: int


class ComplexityDistributionRow(BaseModel):
    function_type: FunctionType
    complexity: ComplexityRating
    count: int
    ufp_per_function: int
    total_ufp: int


class MeasurementSummary(BaseModel):
    total_function_count: int
    total_ufp: int
    adjusted_fp: Optional[int] = None
    vaf: Optional[float] = None
    by_type: dict[FunctionType, TypeBreakdown] = {}
    by_complexity: dict[ComplexityRating, int] = {}
    complexity_distribution: list[ComplexityDistributionRow] = []


class MeasurementExplanation(BaseModel):
    function_id: str
    cfm_element_id: str
    cfm_element_name: str
    classification_reason: str
    complexity_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class APFMeasurementResult(BaseModel):
    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: Optional[str] = None
    measured_functions: list[MeasuredFunction] = []
    summary: MeasurementSummary
    explanations: list[MeasurementExplanation] = []
    warnings: list[MeasurementWarning] = []
    errors: list[MeasurementError] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_consistency(self) -> "APFMeasurementResult":
        if self.errors and self.summary.total_ufp is not None:
            raise ValueError("Cannot have total_ufp when errors are present")
        ids = [f.id for f in self.measured_functions]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate measured_function ids")
        if self.summary.total_function_count != len(self.measured_functions):
            raise ValueError("summary.total_function_count must match len(measured_functions)")
        return self


class RulePack(BaseModel):
    id: str
    methodology: str = "APF"
    complexity_overrides: Optional[dict[str, dict[str, list[int]]]] = None
    weight_overrides: Optional[dict[str, dict[str, int]]] = None
    excluded_types: list[FunctionType] = []
    element_exclusions: Optional[dict[str, list[str]]] = None
    vaf: Optional[dict[str, int]] = None
