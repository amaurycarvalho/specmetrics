from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.kernel.events import PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.tshirt.models import (
    ExecutionMetadata,
    FunctionalWorkItem,
    TShirtMeasurementResult,
)
from specmetrics.plugins.measurement.tshirt.plugin import (
    TShirtHandler,
    create_tshirt_measurement_metadata,
)


class TestMeasurementAPIContract:
    def test_plugin_metadata_type(self):
        metadata = create_tshirt_measurement_metadata()
        assert metadata.plugin_type == PluginType.MEASUREMENT

    def test_plugin_metadata_id(self):
        metadata = create_tshirt_measurement_metadata()
        assert metadata.id == "tshirt"

    def test_handler_event_type(self):
        handler = TShirtHandler()
        assert handler.handled_event_type == EventType.TSHIRT_CLASSIFICATION_COMPLETED

    def test_handler_id(self):
        handler = TShirtHandler()
        assert handler.handler_id == "tshirt_measurement"

    def test_handler_stage_name(self):
        handler = TShirtHandler()
        assert handler.stage_name == "T-Shirt Sizing"

    def test_result_model_required_fields(self):
        r = TShirtMeasurementResult(
            run_id="contract-test",
            total_items=3,
            items=[
                FunctionalWorkItem(
                    element_id="fp-001",
                    element_name="A",
                    story_point_value=3,
                    tshirt_size="S",
                ),
                FunctionalWorkItem(
                    element_id="fp-002",
                    element_name="B",
                    story_point_value=8,
                    tshirt_size="L",
                ),
                FunctionalWorkItem(
                    element_id="fp-003",
                    element_name="C",
                    story_point_value=20,
                    tshirt_size="XL",
                ),
            ],
            distribution={"S": 1, "L": 1, "XL": 1},
            execution_metadata=ExecutionMetadata(
                duration_ms=1.0, total_fps_processed=3
            ),
        )
        assert r.run_id == "contract-test"
        assert r.total_items == 3
        assert r.method == "TShirtSizing"
        assert r.distribution == {"S": 1, "L": 1, "XL": 1}

    def test_payload_has_tshirt_keys(self):
        sp_items = [
            {"element_id": "fp-001", "element_name": "A", "normalized_value": 3},
            {"element_id": "fp-002", "element_name": "B", "normalized_value": 8},
            {"element_id": "fp-003", "element_name": "C", "normalized_value": 20},
        ]
        sp_payload = {"method": "StoryPoints", "items": sp_items}
        ctx = PipelineContext(measurement_result=sp_payload)
        event = PipelineEvent(
            event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TShirtHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert "tshirt" in payload
        assert payload["tshirt"] == 3
        assert "tshirt_breakdown" in payload
        assert "S" in payload["tshirt_breakdown"]
        assert "L" in payload["tshirt_breakdown"]
        assert "XL" in payload["tshirt_breakdown"]

    def test_metadata_mapping_matches_default(self):
        from specmetrics.application.metrics_json import _build_metric_metadata
        from specmetrics.plugins.measurement.tshirt.classifier import DEFAULT_MAPPING
        metadata = _build_metric_metadata("tshirt", {"scale": "XS-S-M-L-XL-XXL"})
        assert metadata is not None
        assert "scale" in metadata
        assert "mapping" in metadata
        mapping = metadata["mapping"]
        for size in DEFAULT_MAPPING:
            label = size.label
            expected = size.story_point_range[1]
            assert label in mapping, f"Missing size {label} in metadata mapping"
            assert mapping[label] == expected, (
                f"Size {label}: expected highest value {expected}, got {mapping[label]}"
            )
