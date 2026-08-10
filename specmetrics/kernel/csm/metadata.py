"""Metadata models for the canonical specification model build."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ClassificationConflict(BaseModel):
    """Records a node whose category could not be resolved unambiguously."""

    node_id: str
    competing_categories: list[str]
    resolved_category: str
    reason: str = ""


class BuildMetadata(BaseModel):
    """Metadata describing a canonical specification model build."""

    run_id: str
    build_duration_ms: int = 0
    element_counts: dict[str, int] = {}
    total_input_nodes: int = 0
    unclassified_count: int = 0
    classification_conflicts: list[ClassificationConflict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
