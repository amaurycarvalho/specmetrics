"""Pydantic output models for CLI result serialization."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MeasureMetadata(BaseModel):
    """Metadata describing a single measure run."""

    id: str = ""
    id_path: str = ""
    sdd_framework: str
    created: str
    llm: dict[str, str]
    project_path: str


class MetricResult(BaseModel):
    """Summary of a single metric in a measure run."""

    name: str
    total: float = 0
    status: str = "completed"
    duration_ms: int = 0


class StageInfo(BaseModel):
    """Summary of a single pipeline stage in a measure run."""

    name: str
    count: int = 0
    count_type: str = "items"
    duration_ms: int = 0


class ErrorRecord(BaseModel):
    """An error recorded during a measure run."""

    stage: str = ""
    message: str = ""
    details: dict[str, Any] | None = None


class MeasureOutput(BaseModel):
    """Full serializable output of a measure run."""

    measure: MeasureMetadata
    results: list[MetricResult] = []
    stages: list[StageInfo] = []
    errors: list[ErrorRecord] = []
