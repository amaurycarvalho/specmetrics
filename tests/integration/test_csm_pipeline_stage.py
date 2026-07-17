from __future__ import annotations

from specmetrics.kernel.csm.builder import CsmBuilderStage
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext


class TestCsmPipelineStage:
    def test_handler_construction(self):
        stage = CsmBuilderStage()
        assert stage.handled_event_type == EventType.EVIDENCE_GRAPH_BUILT
        assert stage.handler_id == "csm_builder_stage"
        assert stage.stage_name == "canonical_spec_model"

    def test_handle_without_evidence_graph(self):
        stage = CsmBuilderStage()
        context = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.EVIDENCE_GRAPH_BUILT,
            publisher="test",
            payload={},
            context=context,
        )
        result = stage.handle(event)
        assert result.canonical_spec_model is None

    def test_handle_with_evidence_graph_no_graph_store(self):
        stage = CsmBuilderStage()
        context = PipelineContext(
            evidence_graph={"run_id": "nonexistent-run"},
        )
        event = PipelineEvent(
            event_type=EventType.EVIDENCE_GRAPH_BUILT,
            publisher="test",
            payload={},
            context=context,
        )
        result = stage.handle(event)
        assert result.canonical_spec_model is None

    def test_emits_correct_event_type(self):
        stage = CsmBuilderStage()
        assert stage.handled_event_type == EventType.EVIDENCE_GRAPH_BUILT
