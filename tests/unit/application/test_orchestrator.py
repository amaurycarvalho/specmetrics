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

        with (
            patch.object(orch, "discover_plugins") as mock_discover,
            patch.object(orch, "_build_stage_results", return_value=[]),
            patch.object(orch, "_extract_measurement", return_value=None),
            patch.object(orch, "_build_metric_results", return_value=[]),
            patch.object(orch, "_build_stage_details", return_value=[]),
            patch.object(orch, "_build_output_errors", return_value=[]),
            patch.object(orch, "_get_llm_info", return_value=("", "")),
            patch.object(orch, "_handle_export", return_value=None),
            patch("specmetrics.application.orchestrator.PipelineEngine"),
            patch("specmetrics.application.orchestrator.AdapterRegistry"),
        ):
            orch.execute(request)

        mock_discover.assert_called_once_with(metrics_filter=["fpa"])

    def test_execute_without_metrics_filter(self):
        orch = PipelineOrchestrator()
        request = PipelineRequest(
            project_path=Path("."),
            metrics_filter=None,
            output_format=OutputFormat.NONE,
        )

        with (
            patch.object(orch, "discover_plugins") as mock_discover,
            patch.object(orch, "_build_stage_results", return_value=[]),
            patch.object(orch, "_extract_measurement", return_value=None),
            patch.object(orch, "_build_metric_results", return_value=[]),
            patch.object(orch, "_build_stage_details", return_value=[]),
            patch.object(orch, "_build_output_errors", return_value=[]),
            patch.object(orch, "_get_llm_info", return_value=("", "")),
            patch.object(orch, "_handle_export", return_value=None),
            patch("specmetrics.application.orchestrator.PipelineEngine"),
            patch("specmetrics.application.orchestrator.AdapterRegistry"),
        ):
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
        stage_details = [
            StageOutputItem(name="discover", count=5, count_type="documents")
        ]
        output_errors = []

        export_file = orch._write_json_output(
            request,
            ctx,
            tmp_path,
            metric_results,
            stage_details,
            output_errors,
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
        from specmetrics.kernel.plugin_metadata import (
            PluginMetadata,
            PluginStatus,
            PluginType,
        )
        from specmetrics.kernel.plugin_registry import PluginDescriptor, PluginRegistry

        registry = PluginRegistry()

        def make_handler():
            handler = MagicMock()
            type(handler).handled_event_type = property(
                lambda _: EventType.MEASUREMENT_COMPLETED
            )
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


class TestOrchestratorInitState:
    def test_initial_plugin_validator_is_set(self):
        from specmetrics.kernel.plugin_validation import PluginValidator

        orch = PipelineOrchestrator()
        assert isinstance(orch._plugin_validator, PluginValidator)

    def test_initial_config_system_is_none(self):
        orch = PipelineOrchestrator()
        assert orch._config_system is None

    def test_initial_framework_detected_is_empty_string(self):
        orch = PipelineOrchestrator()
        assert orch._framework_detected == ""


class TestOrchestratorListPlugins:
    def _register(self, orch, plugin_id, name=None, version=None, status="registered"):
        from specmetrics.kernel.events import EventType
        from specmetrics.kernel.plugin_metadata import (
            PluginMetadata,
            PluginStatus,
            PluginType,
        )
        from specmetrics.kernel.plugin_registry import PluginDescriptor

        meta = PluginMetadata(
            id=plugin_id,
            api_version="1.0.0",
            plugin_type=PluginType.MEASUREMENT,
            handled_event_types=(EventType.MEASUREMENT_COMPLETED,),
            name=name,
            version=version,
        )
        desc = PluginDescriptor(
            metadata=meta,
            entry_point_name=plugin_id,
            status=PluginStatus(status),
        )
        orch._registry.register(desc)

    def test_name_falls_back_to_id(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa")
        plugins = orch.list_plugins()
        assert plugins[0].name == "fpa"

    def test_name_used_when_present(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa", name="FPA Measurement")
        plugins = orch.list_plugins()
        assert plugins[0].name == "FPA Measurement"

    def test_version_falls_back_to_0_0_0(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa")
        plugins = orch.list_plugins()
        assert plugins[0].version == "0.0.0"

    def test_version_used_when_present(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa", version="2.1.0")
        plugins = orch.list_plugins()
        assert plugins[0].version == "2.1.0"

    def test_plugin_type_and_compat_fields(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa")
        plugins = orch.list_plugins()
        assert plugins[0].type == "measurement"
        assert plugins[0].enabled is True
        assert plugins[0].compatible is True

    def test_enabled_false_for_non_registered(self):
        orch = PipelineOrchestrator()
        self._register(orch, "fpa", status="pending")
        plugins = orch.list_plugins()
        assert plugins[0].enabled is False


class TestOrchestratorVersionInfo:
    def test_version_info_fields(self):
        import sys

        import specmetrics

        orch = PipelineOrchestrator()
        info = orch.get_version_info()
        assert info.platform_version == specmetrics.__version__
        assert info.python_version == sys.version.split()[0]
        assert info.plugins == orch.list_plugins()

    def test_plugins_included_in_version_info(self):
        orch = PipelineOrchestrator()
        info = orch.get_version_info()
        assert isinstance(info.plugins, list)


class TestOrchestratorBuildStageEntities:
    def test_forwards_context_and_export_path(self):
        from unittest.mock import patch

        orch = PipelineOrchestrator()
        ctx = MagicMock()
        event_order = []
        export_path = Path("out.json")
        with patch(
            "specmetrics.application.orchestrator._build_stage_entities"
        ) as mock_build:
            orch._build_stage_entities(ctx, event_order, export_path)
        mock_build.assert_called_once_with(ctx, event_order, export_path)
