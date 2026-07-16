from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    document_id: str
    section_id: str | None = None
    text: str
    node_id: str
    confidence: float | None = None


class AppliedRule(BaseModel):
    rule_pack_id: str
    rule_id: str
    rule_type: str
    description: str = ""
    effect: str = ""


class ElementContribution(BaseModel):
    element_id: str
    element_type: str
    element_label: str
    complexity: str | None = None
    weight: int | None = None
    evidence: list[EvidenceReference] = []
    applied_rules: list[AppliedRule] = []


class MetricExplanation(BaseModel):
    metric_name: str
    metric_value: int | float
    computation_summary: str = ""
    elements: list[ElementContribution] = []
    applied_rules: list[AppliedRule] = []


class ExplanationSummary(BaseModel):
    total_metrics: int = 0
    total_elements: int = 0
    total_evidence_refs: int = 0
    total_rules_applied: int = 0
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MeasurementExplanation(BaseModel):
    run_id: str
    spec_path: str = ""
    measured_at: datetime | None = None
    metrics: list[MetricExplanation] = []
    applied_rules: list[AppliedRule] = []
    summary: ExplanationSummary = Field(default_factory=ExplanationSummary)


class ElementChange(BaseModel):
    element_id: str
    change_type: str
    baseline_state: dict[str, Any] = {}
    comparison_state: dict[str, Any] = {}


class MetricChange(BaseModel):
    metric_name: str
    baseline_value: int | float
    comparison_value: int | float
    delta: int | float = 0
    changed_elements: list[ElementChange] = []


class ExplanationComparison(BaseModel):
    baseline_run_id: str
    comparison_run_id: str
    changed_metrics: list[MetricChange] = []
    added_metrics: list[str] = []
    removed_metrics: list[str] = []
    unchanged_metrics: list[str] = []
    summary: str = ""
