from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.measurement.storypoints.models import (
    ExecutionMetadata,
    FunctionalWorkItem,
    StoryPointMeasurementResult,
)
from specmetrics.plugins.measurement.storypoints.plugin import (
    StoryPointsHandler,
    StoryPointsPlugin,
    create_storypoints_measurement_metadata,
)


class TestMeasurementAPIContract:
    def test_plugin_metadata_type(self):
        metadata = create_storypoints_measurement_metadata()
        assert metadata.plugin_type == PluginType.MEASUREMENT

    def test_plugin_metadata_id(self):
        metadata = create_storypoints_measurement_metadata()
        assert metadata.id == "storypoints"

    def test_handler_event_type(self):
        handler = StoryPointsHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED

    def test_handler_id(self):
        handler = StoryPointsHandler()
        assert handler.handler_id == "storypoints_measurement"

    def test_handler_stage_name(self):
        handler = StoryPointsHandler()
        assert handler.stage_name == "Story Points Measurement"

    def test_result_model_required_fields(self):
        m = StoryPointMeasurementResult(
            run_id="contract-test",
            total_story_points=8,
            total_raw_score=8.0,
            specification_effort_total=0.0,
            implementation_effort_total=8.0,
            items=[
                FunctionalWorkItem(
                    element_id="fp-001",
                    element_name="Login",
                    raw_score=5.0,
                    structural_score=5.0,
                    content_score=0.0,
                    normalized_value=5,
                    factor_breakdown={
                        "business_interactions": 5.0,
                        "logical_information": 0.0,
                        "external_integrations": 0.0,
                        "business_rule_density": 0.0,
                        "workflow_breadth": 0.0,
                        "exception_handling": 0.0,
                    },
                ),
                FunctionalWorkItem(
                    element_id="fp-002",
                    element_name="Logout",
                    raw_score=3.0,
                    structural_score=3.0,
                    content_score=0.0,
                    normalized_value=3,
                    factor_breakdown={
                        "business_interactions": 2.0,
                        "logical_information": 1.0,
                        "external_integrations": 0.0,
                        "business_rule_density": 0.0,
                        "workflow_breadth": 0.0,
                        "exception_handling": 0.0,
                    },
                ),
            ],
            distribution={5: 1, 3: 1},
            execution_metadata=ExecutionMetadata(
                total_fps_processed=2,
                fps_estimated=2,
                fps_merged_as_duplicates=0,
            ),
        )
        assert m.run_id == "contract-test"
        assert m.total_story_points == 8
        assert len(m.items) == 2
        assert m.distribution == {5: 1, 3: 1}

    def test_new_payload_fields_present(self):
        m = StoryPointMeasurementResult(
            run_id="contract-test-2",
            total_story_points=5,
            total_raw_score=5.0,
            specification_effort_total=2.0,
            implementation_effort_total=3.0,
            content_multiplier=0.1,
            content_tokens_by_type={"functional_process": 50, "decision": 20},
            calibration_version="1.0",
            items=[
                FunctionalWorkItem(
                    element_id="fp-001",
                    element_name="Login",
                    raw_score=5.0,
                    structural_score=5.0,
                    content_score=0.0,
                    normalized_value=5,
                    factor_breakdown={
                        "business_interactions": 5.0,
                        "logical_information": 0.0,
                        "external_integrations": 0.0,
                        "business_rule_density": 0.0,
                        "workflow_breadth": 0.0,
                        "exception_handling": 0.0,
                    },
                ),
            ],
            distribution={5: 1},
            execution_metadata=ExecutionMetadata(
                total_fps_processed=1,
                fps_estimated=1,
                fps_merged_as_duplicates=0,
            ),
        )
        assert m.total_raw_score == 5.0
        assert m.specification_effort_total == 2.0
        assert m.implementation_effort_total == 3.0
        assert m.content_multiplier == 0.1
        assert m.content_tokens_by_type == {"functional_process": 50, "decision": 20}
        assert m.calibration_version == "1.0"

    def test_plugin_measure_accepts_csm(self):
        plugin = StoryPointsPlugin()
        assert hasattr(plugin, "measure")
        import inspect
        sig = inspect.signature(plugin.measure)
        params = list(sig.parameters.keys())
        assert "csm" in params
