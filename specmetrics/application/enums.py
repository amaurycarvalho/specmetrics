"""Enumerations used across the application layer."""

from __future__ import annotations

import enum


class StageName(enum.Enum):
    """Names of the pipeline stages executed by the engine."""

    DISCOVER = "discover"
    EXTRACT = "extract"
    GRAPH = "graph"
    CSM = "csm"
    CFM = "cfm"
    RULE = "rule"
    MEASURE = "measure"
    EXPORT = "export"


class OutputFormat(enum.Enum):
    """Supported pipeline output formats."""

    JSON = "json"
    CSV = "csv"
    XML = "xml"
    TEXT = "text"
    NONE = "none"


class PipelineStatus(enum.Enum):
    """Overall status of a pipeline run."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class StageExecutionStatus(enum.Enum):
    """Execution status of an individual pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
