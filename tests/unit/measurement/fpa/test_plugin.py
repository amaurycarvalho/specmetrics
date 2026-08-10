import pytest

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.pipeline_context import PipelineContext
from specmetrics.plugins.measurement.fpa.models import RulePack
from specmetrics.plugins.measurement.fpa.plugin import (
    FPAMeasurementHandler,
    FPAMeasurementPlugin,
)


def _evidence() -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="n1", document_id="doc1", section_id="s1", text="src"
    )


def _cfm() -> CanonicalFunctionalModel:
    from datetime import UTC, datetime

    return CanonicalFunctionalModel(
        run_id="test-run",
        data_groups={
            "dg1": DataGroup(
                id="dg1",
                name="Orders",
                data_type="internal",
                evidence=_evidence(),
            )
        },
        operations={
            "op1": Operation(
                id="op1",
                name="CreateOrder",
                parent_process_id="p1",
                evidence=_evidence(),
                metadata={"direction": "input"},
            )
        },
        metadata=BuildMetadata(
            run_id="test-run",
            build_duration_ms=0,
            element_counts={},
            total_input_nodes=0,
            unclassified_count=0,
            conflicts=[],
            created_at=datetime.now(UTC),
        ),
    )


class TestFPAMeasurementPlugin:
    def test_plugin_id(self):
        plugin = FPAMeasurementPlugin()
        assert plugin.plugin_id() == "fpa"

    def test_supported_methodology(self):
        plugin = FPAMeasurementPlugin()
        assert "FPA" in plugin.supported_methodology()

    def test_supported_function_types(self):
        plugin = FPAMeasurementPlugin()
        types = plugin.supported_function_types()
        assert "ILF" in types
        assert "EIF" in types
        assert "EI" in types
        assert "EO" in types
        assert "EQ" in types
        assert len(types) == 5

    def test_measure_raises_on_none_cfm(self):
        plugin = FPAMeasurementPlugin()
        with pytest.raises(ValueError, match="CFM input cannot be None"):
            plugin.measure(None)  # type: ignore[arg-type]

    def test_measure_without_rule_pack(self):
        plugin = FPAMeasurementPlugin()
        result = plugin.measure(_cfm())
        assert result.summary.total_function_count == 2
        assert len(result.explanations) == 2

    def test_measure_with_weight_overrides(self):
        plugin = FPAMeasurementPlugin()
        rp = RulePack(id="rp", weight_overrides={"ILF": {"Low": 99}})
        result = plugin.measure(_cfm(), rule_pack=rp)
        assert result.rule_pack_id == "rp"
        ilf = next(
            f for f in result.measured_functions if f.function_type == "ILF"
        )
        assert ilf.ufp_weight == 99
        assert len(result.explanations) == 2

    def test_measure_with_excluded_types(self):
        plugin = FPAMeasurementPlugin()
        rp = RulePack(id="rp", excluded_types=["ILF"])
        result = plugin.measure(_cfm(), rule_pack=rp)
        types = {f.function_type for f in result.measured_functions}
        assert "ILF" not in types
        assert result.summary.total_function_count == 1


class TestFPAMeasurementHandler:
    def _event(self, cfm):
        ctx = PipelineContext(canonical_model=cfm)
        return PipelineEvent(
            event_type=EventType.MEASUREMENT_COMPLETED,
            publisher="test",
            payload={},
            context=ctx,
        )

    def test_handler_identity(self):
        handler = FPAMeasurementHandler()
        assert handler.handler_id == "fpa_measurement"
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED
        assert handler.stage_name == "FPA Measurement"

    def test_handle_returns_payload(self):
        handler = FPAMeasurementHandler()
        ctx = handler.handle(self._event(_cfm()))
        payload = ctx.measurement_result
        assert payload["fpa_total_function_points"] > 0
        assert "fpa_breakdown" in payload
        assert "fpa_complexity_distribution" in payload
        assert "fpa_function_counts" in payload
        assert "fpa_complexity_counts" in payload
        assert len(payload["fpa_entities"]) == 2

    def test_handle_ignores_missing_cfm(self):
        ctx = PipelineContext(canonical_model=None)
        handler = FPAMeasurementHandler()
        result = handler.handle(
            PipelineEvent(
                event_type=EventType.MEASUREMENT_COMPLETED,
                publisher="test",
                payload={},
                context=ctx,
            )
        )
        assert result is ctx


def test_create_fpa_measurement_metadata_exact():
    """Mutmut 1/2/5/6/7/8/9/10/11/12/13/14/15/16/17/18/19/21/22/23/24/25/26/27."""
    from specmetrics.kernel.events import EventType
    from specmetrics.kernel.plugin_metadata import PluginType
    from specmetrics.plugins.measurement.fpa.plugin import (
        FPAMeasurementHandler,
        create_fpa_measurement_metadata,
    )

    md = create_fpa_measurement_metadata()
    assert md.id == "fpa"
    assert md.api_version == "0.1.0"
    assert md.plugin_type == PluginType.MEASUREMENT
    assert md.handled_event_types == (EventType.MEASUREMENT_COMPLETED,)
    assert md.handler_factory is not None
    assert isinstance(md.handler_factory(), FPAMeasurementHandler)
    assert md.name == "FPA Function Point Analysis"
    assert md.description == (
        "IFPUG-approved Albrecht/FPA Function Point measurement methodology"
    )
    assert md.version == "0.1.0"
