from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ClassificationConflict(BaseModel):
    node_id: str
    competing_categories: list[str]
    resolved_category: str
    reason: str = ""


class BuildMetadata(BaseModel):
    run_id: str
    build_duration_ms: int = 0
    element_counts: dict[str, int] = {}
    total_input_nodes: int = 0
    unclassified_count: int = 0
    conflicts: list[ClassificationConflict] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
