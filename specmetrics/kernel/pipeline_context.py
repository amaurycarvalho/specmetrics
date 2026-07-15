from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID, uuid4

from .diagnostics import Diagnostics


@dataclass(frozen=True)
class PipelineContext:
    execution_id: UUID = field(default_factory=uuid4)
    repository: Optional[Any] = None
    adapter_result: Optional[Any] = None
    extraction_result: Optional[Any] = None
    evidence_graph: Optional[Any] = None
    canonical_model: Optional[Any] = None
    measurement_result: Optional[Any] = None
    exported_files: Optional[list[str]] = None
    published_events: tuple = ()
    diagnostics: Optional[Diagnostics] = None
    metadata: Optional[Any] = None

    def with_stage_output(
        self, field_name: str, value: Any, event: Any = None
    ) -> PipelineContext:
        kwargs: dict[str, Any] = {field_name: value}
        if event is not None:
            kwargs["published_events"] = self.published_events + (event,)
        return dataclasses.replace(self, **kwargs)
