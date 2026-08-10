from __future__ import annotations

from specmetrics.kernel.exceptions import (
    HandlerNotFoundError,
    PipelineError,
    PluginError,
    StageError,
)


class TestStageError:
    def test_args_and_attributes(self) -> None:
        err = StageError("extract", "boom")
        assert err.args == ("extract", "boom")
        assert err.stage_name == "extract"
        assert err.message == "boom"

    def test_is_pipeline_error(self) -> None:
        assert isinstance(StageError("s", "m"), PipelineError)


class TestPluginError:
    def test_args_and_attributes(self) -> None:
        err = PluginError("fpa", "init failed")
        assert err.args == ("fpa", "init failed")
        assert err.plugin_id == "fpa"
        assert err.message == "init failed"


class TestHandlerNotFoundError:
    def test_event_type_attribute(self) -> None:
        err = HandlerNotFoundError("MEASUREMENT_COMPLETED")
        assert err.event_type == "MEASUREMENT_COMPLETED"

    def test_message(self) -> None:
        err = HandlerNotFoundError("MEASUREMENT_COMPLETED")
        assert "No handler registered" in str(err)
        assert "MEASUREMENT_COMPLETED" in str(err)
