from __future__ import annotations

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.tshirt.plugin import (
    TShirtHandler,
    TShirtPlugin,
    create_tshirt_measurement_metadata,
)


def _event(measurement_result, metadata=None) -> PipelineEvent:
    ctx = PipelineContext(measurement_result=measurement_result, metadata=metadata)
    return PipelineEvent(
        event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
        publisher="tshirt",
        payload={},
        context=ctx,
    )


def _storypoints_payload(items=None) -> dict:
    return {
        "run_id": "sp-run-1",
        "items": items
        if items is not None
        else [
            {"element_id": "fp-1", "element_name": "Process 1", "story_point_value": 2},
            {"element_id": "fp-2", "element_name": "Process 2", "story_point_value": 13},
        ],
    }


class TestHandlerIdentity:
    def test_handler_id(self):
        assert TShirtHandler().handler_id == "tshirt_measurement"

    def test_handled_event_type(self):
        assert (
            TShirtHandler().handled_event_type
            == EventType.TSHIRT_CLASSIFICATION_COMPLETED
        )

    def test_stage_name(self):
        assert TShirtHandler().stage_name == "T-Shirt Sizing"


class TestHandleNoStoryPoints:
    def test_no_story_points_returns_empty_result(self):
        ctx = TShirtHandler().handle(_event(None))
        payload = ctx.measurement_result
        assert payload["total_items"] == 0
        assert payload["tshirt"] == 0
        codes = {w["code"] for w in payload["warnings"]}
        assert "NO_STORY_POINTS" in codes
        assert payload["distribution"] == {}

    def test_source_run_id_captured_even_without_items(self):
        ctx = TShirtHandler().handle(
            _event({"run_id": "sp-run-9", "items": None})
        )
        payload = ctx.measurement_result
        assert payload["source_measurement_run_id"] == "sp-run-9"


class TestHandleWithItems:
    def test_classifies_items_and_builds_distribution(self):
        handler = TShirtHandler()
        ctx = handler.handle(_event(_storypoints_payload()))
        payload = ctx.measurement_result
        assert payload["total_items"] == 2
        assert payload["distribution"] == {"S": 1, "L": 1}
        assert len(payload["tshirt_entities"]) == 2
        assert payload["method"] == "TShirtSizing"

    def test_payload_contains_required_keys(self):
        ctx = TShirtHandler().handle(_event(_storypoints_payload()))
        payload = ctx.measurement_result
        for key in [
            "method",
            "scale",
            "tshirt",
            "tshirt_breakdown",
            "total_items",
            "distribution",
            "applied_rule_pack",
            "source_measurement_run_id",
            "duration_ms",
            "warnings",
            "tshirt_entities",
        ]:
            assert key in payload

    def test_item_without_sp_value_skipped(self):
        payload = _storypoints_payload(
            items=[
                {"element_id": "fp-1", "element_name": "A", "story_point_value": 2},
                {"element_id": "fp-2", "element_name": "B"},
            ]
        )
        ctx = TShirtHandler().handle(_event(payload))
        out = ctx.measurement_result
        assert out["total_items"] == 1
        assert out["distribution"] == {"S": 1}

    def test_custom_mapping_override_applied(self):
        ctx = TShirtHandler().handle(
            _event(
                _storypoints_payload(),
                metadata={
                    "tshirt_mapping": [
                        {
                            "label": "TINY",
                            "story_point_range": [1, 100],
                            "ordinal": 1,
                        }
                    ]
                },
            )
        )
        out = ctx.measurement_result
        assert out["distribution"] == {"TINY": 2}


class TestPluginFacade:
    def test_plugin_id(self):
        assert TShirtPlugin().plugin_id() == "tshirt"

    def test_supported_methodology(self):
        assert TShirtPlugin().supported_methodology() == "T-Shirt Sizing"

    def test_supported_component_types(self):
        assert "functional_process" in TShirtPlugin().supported_component_types()


class TestMetadataFactory:
    def test_create_metadata(self):
        metadata = create_tshirt_measurement_metadata()
        assert metadata.id == "tshirt"
        assert metadata.plugin_type.value == "measurement"
        handler = metadata.handler_factory()
        assert handler.handler_id == "tshirt_measurement"

import structlog

from specmetrics.plugins.measurement.tshirt import plugin as tshirt_plugin
from specmetrics.plugins.measurement.tshirt.models import (
    ExecutionMetadata,
    FunctionalWorkItem,
    TShirtMeasurementResult,
)


