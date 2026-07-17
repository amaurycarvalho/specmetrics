from __future__ import annotations

from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.measurement.bcp.models import (
    BCPMeasurementResult,
    BCPWorkItem,
    ExecutionMetadata,
)
from specmetrics.plugins.measurement.bcp.plugin import (
    BCPHandler,
    create_bcp_measurement_metadata,
)


class TestMeasurementAPIContract:
    def test_plugin_metadata_type(self):
        metadata = create_bcp_measurement_metadata()
        assert metadata.plugin_type == PluginType.MEASUREMENT

    def test_plugin_metadata_id(self):
        metadata = create_bcp_measurement_metadata()
        assert metadata.id == "bcp"

    def test_handler_event_type(self):
        handler = BCPHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED

    def test_handler_id(self):
        handler = BCPHandler()
        assert handler.handler_id == "bcp_measurement"

    def test_handler_stage_name(self):
        handler = BCPHandler()
        assert handler.stage_name == "BCP Measurement"

    def test_result_model_required_fields(self):
        r = BCPMeasurementResult(
            run_id="contract-test",
            total_bcp=25.0,
            items=[
                BCPWorkItem(
                    element_id="fp-001",
                    element_name="A",
                    generated_story="# A",
                    bcp_score=15.0,
                    status="success",
                ),
                BCPWorkItem(
                    element_id="fp-002",
                    element_name="B",
                    generated_story="# B",
                    bcp_score=10.0,
                    status="success",
                ),
            ],
            execution_metadata=ExecutionMetadata(
                duration_ms=50.0,
                total_fps_processed=2,
                items_succeeded=2,
                sdk_call_count=2,
            ),
        )
        assert r.run_id == "contract-test"
        assert r.total_bcp == 25.0
        assert r.method == "BCP"
