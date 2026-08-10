"""Data models for T-Shirt sizing."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator


class MeasurementEvidence(BaseModel):
    """Evidence captured for a single T-Shirt classified item."""

    element_id: str
    story_point_value: int
    mapping_rule: str = ""
    document_id: str = ""
    section_id: str | None = None


class MeasurementWarning(BaseModel):
    """Warning raised during T-Shirt classification."""

    code: str
    message: str
    element_id: str | None = None


class TShirtSize(BaseModel):
    """A single t-shirt size with its story point range."""

    label: str
    story_point_range: tuple[int, int]
    ordinal: int

    @model_validator(mode="after")
    def validate_range(self: Self) -> TShirtSize:
        """Validate that the story point range minimum is not above its maximum."""
        mn, mx = self.story_point_range
        if mn > mx:
            raise ValueError(
                f"story_point_range ({self.story_point_range}) must have min ≤ max"
            )
        return self


class FunctionalWorkItem(BaseModel):
    """A work item classified into a t-shirt size."""

    element_id: str
    element_name: str
    story_point_value: int
    tshirt_size: str
    mapping_rule: str = ""
    evidence_refs: list[MeasurementEvidence] = []
    applied_rule_pack: str = "default"


class ExecutionMetadata(BaseModel):
    """Execution metadata for a T-Shirt classification run."""

    duration_ms: float = 0.0
    total_fps_processed: int = 0
    version: str = "1.0"


class TShirtMeasurementResult(BaseModel):
    """Complete T-Shirt classification measurement result."""

    run_id: str
    method: str = "TShirtSizing"
    scale: str = "XS-S-M-L-XL-XXL"
    total_items: int = 0
    items: list[FunctionalWorkItem] = []
    distribution: dict[str, int] = {}
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    source_measurement_run_id: str = ""
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_total_items(self: Self) -> TShirtMeasurementResult:
        """Validate that the total items count matches the items list length."""
        if self.total_items != len(self.items):
            raise ValueError(
                f"total_items ({self.total_items}) must equal len(items) ({len(self.items)})"
            )
        return self

    @model_validator(mode="after")
    def validate_distribution(self: Self) -> TShirtMeasurementResult:
        """Validate that the distribution aggregates to match the items."""
        expected: dict[str, int] = {}
        for item in self.items:
            expected[item.tshirt_size] = expected.get(item.tshirt_size, 0) + 1
        if self.distribution != expected:
            raise ValueError(
                f"distribution ({self.distribution}) must aggregate to match items "
                f"({expected})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self: Self) -> TShirtMeasurementResult:
        """Validate that the run id is not empty."""
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self
