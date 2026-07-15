from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PublisherTarget(BaseModel):
    id: str
    name: str = ""
    endpoint_url: str = ""
    enabled: bool = True
    publishing_interval: int = 30


class EvidenceRef(BaseModel):
    spec_document: str = ""
    spec_section: str = ""
    spec_element_id: str | None = None
    extracted_text: str | None = None


class ResourceAttributes(BaseModel):
    project_name: str
    run_id: str
    specification_version: str = ""
    tool_version: str = ""
    pipeline_execution_timestamp: datetime | None = None


class TelemetryMetric(BaseModel):
    name: str
    value: float
    unit: str = "1"
    description: str = ""
    timestamp: datetime | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
