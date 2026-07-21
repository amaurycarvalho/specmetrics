from __future__ import annotations


from specmetrics.kernel.cfm.model import (
    BuildMetadata,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
)
from specmetrics.plugins.measurement.sfp.plugin import (
    SFPMeasurementPlugin,
    SFPMeasurementHandler,
    create_sfp_measurement_metadata,
)
from specmetrics.kernel.plugin_metadata import PluginType
from specmetrics.kernel.events import EventType


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