class _HistRecorder:
    def __init__(self):
        self.records = []

    def record(self, value, labels=None):
        self.records.append((value, labels))


class _GaugeRecorder:
    def __init__(self):
        self.values = []

    def set(self, value):
        self.values.append(value)


def _tshirt_result() -> TShirtMeasurementResult:
    items = [
        FunctionalWorkItem(
            element_id="fp-1",
            element_name="A",
            story_point_value=2,
            tshirt_size="S",
        ),
        FunctionalWorkItem(
            element_id="fp-2",
            element_name="B",
            story_point_value=13,
            tshirt_size="L",
        ),
    ]
    return TShirtMeasurementResult(
        run_id="r1",
        total_items=2,
        items=items,
        distribution={"S": 1, "L": 1},
        execution_metadata=ExecutionMetadata(duration_ms=10.0, total_fps_processed=2),
    )


def _finalize(handler, ctx, result, start):
    return handler._finalize(ctx, result, start)


class TestFinalizeDuration:
    def test_duration_recorded_in_milliseconds(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_1/2/3/4/5/6 (duration computation)."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)
        monkeypatch.setattr(tshirt_plugin.time, "monotonic", lambda: 1002.5)

        ctx = PipelineContext()
        handler = TShirtHandler()
        _finalize(handler, ctx, _tshirt_result(), 1000.0)
        assert hist.records == [(2500.0, None)]


class TestFinalizeItemGauge:
    def test_item_gauge_set_to_total_items(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_7/8 (gauge guard + set(None))."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)

        ctx = PipelineContext()
        handler = TShirtHandler()
        _finalize(handler, ctx, _tshirt_result(), 1000.0)
        assert gauge.values == [2]


class TestFinalizeDistribution:
    def test_distribution_histogram_records_counts_and_labels(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_9/10/11/12/13/14/15 (histogram recording)."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)

        ctx = PipelineContext()
        handler = TShirtHandler()
        _finalize(handler, ctx, _tshirt_result(), 1000.0)
        assert dist.records == [
            (1, {"tshirt_size": "S"}),
            (1, {"tshirt_size": "L"}),
        ]


class TestFinalizeEntities:
    def test_entities_dumped_as_json(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_19/20/21 (model_dump mode)."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)

        ctx = PipelineContext()
        handler = TShirtHandler()
        out = _finalize(handler, ctx, _tshirt_result(), 1000.0)
        entities = out.measurement_result["tshirt_entities"]
        assert isinstance(entities, list)
        assert len(entities) == 2
        assert all(isinstance(e, dict) for e in entities)
        assert entities[0]["tshirt_size"] == "S"
        assert entities[1]["element_id"] == "fp-2"


class TestFinalizeEvent:
    def test_publishes_tshirt_event_with_payload(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_47/48/49/50/51/56/57/68/71 (event emission)."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)

        ctx = PipelineContext()
        handler = TShirtHandler()
        out = _finalize(handler, ctx, _tshirt_result(), 1000.0)
        assert len(out.published_events) == 1
        event = out.published_events[0]
        assert event.event_type == EventType.TSHIRT_CLASSIFICATION_COMPLETED
        assert event.publisher == "tshirt"
        assert event.context is ctx
        assert event.payload["total_items"] == 2
        assert event.payload["method"] == "TShirtSizing"


class TestFinalizeLogging:
    def test_logs_total_items_and_duration(self, monkeypatch):
        """Kills TShirtHandler::_finalize__mutmut_59/60/62/63 (log field values)."""
        hist = _HistRecorder()
        gauge = _GaugeRecorder()
        dist = _HistRecorder()
        monkeypatch.setattr(tshirt_plugin, "_classify_duration", hist)
        monkeypatch.setattr(tshirt_plugin, "_item_gauge", gauge)
        monkeypatch.setattr(tshirt_plugin, "_distribution_histogram", dist)

        ctx = PipelineContext()
        handler = TShirtHandler()
        with structlog.testing.capture_logs() as cap:
            _finalize(handler, ctx, _tshirt_result(), 1000.0)
        events = {e["event"]: e for e in cap}
        completed = events["tshirt_classification_completed"]
        assert completed["total_items"] == 2
        assert completed["duration_ms"] == 10.0
