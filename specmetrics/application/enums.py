from __future__ import annotations

import enum


class StageName(enum.Enum):
    DISCOVER = "discover"
    EXTRACT = "extract"
    GRAPH = "graph"
    CSM = "csm"
    CFM = "cfm"
    RULE = "rule"
    MEASURE = "measure"
    EXPORT = "export"


class OutputFormat(enum.Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml"
    TEXT = "text"
    NONE = "none"


class PipelineStatus(enum.Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class StageExecutionStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
