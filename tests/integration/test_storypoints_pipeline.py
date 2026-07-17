from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    EvidenceRef,
    FunctionalProcess,
    BuildMetadata,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.storypoints.plugin import (
    StoryPointsHandler,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(
        graph_node_id="gn-001", document_id="doc-001", text="ev"
    )
    fp_id = _uid()
    return CanonicalFunctionalModel(
        run_id="pipeline-test-cfm",
        functional_processes={
            fp_id: FunctionalProcess(
                id=fp_id, name="Login", actor_ids=[], evidence=ev
            ),
            _uid(): FunctionalProcess(
                id=_uid(), name="Process Order", actor_ids=[], evidence=ev
            ),
        },
        metadata=BuildMetadata(
            run_id="pipeline-test-cfm", version="1.0", source="test"
        ),
    )


class TestStoryPointsPipeline:
    def test_pipeline_integration(self):
        cfm = _make_cfm()
        ctx = PipelineContext(canonical_model=cfm)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = StoryPointsHandler()
        result_ctx = handler.handle(event)

        assert result_ctx is not None
        assert result_ctx.measurement_result is not None
        payload = result_ctx.measurement_result
        assert "total_story_points" in payload
        assert "method" in payload
        assert payload["method"] == "StoryPoints"
        assert "estimated_items" in payload
        assert "duration_ms" in payload
        assert payload["total_story_points"] > 0

    def test_pipeline_missing_cfm(self):
        ctx = PipelineContext(canonical_model=None)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = StoryPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["total_story_points"] == 0
        assert len(payload["warnings"]) > 0

    def test_pipeline_empty_cfm(self):
        cfm = CanonicalFunctionalModel(
            run_id="empty",
            metadata=BuildMetadata(
                run_id="empty", version="1.0", source="test"
            ),
        )
        ctx = PipelineContext(canonical_model=cfm)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = StoryPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["total_story_points"] == 0
        assert payload["estimated_items"] == 0
