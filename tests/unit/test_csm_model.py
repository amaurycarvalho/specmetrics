from __future__ import annotations

import pytest
from pydantic import ValidationError

from specmetrics.kernel.csm.metadata import BuildMetadata
from specmetrics.kernel.csm.model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Constraint,
    CsmConsumer,
    CsmElement,
    Decision,
    EvidenceRef,
    GlossaryTerm,
    OpenQuestion,
    Reference,
    Risk,
    SpecificationActivity,
)

UUID1 = "00000000-0000-4000-8000-000000000001"
UUID2 = "00000000-0000-4000-8000-000000000002"


def _make_evidence_ref(text: str = "test evidence") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id=UUID1,
        document_id="doc1",
        section_id="s1",
        text=text,
    )


def _make_build_metadata() -> BuildMetadata:
    return BuildMetadata(run_id="run-1")


class TestCsmElement:
    def test_base_construction(self):
        refs = [_make_evidence_ref()]
        element = CsmElement(
            id=UUID1,
            description="test element",
            evidence_references=refs,
        )
        assert element.id == UUID1
        assert element.evidence_references == refs
        assert element.status == "active"

    def test_status_superseded(self):
        refs = [_make_evidence_ref()]
        element = CsmElement(
            id=UUID1,
            description="test",
            evidence_references=refs,
            status="superseded",
        )
        assert element.status == "superseded"


class TestDecision:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        d = Decision(
            id=UUID1,
            description="We decided to use Python",
            evidence_references=refs,
            rationale="Best ecosystem",
            alternatives=["Java", "Go"],
            timestamp="2026-07-17T00:00:00Z",
        )
        assert d.id == UUID1
        assert d.rationale == "Best ecosystem"
        assert d.alternatives == ["Java", "Go"]
        assert d.timestamp == "2026-07-17T00:00:00Z"


class TestAssumption:
    def test_construction_defaults(self):
        refs = [_make_evidence_ref()]
        a = Assumption(
            id=UUID1,
            description="Users will have internet access",
            evidence_references=refs,
        )
        assert a.validated_date is None

    def test_validated(self):
        refs = [_make_evidence_ref()]
        a = Assumption(
            id=UUID1,
            description="Test",
            evidence_references=refs,
            validated_date="2026-07-17",
        )
        assert a.validated_date == "2026-07-17"


class TestConstraint:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        c = Constraint(
            id=UUID1,
            description="Must use HTTPS",
            evidence_references=refs,
            constraint_type="regulatory",
        )
        assert c.constraint_type == "regulatory"

    def test_invalid_constraint_type(self):
        refs = [_make_evidence_ref()]
        with pytest.raises(ValidationError):
            Constraint(
                id=UUID1,
                description="Test",
                evidence_references=refs,
                constraint_type="invalid",
            )


class TestRisk:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        r = Risk(
            id=UUID1,
            description="Risk of scope creep",
            evidence_references=refs,
            probability="medium",
            impact="high",
            mitigation="Strict change control",
        )
        assert r.probability == "medium"
        assert r.impact == "high"


class TestOpenQuestion:
    def test_construction_defaults(self):
        refs = [_make_evidence_ref()]
        q = OpenQuestion(
            id=UUID1,
            description="What is the target response time?",
            evidence_references=refs,
        )
        assert q.resolved is False
        assert q.resolution == ""

    def test_resolved(self):
        refs = [_make_evidence_ref()]
        q = OpenQuestion(
            id=UUID1,
            description="Test",
            evidence_references=refs,
            resolved=True,
            resolution="Under 200ms",
        )
        assert q.resolved is True
        assert q.resolution == "Under 200ms"


class TestAcceptanceCriterion:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        ac = AcceptanceCriterion(
            id=UUID1,
            description="Given a user logs in, then they see dashboard",
            evidence_references=refs,
        )
        assert ac.verification_method == "test"

    def test_verification_method_review(self):
        refs = [_make_evidence_ref()]
        ac = AcceptanceCriterion(
            id=UUID1,
            description="Test",
            evidence_references=refs,
            verification_method="review",
        )
        assert ac.verification_method == "review"


class TestGlossaryTerm:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        gt = GlossaryTerm(
            id=UUID1,
            description="A measure of code complexity",
            evidence_references=refs,
            aliases=["CC", "Cyclomatic complexity"],
        )
        assert gt.aliases == ["CC", "Cyclomatic complexity"]


class TestReference:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        ref = Reference(
            id=UUID1,
            description="Some unclassified text",
            evidence_references=refs,
            original_label="OpenSpec Explore",
        )
        assert ref.original_label == "OpenSpec Explore"


