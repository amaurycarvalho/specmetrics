from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class StageStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageTiming:
    stage_name: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


@dataclass
class StageError:
    stage_name: str
    message: str
    exception_type: str
    timestamp: datetime


@dataclass
class Diagnostics:
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    stage_timings: dict[str, StageTiming] = field(default_factory=dict)
    errors: list[StageError] = field(default_factory=list)
    total_duration_ms: Optional[int] = None
