from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from specmetrics.kernel.cfm.model import EvidenceRef


class Measurement(BaseModel):
    function_id: str
    function_name: str
    category: str = ""
    complexity: str = ""
    functional_size: float = 0.0
    evidence: list[EvidenceRef] = []
    attributes: dict[str, Any] = {}


class ExportMetadata(BaseModel):
    specmetrics_version: str = ""
    run_id: str = ""
    export_timestamp: datetime | None = None
    function_count: int = 0
    pipeline_duration_ms: int = 0


class ExportFormat(BaseModel):
    id: str
    name: str
    description: str = ""
    file_extension: str
    content_type: str = "application/octet-stream"
    serializer: object = None
