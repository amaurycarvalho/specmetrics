from __future__ import annotations

from specmetrics.application.enums import StageName
from specmetrics.application.stage_mapping import (
    _resolve_event_order,
    _stage_name_from_event,
)
from specmetrics.kernel.events import EventType
from specmetrics.kernel.pipeline_engine import CANONICAL_EVENT_ORDER


class TestStageNameFromEvent:
    def test_known_event_maps_to_stage(self) -> None:
        assert _stage_name_from_event(EventType.REPOSITORY_LOADED) == "discover"
        assert _stage_name_from_event(EventType.SEMANTIC_EXTRACTION_COMPLETED) == "extract"
        assert _stage_name_from_event(EventType.MEASUREMENT_COMPLETED) == "measure"

    def test_unknown_event_uses_event_value(self) -> None:
        assert _stage_name_from_event(EventType.TELEMETRY_PUBLISHED) == "telemetry_published"


class TestResolveEventOrder:
    def test_explicit_stages_map_to_events(self) -> None:
        order = _resolve_event_order([StageName.DISCOVER, StageName.CSM], None)
        assert order == [
            EventType.REPOSITORY_LOADED,
            EventType.CANONICAL_SPECIFICATION_MODEL_BUILT,
        ]

    def test_no_stages_returns_full_canonical_order(self) -> None:
        assert _resolve_event_order(None, None) == list(CANONICAL_EVENT_ORDER)

    def test_from_stage_includes_start_and_later(self) -> None:
        order = _resolve_event_order(None, StageName.CSM)
        assert order[0] == EventType.CANONICAL_SPECIFICATION_MODEL_BUILT
        assert EventType.CANONICAL_MODEL_BUILT in order
        assert EventType.MEASUREMENT_COMPLETED in order
        assert EventType.REPOSITORY_LOADED not in order

    def test_from_stage_results_are_all_events(self) -> None:
        order = _resolve_event_order(None, StageName.EXTRACT)
        assert all(isinstance(et, EventType) for et in order)

    def test_from_stage_full_order_when_first(self) -> None:
        order = _resolve_event_order(None, StageName.DISCOVER)
        assert order == list(CANONICAL_EVENT_ORDER)
