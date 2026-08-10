from __future__ import annotations

import pytest
import structlog

from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.kernel.events import EventType
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.plugins.measurement.sfp import plugin as sfp_plugin
from specmetrics.plugins.measurement.sfp.models import RulePack, SFPMeasurementResult
from specmetrics.plugins.measurement.sfp.plugin import (
    SFPMeasurementHandler,
    SFPMeasurementPlugin,
    create_sfp_measurement_metadata,
)


def _make_evidence(
    graph_node_id: str = "gn-001",
    document_id: str = "doc-001",
    section_id: str = "s1",
    text: str = "test evidence",
) -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=graph_node_id,
        document_id=document_id,
        section_id=section_id,
        text=text,
    )


def _make_cfm() -> CanonicalFunctionalModel:
    ev = _make_evidence()
    return CanonicalFunctionalModel(
        run_id="test-run-001",
        operations={
            "op-001": Operation(
                id="op-001",
                name="Create Order",
                parent_process_id="fp-001",
                evidence=ev,
                metadata={"node_type": "elementary_process"},
            ),
        },
        data_groups={
            "dg-001": DataGroup(
                id="dg-001",
                name="Customer",
                evidence=ev,
                metadata={"node_type": "data_group"},
            ),
        },
        metadata=BuildMetadata(run_id="test-run-001", version="1.0", source="test"),
    )


class TestT017_MeasurementExplanationCompleteness:
    def test_explanation_has_required_fields(self):
        cfm = _make_cfm()
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        for explanation in result.explanations:
            assert explanation.identification_reason
            assert explanation.contribution_reason
            assert isinstance(explanation.evidence_chain, list)
            assert len(explanation.evidence_chain) > 0


class TestT032_PluginDiscovery:
    def test_plugin_id(self):
        plugin = SFPMeasurementPlugin()
        assert plugin.plugin_id() == "sfp"

    def test_supported_component_types(self):
        plugin = SFPMeasurementPlugin()
        types = plugin.supported_component_types()
        assert "functional_process" in types
        assert "logical_function" in types

    def test_metadata_plugin_type(self):
        metadata = create_sfp_measurement_metadata()
        assert metadata.id == "sfp"
        assert metadata.plugin_type == PluginType.MEASUREMENT


class TestT033_MeasurementCompletedEvent:
    def test_handler_handles_event_type(self):
        handler = SFPMeasurementHandler()
        assert handler.handled_event_type == EventType.MEASUREMENT_COMPLETED

    def test_handler_stage_name(self):
        handler = SFPMeasurementHandler()
        assert handler.stage_name == "SFP Measurement"


