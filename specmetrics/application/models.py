from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .enums import (
    OutputFormat,
    PipelineStatus,
    StageExecutionStatus,
    StageName,
)


@dataclass
class PipelineRequest:
    project_path: Path
    stages: list[StageName] | None = None
    from_stage: StageName | None = None
    output_format: OutputFormat = OutputFormat.NONE
    output_path: Path | None = None
    verbose: bool = False
    quiet: bool = False


@dataclass
class StageResult:
    stage: StageName
    status: StageExecutionStatus
    duration_seconds: float = 0.0
    entities_found: int = 0


@dataclass
class MeasurementResult:
    total_function_points: int = 0
    breakdown: dict[str, int] = field(default_factory=dict)
    complexity_distribution: dict[str, dict[str, int]] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    applied_rule_pack: str = ""


@dataclass
class PipelineResult:
    status: PipelineStatus
    project_path: Path | None = None
    stages_executed: list[StageResult] = field(default_factory=list)
    measurement: MeasurementResult | None = None
    duration_seconds: float = 0.0
    error: str = ""
    export_path: Path | None = None


@dataclass
class PluginInfo:
    name: str
    version: str
    type: str
    enabled: bool = True
    compatible: bool = True


@dataclass
class VersionInfo:
    platform_version: str
    python_version: str
    plugins: list[PluginInfo] = field(default_factory=list)
