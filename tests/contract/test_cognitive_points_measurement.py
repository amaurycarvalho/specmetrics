from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.measurement.cognitive_points.models import (
    CognitivePointsMeasurement,
    FibonacciNormalizationResult,
    FunctionalValidationEffort,
    MeasurementMetadata,
    SpecificationReviewEffort,
)
from specmetrics.plugins.measurement.cognitive_points.plugin import (
    CognitivePointsHandler,
    create_cognitive_points_measurement_metadata,
)


class TestMeasurementAPIContract:
    def test_plugin_metadata_type(self):
        metadata = create_cognitive_points_measurement_metadata()
        assert metadata.plugin_type == PluginType.MEASUREMENT

    def test_plugin_metadata_id(self):
        metadata = create_cognitive_points_measurement_metadata()
        assert metadata.id == "cognitive_points"

    def test_handler_event_type(self):
        handler = CognitivePointsHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED

    def test_handler_id(self):
        handler = CognitivePointsHandler()
        assert handler.handler_id == "cognitive_points_measurement"

    def test_handler_stage_name(self):
        handler = CognitivePointsHandler()
        assert handler.stage_name == "Cognitive Points Measurement"

    def test_result_model_required_fields(self):
        m = CognitivePointsMeasurement(
            run_id="contract-test",
            total_cognitive_points=8,
            raw_score=25.0,
            specification_review_effort=SpecificationReviewEffort(
                total_raw=10.0
            ),
            functional_validation_effort=FunctionalValidationEffort(
                total_raw=15.0
            ),
            fibonacci_normalization=FibonacciNormalizationResult(
                raw_score=25.0, threshold_applied=22, output_value=8
            ),
            measurement_metadata=MeasurementMetadata(
                total_elements_processed=6
            ),
        )
        assert m.run_id == "contract-test"
        assert m.total_cognitive_points == 8
        assert m.raw_score == 25.0
        assert m.specification_review_effort.total_raw == 10.0
        assert m.functional_validation_effort.total_raw == 15.0
        assert m.measurement_metadata.total_elements_processed == 6
