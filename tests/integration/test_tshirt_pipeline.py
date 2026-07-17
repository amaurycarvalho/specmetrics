from __future__ import annotations

from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.tshirt.plugin import TShirtHandler


class TestTShirtPipeline:
    def test_pipeline_integration(self):
        sp_items = [
            {
                "element_id": "fp-001",
                "element_name": "Login",
                "normalized_value": 3,
            },
            {
                "element_id": "fp-002",
                "element_name": "Process Order",
                "normalized_value": 8,
            },
            {
                "element_id": "fp-003",
                "element_name": "Validate",
                "normalized_value": 20,
            },
        ]
        sp_payload = {
            "method": "StoryPoints",
            "items": sp_items,
            "total_story_points": 31,
            "run_id": "sp-run-001",
        }
        ctx = PipelineContext(measurement_result=sp_payload)
        event = PipelineEvent(
            event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TShirtHandler()
        result_ctx = handler.handle(event)

        assert result_ctx is not None
        assert result_ctx.measurement_result is not None
        payload = result_ctx.measurement_result
        assert "method" in payload
        assert payload["method"] == "TShirtSizing"
        assert "total_items" in payload
        assert payload["total_items"] == 3
        assert "distribution" in payload
        assert "duration_ms" in payload

    def test_pipeline_no_sp_result(self):
        ctx = PipelineContext(measurement_result=None)
        event = PipelineEvent(
            event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TShirtHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["total_items"] == 0
        assert len(payload["warnings"]) > 0

    def test_pipeline_empty_sp_result(self):
        ctx = PipelineContext(measurement_result={"items": [], "run_id": "sp-run"})
        event = PipelineEvent(
            event_type=EventType.TSHIRT_CLASSIFICATION_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = TShirtHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["total_items"] == 0
