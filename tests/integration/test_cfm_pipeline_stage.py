from __future__ import annotations


import dataclasses

from specmetrics.kernel.cfm.builder import CfmBuilderStage
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext


class TestCfmPipelineStage:
    def test_stage_properties(self) -> None:
        stage = CfmBuilderStage()
        assert stage.handled_event_type == EventType.EVIDENCE_GRAPH_BUILT
        assert stage.handler_id == "cfm_builder_stage"
        assert stage.stage_name == "canonical_model"

    def test_handle_without_evidence_graph_produces_empty(self) -> None:
        stage = CfmBuilderStage()
        context = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.EVIDENCE_GRAPH_BUILT,
            publisher="test",
            payload={},
            context=context,
        )
        result = stage.handle(event)
        assert result.canonical_model is None

    def test_handle_returns_context_with_canonical_model_field(self) -> None:
        stage = CfmBuilderStage()
        context = PipelineContext()
        event = PipelineEvent(
            event_type=EventType.EVIDENCE_GRAPH_BUILT,
            publisher="test",
            payload={},
            context=context,
        )
        result = stage.handle(event)
        assert "canonical_model" in dataclasses.asdict(result)
        assert result.canonical_model is None
