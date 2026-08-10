from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.measurement.token_points.models import (
    TokenPointsMeasurement,
)
from specmetrics.plugins.measurement.token_points.plugin import (
    TokenPointsHandler,
    create_token_points_measurement_metadata,
)


class TestMeasurementAPIContract:
    def test_plugin_metadata_type(self):
        metadata = create_token_points_measurement_metadata()
        assert metadata.plugin_type == PluginType.MEASUREMENT

    def test_plugin_metadata_id(self):
        metadata = create_token_points_measurement_metadata()
        assert metadata.id == "token_points"

    def test_handler_event_type(self):
        handler = TokenPointsHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED

    def test_handler_id(self):
        handler = TokenPointsHandler()
        assert handler.handler_id == "token_points_measurement"

    def test_handler_stage_name(self):
        handler = TokenPointsHandler()
        assert handler.stage_name == "Token Points Measurement"

    def test_result_model_required_fields(self):
        from specmetrics.plugins.measurement.token_points.models import (
            CodeGenerationCost,
            MeasurementMetadata,
            SpecificationCost,
        )

        m = TokenPointsMeasurement(
            run_id="contract-test",
            total_score=10.0,
            specification_cost=SpecificationCost(total=4.0),
            code_generation_cost=CodeGenerationCost(total=6.0),
            measurement_metadata=MeasurementMetadata(total_elements_processed=5),
        )
        assert m.run_id == "contract-test"
        assert m.total_score == 10.0
        assert m.specification_cost.total == 4.0
        assert m.code_generation_cost.total == 6.0
        assert m.measurement_metadata.total_elements_processed == 5


class TestResolveCalibration:
    def test_resolve_calibration_returns_metadata_profile(self):
        """Kills TokenPointsHandler::_resolve_calibration__mutmut_1 (metadata=None)."""
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.calibration.models import CalibrationProfile
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        profile = CalibrationProfile(version="3.1", content_multiplier=0.99)
        ctx = PipelineContext(metadata=profile)
        resolved = handler._resolve_calibration(ctx)
        assert resolved is profile
        assert resolved.version == "3.1"
        assert resolved.content_multiplier == 0.99

    def test_resolve_calibration_falls_back_to_default_without_metadata(self):
        """Kills TokenPointsHandler::_resolve_calibration__mutmut_1 (default path intact)."""
        from specmetrics.kernel.pipeline_context import PipelineContext
        from specmetrics.plugins.measurement.token_points.plugin import (
            TokenPointsHandler,
        )

        handler = TokenPointsHandler()
        ctx = PipelineContext()
        resolved = handler._resolve_calibration(ctx)
        assert resolved is not None
        assert resolved.version == "1.0"
