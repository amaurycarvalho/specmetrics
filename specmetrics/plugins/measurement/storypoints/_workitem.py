"""WorkItem model for Story Points measurement."""
from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from ._evidence import EvidenceRef


class WorkItem(BaseModel):
    """A single work item contributing to the Story Points total."""

    element_id: str
    element_name: str
    element_type: str = "functional_process"
    source_model: str = "CFM"
    raw_score: float
    normalized_value: int
    rank_position: int = 0
    structural_score: float = 0.0
    content_tokens: int = 0
    content_score: float = 0.0
    factor_breakdown: dict[str, float] = Field(default_factory=dict)
    base_weight: float | None = None
    applied_rules: list[str] = Field(default_factory=list)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_raw_score(self: Self) -> WorkItem:
        """Validate that raw score equals structural plus content score."""
        expected = self.structural_score + self.content_score
        if abs(self.raw_score - expected) > 0.001:
            raise ValueError(
                f"raw_score ({self.raw_score}) must equal structural_score "
                f"({self.structural_score}) + content_score ({self.content_score}) "
                f"= {expected}"
            )
        return self

    @model_validator(mode="after")
    def validate_factor_or_base_weight(self: Self) -> WorkItem:
        """Validate that factor breakdown and base weight are not combined."""
        is_fp = self.element_type == "functional_process"
        if is_fp and self.factor_breakdown and self.base_weight is not None:
            raise ValueError(
                "functional_process items must not have base_weight"
            )
        if is_fp and self.factor_breakdown:
            fb_sum = sum(self.factor_breakdown.values())
            if abs(fb_sum - self.structural_score) > 0.001:
                raise ValueError(
                    f"sum of factor_breakdown ({fb_sum}) must equal "
                    f"structural_score ({self.structural_score})"
                )
        if not is_fp and self.base_weight is not None and self.factor_breakdown:
            raise ValueError(
                "non-FP items must not have factor_breakdown"
            )
        return self


FunctionalWorkItem = WorkItem