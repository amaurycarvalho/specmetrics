from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from specmetrics.application.enums import OutputFormat
from specmetrics.application.models import (
    METRIC_NAME_MAP,
    PipelineRequest,
)
from specmetrics.application.orchestrator import PipelineOrchestrator


class TestOrchestratorMetricFiltering:
    def test_execute_passes_metrics_filter_to_discover(self):
        orch = PipelineOrchestrator()
        request = PipelineRequest(
            project_path=Path("."),
            metrics_filter=["fpa"],
            output_format=OutputFormat.NONE,
        )

        with patch.object(orch, "discover_plugins") as mock_discover:
            with patch.object(orch, "_build_stage_results", return_value=[]):
                with patch.object(orch, "_extract_measurement", return_value=None):
                    with patch.object(orch, "_build_metric_results", return_value=[]):
                        with patch.object(orch, "_build_stage_details", return_value=[]):
                            with patch.object(orch, "_build_output_errors", return_value=[]):
                                with patch.object(orch, "_get_llm_info", return_value=("", "")):
                                    with patch.object(orch, "_handle_export", return_value=None):
                                        with patch("specmetrics.application.orchestrator.PipelineEngine"):
                                            with patch("specmetrics.application.orchestrator.AdapterRegistry"):
                                                orch.execute(request)

        mock_discover.assert_called_once_with(metrics_filter=["fpa"])

    def test_execute_without_metrics_filter(self):
        orch = PipelineOrchestrator()
        request = PipelineRequest(
            project_path=Path("."),
            metrics_filter=None,
            output_format=OutputFormat.NONE,
        )

        with patch.object(orch, "discover_plugins") as mock_discover:
            with patch.object(orch, "_build_stage_results", return_value=[]):
                with patch.object(orch, "_extract_measurement", return_value=None):
                    with patch.object(orch, "_build_metric_results", return_value=[]):
                        with patch.object(orch, "_build_stage_details", return_value=[]):
                            with patch.object(orch, "_build_output_errors", return_value=[]):
                                with patch.object(orch, "_get_llm_info", return_value=("", "")):
                                    with patch.object(orch, "_handle_export", return_value=None):
                                        with patch("specmetrics.application.orchestrator.PipelineEngine"):
                                            with patch("specmetrics.application.orchestrator.AdapterRegistry"):
                                                orch.execute(request)

        mock_discover.assert_called_once_with(metrics_filter=None)

    def test_build_metric_results_with_filter(self):
        orch = PipelineOrchestrator()
        ctx = MagicMock()
        ctx.measurement_result = {"fpa_total_function_points": 42}

        results = orch._build_metric_results(ctx, metrics_filter=["fpa"])
        assert len(results) == 1
        assert results[0].name == "function_points"
        assert results[0].total == 42

    def test_build_metric_results_without_filter_all_metrics(self):
        orch = PipelineOrchestrator()
        ctx = MagicMock()
        ctx.measurement_result = {
            "fpa_total_function_points": 42,
            "bcp_measured_items": 10,
        }

        results = orch._build_metric_results(ctx, metrics_filter=None)
        assert len(results) == len(METRIC_NAME_MAP)

    def test_build_metric_results_empty_context(self):
        orch = PipelineOrchestrator()
        ctx = MagicMock()
        ctx.measurement_result = None

        results = orch._build_metric_results(ctx, metrics_filter=["fpa"])
        assert results == []


class TestOrchestratorOutput:
    def test_write_json_output(self, tmp_path):
        from specmetrics.application.models import MetricOutputItem, StageOutputItem

        orch = PipelineOrchestrator()
        request = PipelineRequest(
            project_path=Path("."),
            metrics_filter=["fpa"],
            output_format=OutputFormat.TEXT,
        )
        ctx = MagicMock()

        metric_results = [MetricOutputItem(name="function_points", total=42)]
        stage_details = [StageOutputItem(name="discover", count=5, count_type="documents")]
        output_errors = []

        export_file = orch._write_json_output(
            request, ctx, tmp_path,
            metric_results, stage_details, output_errors,
        )

        assert export_file.exists()
        content = export_file.read_text()
        assert "function_points" in content
        assert "discover" in content
        assert "measure" in content


class TestPluginRegistryFiltering:
    def test_install_handlers_with_filter(self):
        from specmetrics.kernel.events import EventType
        from specmetrics.kernel.handler_registry import HandlerRegistry
        from specmetrics.kernel.plugin_metadata import PluginMetadata, PluginStatus, PluginType
        from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry

        registry = PluginRegistry()

        def make_handler():
            handler = MagicMock()
            type(handler).handled_event_type = property(lambda _: EventType.MEASUREMENT_COMPLETED)
            type(handler).handler_id = property(lambda _: "test_handler")
            type(handler).stage_name = property(lambda _: "Test")
            return handler

        for pid in ["fpa", "sfp", "bcp"]:
            meta = PluginMetadata(
                id=pid,
                api_version="1.0",
                plugin_type=PluginType.MEASUREMENT,
                handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
                handler_factory=make_handler,
            )
            desc = PluginDescriptor(
                metadata=meta,
                entry_point_name=f"specmetrics.plugins.measurement.{pid}",
                status=PluginStatus.REGISTERED,
            )
            registry.register(desc)

        handler_reg = HandlerRegistry()
        registry.install_handlers(handler_reg, metrics_filter=["fpa"])

        handlers = handler_reg.resolve_all(EventType.MEASUREMENT_COMPLETED)
        assert len(handlers) == 1
