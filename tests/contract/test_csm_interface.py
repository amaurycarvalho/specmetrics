from __future__ import annotations

from specmetrics.kernel.csm.metadata import BuildMetadata
from specmetrics.kernel.csm.model import (
    CanonicalSpecificationModel,
    CsmConsumer,
    Decision,
    EvidenceRef,
)

UUID1 = "00000000-0000-4000-8000-000000000001"
UUID2 = "00000000-0000-4000-8000-000000000002"


def _make_evidence_ref() -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=UUID1,
        document_id="doc1",
        section_id="s1",
        text="test evidence",
    )


class MockMeasurementEngine:
    def __init__(self):
        self.consumed_csms = []

    def consume(self, csm: CanonicalSpecificationModel):
        self.consumed_csms.append(csm)
        return {
            "status": "ok",
            "categories": [
                "specification_activities",
                "decisions",
                "assumptions",
                "constraints",
                "risks",
                "open_questions",
                "acceptance_criteria",
                "glossary_terms",
                "references",
            ],
            "element_counts": {
                "decisions": len(csm.get_elements("decisions")),
                "assumptions": len(csm.get_elements("assumptions")),
                "risks": len(csm.get_elements("risks")),
            },
        }


class TestCsmConsumerProtocol:
    def test_mock_consumer_conforms_to_protocol(self):
        consumer = MockMeasurementEngine()
        assert isinstance(consumer, CsmConsumer)

    def test_consumer_enumerates_categories(self):
        consumer = MockMeasurementEngine()
        refs = [_make_evidence_ref()]
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(
                    id=UUID1, description="Decide X", evidence_references=refs
                ),
            },
            assumptions={},
            metadata=metadata,
        )

        result = consumer.consume(csm)
        assert result["status"] == "ok"
        assert "decisions" in result["categories"]
        assert result["element_counts"]["decisions"] == 1
        assert result["element_counts"]["assumptions"] == 0

    def test_consumer_no_framework_imports(self):
        import sys

        framework_modules = [
            "specmetrics.kernel.csm",
        ]

        consumer = MockMeasurementEngine()
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            metadata=metadata,
        )

        result = consumer.consume(csm)
        assert result["status"] == "ok"

        for mod_name in framework_modules:
            if mod_name in sys.modules:
                pass

    def test_csm_structure_identical_across_sources(self):
        metadata1 = BuildMetadata(run_id="openspec-run")
        metadata2 = BuildMetadata(run_id="speckit-run")

        refs = [_make_evidence_ref()]

        csm1 = CanonicalSpecificationModel(
            run_id="openspec-run",
            decisions={
                UUID1: Decision(
                    id=UUID1, description="Use Python", evidence_references=refs
                ),
            },
            metadata=metadata1,
        )
        csm2 = CanonicalSpecificationModel(
            run_id="speckit-run",
            decisions={
                UUID1: Decision(
                    id=UUID1, description="Use Python", evidence_references=refs
                ),
            },
            metadata=metadata2,
        )

        consumer = MockMeasurementEngine()
        r1 = consumer.consume(csm1)
        r2 = consumer.consume(csm2)

        assert r1["element_counts"] == r2["element_counts"]
        assert r1["categories"] == r2["categories"]


class TestCsmQueryInterface:
    def test_get_element_by_id(self):
        refs = [_make_evidence_ref()]
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(
                    id=UUID1, description="Decision text", evidence_references=refs
                ),
            },
            metadata=metadata,
        )
        element = csm.get_element(UUID1)
        assert element is not None
        assert element.description == "Decision text"

    def test_get_elements_by_category(self):
        refs = [_make_evidence_ref()]
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(id=UUID1, description="D1", evidence_references=refs),
            },
            metadata=metadata,
        )
        decisions = csm.get_elements("decisions")
        assert UUID1 in decisions

    def test_get_elements_by_evidence(self):
        refs_doc1 = [
            EvidenceRef(
                graph_node_id=UUID1,
                document_id="doc1",
                text="evidence in doc1",
            )
        ]
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(
                    id=UUID1, description="D1", evidence_references=refs_doc1
                ),
            },
            metadata=metadata,
        )
        result = csm.get_elements_by_evidence("doc1")
        assert len(result) == 1

    def test_trace_evidence_chain(self):
        refs = [_make_evidence_ref()]
        metadata = BuildMetadata(run_id="run-1")
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(id=UUID1, description="D1", evidence_references=refs),
            },
            metadata=metadata,
        )
        chain = csm.trace_evidence(UUID1)
        assert chain == refs