class TestT044_EdgeCases:
    def test_empty_cfm_plugin_measurement(self):
        cfm = CanonicalFunctionalModel(
            run_id="empty-run",
            metadata=BuildMetadata(run_id="empty-run", version="1.0", source="test"),
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        assert result.summary.total_component_count == 0
        assert result.summary.total_sfp == 0.0

    def test_cfm_with_unclassified_elements(self):
        ev = _make_evidence()
        from specmetrics.kernel.cfm.model import UnclassifiedElement

        cfm = CanonicalFunctionalModel(
            run_id="test-unclassified",
            operations={
                "op-001": Operation(
                    id="op-001",
                    name="Create Order",
                    parent_process_id="fp-001",
                    evidence=ev,
                    metadata={"node_type": "elementary_process"},
                ),
            },
            unclassified={
                "uc-001": UnclassifiedElement(
                    id="uc-001",
                    original_type="unknown",
                    content="some content",
                    evidence=ev,
                ),
            },
            metadata=BuildMetadata(
                run_id="test-unclassified", version="1.0", source="test"
            ),
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1


class TestT045_CyclicReferences:
    def test_cyclic_relationships_do_not_crash_plugin(self):
        ev = _make_evidence()
        from specmetrics.kernel.cfm.model import Relationship

        cfm = CanonicalFunctionalModel(
            run_id="test-cyclic",
            operations={
                "op-001": Operation(
                    id="op-001",
                    name="Create Order",
                    parent_process_id="fp-001",
                    evidence=ev,
                    metadata={"node_type": "elementary_process"},
                ),
            },
            data_groups={
                "dg-001": DataGroup(
                    id="dg-001",
                    name="Customer",
                    evidence=ev,
                    metadata={"node_type": "data_group"},
                ),
            },
            relationships=[
                Relationship(
                    id="rel-001",
                    source_id="op-001",
                    target_id="dg-001",
                    relationship_type="uses",
                    evidence=ev,
                ),
                Relationship(
                    id="rel-002",
                    source_id="dg-001",
                    target_id="op-001",
                    relationship_type="governs",
                    evidence=ev,
                ),
                Relationship(
                    id="rel-003",
                    source_id="op-001",
                    target_id="op-001",
                    relationship_type="triggers",
                    evidence=ev,
                ),
            ],
            metadata=BuildMetadata(run_id="test-cyclic", version="1.0", source="test"),
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        assert result.summary.total_component_count == 2
        assert result.summary.total_sfp > 0

    def test_deeply_nested_cyclic_references(self):
        from specmetrics.kernel.cfm.model import Relationship

        ops = {}
        for i in range(100):
            ev = _make_evidence(text=f"process evidence {i}")
            ops[f"op-{i:03d}"] = Operation(
                id=f"op-{i:03d}",
                name=f"Process {i}",
                parent_process_id="fp-001",
                evidence=ev,
                metadata={"node_type": "elementary_process"},
            )
        rels = []
        for i in range(99):
            rels.append(
                Relationship(
                    id=f"rel-{i:03d}",
                    source_id=f"op-{i:03d}",
                    target_id=f"op-{i + 1:03d}",
                    relationship_type="triggers",
                    evidence=_make_evidence(text=f"relationship {i}"),
                )
            )
        rels.append(
            Relationship(
                id="rel-loop",
                source_id="op-099",
                target_id="op-000",
                relationship_type="triggers",
                evidence=_make_evidence(text="relationship loop"),
            )
        )
        cfm = CanonicalFunctionalModel(
            run_id="test-deep-cyclic",
            operations=ops,
            relationships=rels,
            metadata=BuildMetadata(
                run_id="test-deep-cyclic", version="1.0", source="test"
            ),
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm)
        assert result.summary.total_component_count == 100


class TestMeasureErrorHandling:
    def test_measure_none_raises_clear_error(self):
        with pytest.raises(ValueError, match="CFM input cannot be None"):
            SFPMeasurementPlugin().measure(None)


class TestAsyncExecution:
    def test_async_execution_returns_awaitable_result(self):
        import asyncio

        out = SFPMeasurementPlugin().measure(_make_cfm(), async_execution=True)

        async def _await(it):
            return await it

        result = asyncio.run(_await(out))
        assert isinstance(result, SFPMeasurementResult)


class TestMetadataFields:
    def test_metadata_full_content(self):
        metadata = create_sfp_measurement_metadata()
        assert metadata.id == "sfp"
        assert metadata.api_version == "0.1.0"
        assert metadata.plugin_type == PluginType.MEASUREMENT
        assert metadata.handled_event_types == (EventType.MEASUREMENT_COMPLETED,)
        assert isinstance(metadata.handler_factory(), SFPMeasurementHandler)
        assert metadata.name == "SFP Simple Function Points"
        assert metadata.description == (
            "Simple Function Points (SFP) measurement methodology"
        )
        assert metadata.version == "0.1.0"


class TestRulePackMeasurement:
    def test_rule_pack_element_inclusions_override_node(self):
        ev = _make_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="test-inclusions",
            operations={
                "op-001": Operation(
                    id="op-001",
                    name="Internal",
                    parent_process_id="fp-001",
                    evidence=ev,
                    metadata={"node_type": "internal_step"},
                ),
            },
            metadata=BuildMetadata(
                run_id="test-inclusions", version="1.0", source="test"
            ),
        )
        rule_pack = RulePack(
            id="include-rules",
            methodology="SFP",
            element_inclusions={"by_id": ["op-001"], "by_pattern": []},
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm, rule_pack=rule_pack)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1

    def test_rule_pack_inclusion_criteria_node_types(self):
        ev = _make_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="test-criteria",
            operations={
                "op-001": Operation(
                    id="op-001",
                    name="Custom",
                    parent_process_id="fp-001",
                    evidence=ev,
                    metadata={"node_type": "custom_process"},
                ),
            },
            metadata=BuildMetadata(
                run_id="test-criteria", version="1.0", source="test"
            ),
        )
        rule_pack = RulePack(
            id="criteria-rules",
            methodology="SFP",
            inclusion_criteria={
                "functional_process": {
                    "node_types": ["custom_process"],
                    "semantic_types": [],
                }
            },
        )
        plugin = SFPMeasurementPlugin()
        result = plugin.measure(cfm, rule_pack=rule_pack)
        fps = [
            c
            for c in result.measured_components
            if c.component_type == "functional_process"
        ]
        assert len(fps) == 1


class _RecordingHistogram:
    def __init__(self):
        self.recorded: list[object] = []

    def record(self, value):
        self.recorded.append(value)


class _RecordingGauge:
    def __init__(self):
        self.values: list[object] = []

    def set(self, value):
        self.values.append(value)


class TestRecordMetrics:
    def test_records_metrics_for_counter_result(self, monkeypatch):
        hist = _RecordingHistogram()
        fp_gauge = _RecordingGauge()
        lf_gauge = _RecordingGauge()
        monkeypatch.setattr(sfp_plugin, "_measurement_duration", hist)
        monkeypatch.setattr(sfp_plugin, "_fp_gauge", fp_gauge)
        monkeypatch.setattr(sfp_plugin, "_lf_gauge", lf_gauge)

        ev = _make_evidence()
        cfm = CanonicalFunctionalModel(
            run_id="metrics-run",
            operations={
                f"op-00{i}": Operation(
                    id=f"op-00{i}",
                    name=f"Process {i}",
                    parent_process_id="fp-001",
                    evidence=_make_evidence(text=f"op {i}"),
                    metadata={"node_type": "elementary_process"},
                )
                for i in range(2)
            },
            data_groups={
                "dg-001": DataGroup(
                    id="dg-001",
                    name="Customer",
                    evidence=ev,
                    metadata={"node_type": "data_group"},
                ),
            },
            metadata=BuildMetadata(
                run_id="metrics-run", version="1.0", source="test"
            ),
        )
        SFPMeasurementPlugin().measure(cfm)
        self._assert_metrics(hist, fp_gauge, lf_gauge)

    def _assert_metrics(self, hist, fp_gauge, lf_gauge):
        assert hist.recorded and isinstance(hist.recorded[0], float)
        assert fp_gauge.values == [2]
        assert lf_gauge.values == [1]


class TestMeasurementLogEvents:
    def test_measurement_log_events_content(self):
        cfm = _make_cfm()
        with structlog.testing.capture_logs() as cap:
            SFPMeasurementPlugin().measure(cfm)
        events = {e["event"]: e for e in cap}
        started = events["sfp_measurement_started"]
        completed = events["sfp_measurement_completed"]
        assert started["component_count"] == 2
        assert started["rule_pack_id"] is None
        assert completed["total_components"] == 2
        assert completed["total_sfp"] == pytest.approx(11.7)
        assert isinstance(completed["warnings_count"], int)
        assert isinstance(completed["duration_ms"], float)
        assert completed["duration_ms"] >= 0

    def test_measurement_log_counts_rule_pack_id(self):
        rule_pack = RulePack(id="rp-xyz")
        with structlog.testing.capture_logs() as cap:
            cfm = _make_cfm()
            SFPMeasurementPlugin().measure(cfm, rule_pack=rule_pack)
        events = {e["event"]: e for e in cap}
        started = events["sfp_measurement_started"]
        assert started["rule_pack_id"] == "rp-xyz"


from specmetrics.plugins.measurement.sfp.models import (
    MeasuredComponent,
    MeasurementSummary,
)


def _metrics_result() -> SFPMeasurementResult:
    components = [
        MeasuredComponent(
            id="fp-1",
            name="A",
            component_type="functional_process",
            contribution=4.0,
            cfm_element_id="fp-1",
            cfm_element_type="Operation",
        ),
        MeasuredComponent(
            id="fp-2",
            name="B",
            component_type="functional_process",
            contribution=4.0,
            cfm_element_id="fp-2",
            cfm_element_type="Operation",
        ),
        MeasuredComponent(
            id="lf-1",
            name="C",
            component_type="logical_function",
            contribution=2.0,
            cfm_element_id="dg-1",
            cfm_element_type="DataGroup",
        ),
    ]
    return SFPMeasurementResult(
        run_id="r",
        cfm_run_id="c",
        measured_components=components,
        summary=MeasurementSummary(total_component_count=3, total_sfp=10.0),
    )


class TestRecordMetricsMutationKillers:
    def test_duration_recorded_with_value(self, monkeypatch):
        """Kills _record_metrics__mutmut_1/2 (guard inverted + record(None))."""
        hist = _RecordingHistogram()
        fp_gauge = _RecordingGauge()
        lf_gauge = _RecordingGauge()
        monkeypatch.setattr(sfp_plugin, "_measurement_duration", hist)
        monkeypatch.setattr(sfp_plugin, "_fp_gauge", fp_gauge)
        monkeypatch.setattr(sfp_plugin, "_lf_gauge", lf_gauge)
        sfp_plugin._record_metrics(_metrics_result(), 42.5)
        assert hist.recorded == [42.5]

    def test_fp_gauge_counts_functional_processes(self, monkeypatch):
        """Kills _record_metrics__mutmut_3/4/7/8/9/10 (fp counting + set(None))."""
        hist = _RecordingHistogram()
        fp_gauge = _RecordingGauge()
        lf_gauge = _RecordingGauge()
        monkeypatch.setattr(sfp_plugin, "_measurement_duration", hist)
        monkeypatch.setattr(sfp_plugin, "_fp_gauge", fp_gauge)
        monkeypatch.setattr(sfp_plugin, "_lf_gauge", lf_gauge)
        sfp_plugin._record_metrics(_metrics_result(), 1.0)
        assert fp_gauge.values == [2]

    def test_lf_gauge_counts_logical_functions(self, monkeypatch):
        """Kills _record_metrics__mutmut_11/12/15/16/17/18 (lf counting + set(None))."""
        hist = _RecordingHistogram()
        fp_gauge = _RecordingGauge()
        lf_gauge = _RecordingGauge()
        monkeypatch.setattr(sfp_plugin, "_measurement_duration", hist)
        monkeypatch.setattr(sfp_plugin, "_fp_gauge", fp_gauge)
        monkeypatch.setattr(sfp_plugin, "_lf_gauge", lf_gauge)
        sfp_plugin._record_metrics(_metrics_result(), 1.0)
        assert lf_gauge.values == [1]