class TestSpecificationActivity:
    def test_construction(self):
        refs = [_make_evidence_ref()]
        sa = SpecificationActivity(
            id=UUID1,
            description="Explored alternatives for auth",
            evidence_references=refs,
            activity_type="exploration",
        )
        assert sa.activity_type == "exploration"
        assert sa.activity_status == "completed"
        assert sa.linked_decisions == []

    def test_with_linked_entities(self):
        refs = [_make_evidence_ref()]
        sa = SpecificationActivity(
            id=UUID1,
            description="Review session",
            evidence_references=refs,
            activity_type="review",
            activity_status="in_progress",
            linked_decisions=[UUID2],
            linked_questions=[UUID2],
        )
        assert sa.linked_decisions == [UUID2]
        assert sa.linked_questions == [UUID2]


class TestCanonicalSpecificationModel:
    def test_frozen_model(self):
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            metadata=metadata,
        )
        with pytest.raises(ValidationError):
            csm.run_id = "changed"

    def test_empty_model(self):
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            metadata=metadata,
        )
        assert csm.get_element("nonexistent") is None
        assert csm.get_elements("decisions") == {}

    def test_get_element(self):
        refs = [_make_evidence_ref()]
        metadata = _make_build_metadata()
        d = Decision(id=UUID1, description="Test decision", evidence_references=refs)
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={UUID1: d},
            metadata=metadata,
        )
        assert csm.get_element(UUID1) == d

    def test_get_elements_by_category(self):
        refs = [_make_evidence_ref()]
        metadata = _make_build_metadata()
        d1 = Decision(id=UUID1, description="Decision 1", evidence_references=refs)
        d2 = Decision(id=UUID2, description="Decision 2", evidence_references=refs)
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={UUID1: d1, UUID2: d2},
            metadata=metadata,
        )
        result = csm.get_elements("decisions")
        assert len(result) == 2
        assert UUID1 in result
        assert UUID2 in result

    def test_get_elements_by_evidence(self):
        refs1 = [_make_evidence_ref()]
        refs2 = [
            EvidenceRef(
                graph_node_id=UUID2,
                document_id="doc2",
                section_id="s2",
                text="other evidence",
            )
        ]
        metadata = _make_build_metadata()
        d1 = Decision(id=UUID1, description="Decision 1", evidence_references=refs1)
        d2 = Decision(id=UUID2, description="Decision 2", evidence_references=refs2)
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={UUID1: d1, UUID2: d2},
            metadata=metadata,
        )
        result = csm.get_elements_by_evidence("doc1")
        assert len(result) == 1
        assert result[0] == d1

    def test_trace_evidence(self):
        refs = [_make_evidence_ref("specific evidence")]
        metadata = _make_build_metadata()
        d = Decision(id=UUID1, description="Test", evidence_references=refs)
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={UUID1: d},
            metadata=metadata,
        )
        result = csm.trace_evidence(UUID1)
        assert result == refs

    def test_trace_evidence_nonexistent(self):
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            metadata=metadata,
        )
        assert csm.trace_evidence("nonexistent") is None

    def test_immutability_enforced(self):
        refs = [_make_evidence_ref()]
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            metadata=metadata,
        )
        with pytest.raises(ValidationError):
            csm.decisions = {
                UUID1: Decision(id=UUID1, description="x", evidence_references=refs)
            }


class TestCsmConsumer:
    def test_protocol_conformance(self):
        class MockConsumer:
            def consume(self, csm):
                return {
                    "status": "ok",
                    "element_count": len(csm.get_elements("decisions")),
                }

        consumer = MockConsumer()
        assert isinstance(consumer, CsmConsumer)

        refs = [_make_evidence_ref()]
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(id=UUID1, description="x", evidence_references=refs)
            },
            metadata=metadata,
        )
        result = consumer.consume(csm)
        assert result["status"] == "ok"
        assert result["element_count"] == 1

    def test_serialization_roundtrip(self):
        refs = [_make_evidence_ref()]
        metadata = _make_build_metadata()
        csm = CanonicalSpecificationModel(
            run_id="run-1",
            decisions={
                UUID1: Decision(id=UUID1, description="x", evidence_references=refs)
            },
            metadata=metadata,
        )
        json_str = csm.model_dump_json()
        restored = CanonicalSpecificationModel.model_validate_json(json_str)
        assert restored.run_id == csm.run_id
        assert len(restored.decisions) == 1
        assert restored.decisions[UUID1].description == "x"
