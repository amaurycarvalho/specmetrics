"""Data models for the BCP measurement plugin."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator


class MeasurementEvidence(BaseModel):
    """Evidence reference supporting a BCP measurement item."""

    element_id: str
    document_id: str = ""
    section_id: str | None = None
    story_point_value: float | None = None
    text: str = ""


class MeasurementWarning(BaseModel):
    """A non-fatal warning raised during BCP measurement."""

    code: str
    message: str
    element_id: str | None = None


class GeneratedStory(BaseModel):
    """A user story generated from a functional process."""

    content: str
    evidence_ref: MeasurementEvidence


class SDKResult(BaseModel):
    """Result returned by the BCP calculation SDK."""

    total_bcp: float
    breakdown: dict[str, float] = {}
    raw_response: dict[str, Any] = {}
    provider: str = "openai"
    duration_ms: float = 0.0
    warnings: list[str] = []
    errors: list[str] = []


class BCPWorkItem(BaseModel):
    """A single functional process measured for Business Complexity Points."""

    element_id: str
    element_name: str
    generated_story: str
    sdk_response: dict[str, Any] = {}
    bcp_score: float
    component_breakdown: dict[str, float] = {}
    evidence_refs: list[MeasurementEvidence] = []
    status: Literal["success", "failed", "skipped"] = "success"


class ExecutionMetadata(BaseModel):
    """Execution metadata for a BCP measurement run."""

    duration_ms: float = 0.0
    total_fps_processed: int = 0
    items_succeeded: int = 0
    items_failed: int = 0
    sdk_call_count: int = 0
    sdk_errors: int = 0
    version: str = "1.0"

    @model_validator(mode="after")
    def validate_counts(self: Self) -> ExecutionMetadata:
        """Validate that processed counts reconcile with success and failure."""
        if self.total_fps_processed != self.items_succeeded + self.items_failed:
            raise ValueError(
                f"total_fps_processed ({self.total_fps_processed}) must equal "
                f"items_succeeded ({self.items_succeeded}) + "
                f"items_failed ({self.items_failed})"
            )
        return self


class BCPMeasurementResult(BaseModel):
    """Aggregated result of a BCP measurement run."""

    run_id: str
    method: str = "BCP"
    sdk_version: str = ""
    provider: str = "openai"
    items: list[BCPWorkItem] = []
    total_bcp: float = 0.0
    generated_stories: list[GeneratedStory] = []
    applied_rule_pack: str = "default"
    execution_metadata: ExecutionMetadata
    warnings: list[MeasurementWarning] = []
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_total(self: Self) -> BCPMeasurementResult:
        """Validate that total_bcp equals the sum of successful item scores."""
        expected = sum(
            item.bcp_score for item in self.items if item.status == "success"
        )
        if abs(self.total_bcp - expected) > 0.001:
            raise ValueError(
                f"total_bcp ({self.total_bcp}) must equal sum of successful "
                f"item.bcp_score ({expected})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self: Self) -> BCPMeasurementResult:
        """Validate that run_id is not empty."""
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self
