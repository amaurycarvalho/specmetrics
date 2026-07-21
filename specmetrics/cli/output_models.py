from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class MeasureMetadata(BaseModel):
    id: str = ""
    id_path: str = ""
    sdd_framework: str
    created: str
    llm: dict[str, str]
    project_path: str


class MetricResult(BaseModel):
    name: str
    total: float = 0
    status: str = "completed"
    duration_ms: int = 0


class StageInfo(BaseModel):
    name: str
    count: int = 0
    count_type: str = "items"
    duration_ms: int = 0


class ErrorRecord(BaseModel):
    stage: str = ""
    message: str = ""
    details: dict[str, Any] | None = None


class MeasureOutput(BaseModel):
    measure: MeasureMetadata
    results: list[MetricResult] = []
    stages: list[StageInfo] = []
    errors: list[ErrorRecord] = []
