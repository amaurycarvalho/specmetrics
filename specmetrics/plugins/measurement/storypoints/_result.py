"""Measurement result model for Story Points."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from ._evidence import MeasurementWarning
from ._metadata import ExecutionMetadata
from ._workitem import WorkItem


class StoryPointMeasurementResult(BaseModel):
    """Complete Story Points measurement result."""

    run_id: str
    method: str = "StoryPoints"
    scale: str = "ModifiedFibonacci"
    total_story_points: int = 0
    total_raw_score: float = 0.0
    specification_effort_total: float = 0.0
    implementation_effort_total: float = 0.0
    content_multiplier: float = 0.1
    content_tokens_by_type: dict[str, int] = Field(default_factory=dict)
    calibration_version: str = "1.0"
    items: list[WorkItem] = Field(default_factory=list)
    distribution: dict[int, int] = Field(default_factory=dict)
    execution_metadata: ExecutionMetadata = Field(default_factory=ExecutionMetadata)
    warnings: list[MeasurementWarning] = Field(default_factory=list)
    measured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_total_story_points(self: Self) -> StoryPointMeasurementResult:
        """Validate that the total equals the sum of item normalized values."""
        expected = sum(item.normalized_value for item in self.items)
        if self.total_story_points != expected:
            raise ValueError(
                f"total_story_points ({self.total_story_points}) must equal "
                f"sum of item normalized values ({expected})"
            )
        return self

    @model_validator(mode="after")
    def validate_distribution(self: Self) -> StoryPointMeasurementResult:
        """Validate that the distribution matches the item normalized values."""
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
    def validate_raw_totals(self: Self) -> StoryPointMeasurementResult:
        """Validate that the total raw score matches the sum of item raw scores."""
        expected_raw = sum(item.raw_score for item in self.items)
        if abs(self.total_raw_score - expected_raw) > 0.001:
            raise ValueError(
                f"total_raw_score ({self.total_raw_score}) must equal "
                f"sum of item raw scores ({expected_raw})"
            )
        return self

    @model_validator(mode="after")
    def validate_effort_totals(self: Self) -> StoryPointMeasurementResult:
        """Validate that effort totals sum to the total raw score."""
        if abs(
            self.specification_effort_total + self.implementation_effort_total
            - self.total_raw_score
        ) > 0.001:
            raise ValueError(
                f"specification_effort_total + implementation_effort_total "
                f"({self.specification_effort_total} + {self.implementation_effort_total}) "
                f"must equal total_raw_score ({self.total_raw_score})"
            )
        return self

    @model_validator(mode="after")
    def validate_run_id(self: Self) -> StoryPointMeasurementResult:
        """Validate that the run id is not empty."""
        if not self.run_id:
            raise ValueError("run_id must be non-empty")
        return self