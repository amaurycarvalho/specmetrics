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
        assert "tshirt" in payload
        assert payload["tshirt"] == 3
        assert "tshirt_breakdown" in payload
        assert isinstance(payload["tshirt_breakdown"], dict)
        total_breakdown = sum(
            v["count"] for v in payload["tshirt_breakdown"].values()
        )
        assert total_breakdown == 3

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

    def test_pipeline_with_storypoints_entities_key(self):
        sp_items = [
            {"element_id": "fp-001", "element_name": "A", "normalized_value": 3},
            {"element_id": "fp-002", "element_name": "B", "normalized_value": 8},
            {"element_id": "fp-003", "element_name": "C", "normalized_value": 20},
        ]
        sp_payload = {
            "method": "StoryPoints",
            "storypoints_entities": sp_items,
            "storypoints_total_story_points": 31,
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
        payload = result_ctx.measurement_result
        assert payload["tshirt"] == 3
        assert len(payload["tshirt_breakdown"]) == 3

    def test_tshirt_entities_have_required_fields(self):
        sp_items = [
            {"element_id": "fp-001", "element_name": "A", "normalized_value": 3},
            {"element_id": "fp-002", "element_name": "B", "normalized_value": 8},
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
        entities = payload.get("tshirt_entities", [])
        assert len(entities) == 2
        for entity in entities:
            assert "element_id" in entity
            assert "element_name" in entity
            assert "story_point_value" in entity
            assert "tshirt_size" in entity
            assert "mapping_rule" in entity

    def test_cross_spec_distribution_differs(self):
        sp_items_a = [
            {"element_id": f"fp-{i:03d}", "element_name": f"E{i}", "normalized_value": 3}
            for i in range(10)
        ]
        sp_items_b = [
            {"element_id": f"fp-{i:03d}", "element_name": f"E{i}", "normalized_value": 100}
            for i in range(10)
        ]
        from specmetrics.plugins.measurement.tshirt.classifier import classify_all
        items_a, _ = classify_all(sp_items_a)
        items_b, _ = classify_all(sp_items_b)
        dist_a: dict[str, int] = {}
        for i in items_a:
            dist_a[i.tshirt_size] = dist_a.get(i.tshirt_size, 0) + 1
        dist_b: dict[str, int] = {}
        for i in items_b:
            dist_b[i.tshirt_size] = dist_b.get(i.tshirt_size, 0) + 1
        l_xl_xxl_a = sum(dist_a.get(s, 0) for s in ("L", "XL", "XXL"))
        l_xl_xxl_b = sum(dist_b.get(s, 0) for s in ("L", "XL", "XXL"))
        assert l_xl_xxl_b > l_xl_xxl_a
