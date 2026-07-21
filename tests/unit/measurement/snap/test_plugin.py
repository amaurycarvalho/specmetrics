from __future__ import annotations


from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    BuildMetadata,
)
from specmetrics.plugins.measurement.snap.plugin import (
    SNAPMeasurementPlugin,
    create_snap_measurement_metadata,
)
from specmetrics.plugins.measurement.snap.models import (
    SNAPMeasurementResult,
    AssessedItem,
    AssessmentSummary,
    CategoryAssessment,
    CategoryBreakdown,
)
from specmetrics.plugins.measurement.snap.explainer import AssessmentExplainer


def _make_cfm() -> CanonicalFunctionalModel:
    return CanonicalFunctionalModel(
        run_id="test-run",
        metadata=BuildMetadata(run_id="test-run"),
    )


class TestExplanationCompleteness:
    def test_explanation_includes_required_fields(self):
        item = AssessedItem(
            id="item-1",
            name="Test",
            category_id="presentation",
            contribution=4.0,
            cfm_element_id="elem-1",
            cfm_semantic_marker="presentation_interface",
            evidence_refs=[],
        )
        result = SNAPMeasurementResult(
            run_id="r1",
            cfm_run_id="cfm-r1",
            assessed_items=[item],
            summary=AssessmentSummary(
                total_item_count=1,
                total_active_count=1,
                total_snap=4.0,
                by_category={
                    "presentation": CategoryBreakdown(item_count=1, total_snap=4.0)
                },
            ),
            categories=[
                CategoryAssessment(
                    category_id="presentation",
                    category_name="Presentation",
                    category_version="1.0.0",
                    items=[item],
                    total_contribution=4.0,
                )
            ],
        )
        explainer = AssessmentExplainer()
        explanations = explainer.build_explanations(result)
        assert len(explanations) == 1
        expl = explanations[0]
        assert expl.item_id == "item-1"
        assert expl.identification_reason
        assert expl.contribution_reason
        assert isinstance(expl.evidence_chain, list)


class TestPluginDiscovery:
    def test_plugin_id(self):
        plugin = SNAPMeasurementPlugin()
        assert plugin.plugin_id() == "snap"

    def test_metadata_creation(self):
        metadata = create_snap_measurement_metadata()
        assert metadata.id == "snap"
        assert metadata.plugin_type.value == "measurement"

    def test_supported_methodology(self):
        plugin = SNAPMeasurementPlugin()
        assert "SNAP" in plugin.supported_methodology()

    def test_supported_function_types(self):
        plugin = SNAPMeasurementPlugin()
        types = plugin.supported_function_types()
        assert "presentation" in types
        assert "data_operations" in types


class TestEventEmission:
    def test_plugin_handler_provided(self):
        metadata = create_snap_measurement_metadata()
        assert metadata.handler_factory is not None
        handler = metadata.handler_factory()
        assert handler is not None
        assert handler.handler_id == "snap_measurement"


class TestAsyncExecution:
    def test_async_execution_returns_future(self):
        import asyncio

        plugin = SNAPMeasurementPlugin()
        cfm = _make_cfm()
        result = plugin.measure(cfm, async_execution=True)
        assert asyncio.isfuture(result) or hasattr(result, "set_result")


class TestCorruptedPluginMetadata:
    def test_plugin_metadata_has_required_fields(self):
        metadata = create_snap_measurement_metadata()
        assert metadata.id is not None
        assert metadata.api_version is not None
        assert metadata.version is not None


class TestUnsupportedInteractionTypes:
    def test_plugin_handles_cfm_without_markers(self):
        plugin = SNAPMeasurementPlugin()
        cfm = _make_cfm()
        result = plugin.measure(cfm)
        assert result.summary.total_item_count == 0
        assert result.summary.total_snap == 0.0
