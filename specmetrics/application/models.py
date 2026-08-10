"""Canonical data models for the measurement pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from .enums import (
    OutputFormat,
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)

CanonicalEntityType = Literal[
    "data_group",
    "operation",
    "functional_process",
    "specification_activity",
    "business_rule",
    "actor",
    "relationship",
    "decision",
    "assumption",
    "constraint",
    "risk",
    "open_question",
    "acceptance_criteria",
    "glossary_term",
]

CANONICAL_ENTITY_TYPES: frozenset[str] = frozenset(CanonicalEntityType.__args__)


_ENTITY_ID_PATTERN = re.compile(r"^(cfm|csm):[a-z_]+:.+$")


def is_valid_entity_id(id_str: str) -> bool:
    """Return whether the given string is a valid canonical entity identifier."""
    return bool(_ENTITY_ID_PATTERN.match(id_str))


def make_entity_id(category: str, name: str, model_source: str = "cfm") -> str:
    """Build a canonical entity identifier from category, name, and model source."""
    if model_source not in ("cfm", "csm"):
        model_source = "cfm"
    safe_name = name.lower()
    safe_name = re.sub(r'[^\w/-]', '-', safe_name)
    safe_name = re.sub(r'[-]+', '-', safe_name)
    safe_name = safe_name.strip("-")
    safe_name = safe_name[:100]
    return f"{model_source}:{category}:{safe_name}"


def resolve_entity_id(raw_id: str, category: str, name: str, model_source: str = "cfm") -> str:
    """Return ``raw_id`` when valid, otherwise build one from category and name."""
    if raw_id and is_valid_entity_id(raw_id):
        return raw_id
    return make_entity_id(category, name, model_source)


class EntityScore(BaseModel):
    """Canonical score for a single measured entity."""

    id: str
    name: str
    type: str
    score: float
    metadata: dict[str, Any] | None = None

    @field_validator("id")
    @classmethod
    def validate_id_format(cls: type[EntityScore], v: str) -> str:
        """Validate that the entity id matches the compound URI pattern."""
        if not _ENTITY_ID_PATTERN.match(v):
            raise ValueError(
                f"Entity id '{v}' must match compound URI pattern "
                f"<source_model>:<category>:<name> where source_model is cfm or csm"
            )
        return v


class MetricBreakdownEntry(BaseModel):
    """Breakdown of entities and totals for a single metric."""

    name: str
    metric: str
    total: float
    unit: str
    entity_count: int
    entities: list[EntityScore] = Field(default_factory=list)
    status: str = "success"
    errors: list[str] | None = None
    warnings: list[str] | None = None
    metadata: dict[str, Any] | None = None


METRIC_NAME_MAP: dict[str, str] = {
    "bcp": "business_complexity_points",
    "fpa": "function_points",
    "sfp": "simplified_function_points",
    "snap": "snap",
    "sp": "story_points",
    "tshirt": "tshirt",
    "tp": "token_points",
    "cp": "cognitive_points",
}

CLI_ID_TO_PLUGIN_ID: dict[str, str] = {
    "sp": "storypoints",
    "tp": "token_points",
    "cp": "cognitive_points",
}

METRIC_DISPLAY_MAP: dict[str, str] = {
    "bcp": "Business Complexity Points",
    "fpa": "Function Points",
    "sfp": "Simplified Function Points",
    "snap": "SNAP",
    "sp": "Story Points",
    "tshirt": "TShirt",
    "tp": "Token Points",
    "cp": "Cognitive Points",
}

JSON_NAME_TO_DISPLAY_MAP: dict[str, str] = {
    METRIC_NAME_MAP[k]: v for k, v in METRIC_DISPLAY_MAP.items()
}


@dataclass
class PipelineRequest:
    """Parameters of a pipeline execution request."""

    project_path: Path
    stages: list[StageName] | None = None
    from_stage: StageName | None = None
    metrics_filter: list[str] | None = None
    output_format: OutputFormat = OutputFormat.NONE
    output_path: Path | None = None
    verbose: bool = False
    quiet: bool = False
    measure_id: str = ""
    llm_rpm_limit: int = 15


@dataclass
class StageResult:
    """Outcome of a single executed pipeline stage."""

    stage: StageName
    status: StageExecutionStatus
    duration_seconds: float = 0.0
    entities_found: int = 0


@dataclass
class MeasurementResult:
    """Aggregated measurement outcome of a pipeline run."""

    total_function_points: int = 0
    breakdown: dict[str, int] = field(default_factory=dict)
    complexity_distribution: dict[str, dict[str, int]] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    applied_rule_pack: str = ""


@dataclass
class MetricOutputItem:
    """Summary of a single metric produced by the pipeline."""

    name: str
    total: float = 0
    status: str = "completed"
    duration_ms: int = 0


@dataclass
class StageOutputItem:
    """Summary of entities produced by a single pipeline stage."""

    name: str
    count: int = 0
    count_type: str = "items"
    duration_ms: int = 0


@dataclass
class ErrorOutputItem:
    """An error raised during pipeline execution."""

    stage: str = ""
    message: str = ""
    details: dict[str, Any] | None = None


@dataclass
class PipelineResult:
    """Full result of a pipeline execution."""

    status: PipelineStatus
    project_path: Path | None = None
    run_id: str = ""
    stages_executed: list[StageResult] = field(default_factory=list)
    measurement: MeasurementResult | None = None
    duration_seconds: float = 0.0
    error: str = ""
    export_path: Path | None = None
    canonical_model: Any | None = None
    _framework_detected: str = ""
    _max_entities_per_stage: int = 5000
    metric_results: list[MetricOutputItem] = field(default_factory=list)
    stage_entities: dict[str, list[dict]] = field(default_factory=dict)
    stage_details: list[StageOutputItem] = field(default_factory=list)
    output_errors: list[ErrorOutputItem] = field(default_factory=list)
    llm_provider: str = ""
    llm_model: str = ""
    measurement_result_raw: dict[str, Any] = field(default_factory=dict)
    llm_call_stats: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginInfo:
    """Metadata about a discovered plugin."""

    name: str
    version: str
    type: str
    enabled: bool = True
    compatible: bool = True


@dataclass
class VersionInfo:
    """Version information for the platform and its plugins."""

    platform_version: str
    python_version: str
    plugins: list[PluginInfo] = field(default_factory=list)
