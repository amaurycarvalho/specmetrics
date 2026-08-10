"""Immutable context object passed through pipeline stages."""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Self
from uuid import UUID, uuid4

from .diagnostics import Diagnostics


@dataclass(frozen=True)
class PipelineContext:
    """Immutable snapshot of state shared across pipeline stages."""

    execution_id: UUID = field(default_factory=uuid4)
    repository: Any | None = None
    adapter_result: Any | None = None
    extraction_result: Any | None = None
    evidence_graph: Any | None = None
    canonical_spec_model: Any | None = None
    canonical_model: Any | None = None
    measurement_result: Any | None = None
    exported_files: list[str] | None = None
    published_events: tuple = ()
    diagnostics: Diagnostics | None = None
    metadata: Any | None = None

    def with_stage_output(
        self: Self, field_name: str, value: object, event: object = None
    ) -> PipelineContext:
        """Return a copy of this context with the given stage output set."""
        kwargs: dict[str, Any] = {field_name: value}
        if event is not None:
            kwargs["published_events"] = self.published_events + (event,)
        return dataclasses.replace(self, **kwargs)

    def merge_stage_output(
        self: Self, field_name: str, value: dict, event: object = None
    ) -> PipelineContext:
        """Return a copy of this context with the given mapping merged into a stage output."""
        current = getattr(self, field_name, None) or {}
        if not isinstance(current, dict):
            current = {}
        merged = {**current, **value}
        return self.with_stage_output(field_name, merged, event=event)
