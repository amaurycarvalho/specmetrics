"""Diagnostics models for tracking pipeline stage timings and errors."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime


class StageStatus(enum.Enum):
    """Lifecycle status of a single pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageTiming:
    """Timing and status of a single pipeline stage."""

    stage_name: str
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None


@dataclass
class StageError:
    """Error record for a failed pipeline stage."""

    stage_name: str
    message: str
    exception_type: str
    timestamp: datetime


@dataclass
class Diagnostics:
    """Collects timing and error diagnostics for a pipeline run."""

    started_at: datetime | None = None
    completed_at: datetime | None = None
    stage_timings: dict[str, StageTiming] = field(default_factory=dict)
    errors: list[StageError] = field(default_factory=list)
    total_duration_ms: int | None = None
