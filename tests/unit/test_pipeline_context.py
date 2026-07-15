from uuid import UUID

import pytest

from specmetrics.kernel import PipelineContext


class TestPipelineContextImmutability:
    def test_context_is_frozen(self) -> None:
        ctx = PipelineContext()
        with pytest.raises(AttributeError):
            ctx.execution_id = "changed"  # type: ignore

    def test_with_stage_output_returns_new_instance(self) -> None:
        ctx1 = PipelineContext()
        ctx2 = ctx1.with_stage_output("repository", "/tmp/repo")
        assert ctx1 is not ctx2
        assert ctx1.repository is None
        assert ctx2.repository == "/tmp/repo"
        assert ctx1.execution_id == ctx2.execution_id

    def test_with_stage_output_appends_event(self) -> None:
        ctx = PipelineContext()
        event = MockEvent()
        ctx2 = ctx.with_stage_output("repository", "/tmp/repo", event=event)
        assert len(ctx2.published_events) == 1
        assert ctx2.published_events[0] is event

    def test_each_execution_has_unique_id(self) -> None:
        ctx1 = PipelineContext()
        ctx2 = PipelineContext()
        assert ctx1.execution_id != ctx2.execution_id
        assert isinstance(ctx1.execution_id, UUID)


class MockEvent:
    pass
