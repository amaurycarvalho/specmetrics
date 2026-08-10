"""Simple data models for Story Points measurement."""
from __future__ import annotations

from pydantic import BaseModel


class EvidenceRef(BaseModel):
    """Reference to an evidence source for a Story Points item."""

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class MeasurementWarning(BaseModel):
    """Warning raised during Story Points estimation."""

    code: str
    message: str
    element_id: str | None = None


class MeasurementEvidence(BaseModel):
    """Evidence captured for a single Story Points measurement element."""

    element_id: str
    document_id: str
    section_id: str | None = None
    applied_rule: str = ""
    text: str = ""


class RawEffortScore(BaseModel):
    """Raw effort score with factor breakdown and applied coefficients."""

    value: float
    factor_breakdown: dict[str, float]
    factor_coefficients: dict[str, float]


class StoryPointEstimate(BaseModel):
    """A single normalized Story Point estimate."""

    value: int
    raw_score: float
    normalization_rule: str = "default_threshold_v1"