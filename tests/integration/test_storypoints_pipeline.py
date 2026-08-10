from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    BuildMetadata as CfmBuildMeta,
)
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    FunctionalProcess,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef as CfmEvidenceRef,
)
from specmetrics.kernel.csm.model import (
    BuildMetadata as CsmBuildMeta,
)
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    Decision,
)
from specmetrics.kernel.csm.model import (
    EvidenceRef as CsmEvidenceRef,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.storypoints.plugin import (
    StoryPointsHandler,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_cfm() -> CanonicalFunctionalModel:
    ev = CfmEvidenceRef(graph_node_id="gn-001", document_id="doc-001", text="ev")
    fp_id = _uid()
    return CanonicalFunctionalModel(
        run_id="pipeline-test-cfm",
        functional_processes={
            fp_id: FunctionalProcess(id=fp_id, name="Login", actor_ids=[], evidence=ev),
            _uid(): FunctionalProcess(
                id=_uid(), name="Process Order", actor_ids=[], evidence=ev
            ),
        },
        metadata=CfmBuildMeta(
            run_id="pipeline-test-cfm", version="1.0", source="test"
        ),
    )


def _make_csm() -> CanonicalSpecificationModel:
    ev = CsmEvidenceRef(graph_node_id="gn-csm", document_id="doc-csm", text="csm ev")
    dec_id = _uid()
    return CanonicalSpecificationModel(
        run_id="pipeline-test-csm",
        decisions={
            dec_id: Decision(
                id=dec_id,
                description="Use OAuth2 for authentication",
                evidence_references=[ev],
            ),
        },
        metadata=CsmBuildMeta(
            run_id="pipeline-test-csm", version="1.0", source="test"
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
        assert "storypoints_total_story_points" in payload
        assert "storypoints_method" in payload
        assert payload["storypoints_method"] == "StoryPoints"
        assert "storypoints_estimated_items" in payload
        assert "storypoints_duration_ms" in payload
        assert payload["storypoints_total_story_points"] > 0

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
        assert payload["storypoints_total_story_points"] == 0
        assert len(payload["storypoints_warnings"]) > 0

    def test_pipeline_empty_cfm(self):
        cfm = CanonicalFunctionalModel(
            run_id="empty",
            metadata=CfmBuildMeta(run_id="empty", version="1.0", source="test"),
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
        assert payload["storypoints_total_story_points"] == 0
        assert payload["storypoints_estimated_items"] == 0

    def test_pipeline_with_csm_and_cfm(self):
        cfm = _make_cfm()
        csm = _make_csm()
        ctx = PipelineContext(canonical_model=cfm, canonical_spec_model=csm)
        event = PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )
        handler = StoryPointsHandler()
        result_ctx = handler.handle(event)
        payload = result_ctx.measurement_result
        assert payload["storypoints_total_story_points"] > 0
        assert payload["storypoints_total_raw_score"] > 0
        assert payload["storypoints_specification_effort_total"] > 0
        assert payload["storypoints_implementation_effort_total"] > 0
        assert payload["storypoints_content_multiplier"] == 0.1
        assert "storypoints_calibration_version" in payload
