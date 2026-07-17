from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .pipeline_context import PipelineContext


class EventType(enum.Enum):
    REPOSITORY_LOADED = "repository_loaded"
    DOCUMENTS_DISCOVERED = "documents_discovered"
    DOCUMENTS_VALIDATED = "documents_validated"
    SEMANTIC_EXTRACTION_COMPLETED = "semantic_extraction_completed"
    EVIDENCE_GRAPH_BUILT = "evidence_graph_built"
    CANONICAL_SPECIFICATION_MODEL_BUILT = "canonical_specification_model_built"
    CANONICAL_MODEL_BUILT = "canonical_model_built"
    RULE_PACK_APPLIED = "rule_pack_applied"
    MEASUREMENT_COMPLETED = "measurement_completed"
    TOKEN_POINTS_MEASURED = "token_points_measured"
    COGNITIVE_POINTS_MEASURED = "cognitive_points_measured"
    EXPORT_COMPLETED = "export_completed"
    TELEMETRY_PUBLISHED = "telemetry_published"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"


@dataclass(frozen=True)
class PipelineEvent:
    event_type: EventType
    publisher: str
    payload: dict[str, Any]
    context: "PipelineContext"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
