from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
    BuildMetadata,
)
from specmetrics.plugins.measurement.bcp.story_generator import generate_story


def _uid() -> str:
    return str(uuid.uuid4())


def _make_evidence(text: str = "ev") -> EvidenceRef:
    return EvidenceRef(
        graph_node_id="gn-001", document_id="doc-001", text=text
    )


def _make_cfm() -> tuple[CanonicalFunctionalModel, str]:
    ev = _make_evidence()
    actor_id = _uid()
    op_id = _uid()
    dg_id = _uid()
    fp_id = _uid()
    br_id = _uid()
    rel_id = _uid()

    actors = {
        actor_id: Actor(id=actor_id, name="Customer", evidence=ev)
    }
    operations = {
        op_id: Operation(
            id=op_id,
            name="Validate Input",
            parent_process_id=fp_id,
            evidence=ev,
        )
    }
    data_groups = {
        dg_id: DataGroup(id=dg_id, name="Order Data", evidence=ev)
    }
    business_rules = {
        br_id: BusinessRule(
            id=br_id,
            name="Min Order",
            description="Order must be at least $10",
            related_process_ids=[fp_id],
            evidence=ev,
        )
    }
    relationships = [
        Relationship(
            id=rel_id,
            source_id=fp_id,
            target_id=_uid(),
            relationship_type="communicates_with",
            evidence=ev,
        )
    ]

    fp = FunctionalProcess(
        id=fp_id,
        name="Place Order",
        description="Place a new order",
        actor_ids=[actor_id],
        operation_ids=[op_id],
        data_group_ids=[dg_id],
        evidence=ev,
    )

    cfm = CanonicalFunctionalModel(
        run_id="test",
        actors=actors,
        functional_processes={fp_id: fp},
        business_rules=business_rules,
        data_groups=data_groups,
        operations=operations,
        relationships=relationships,
        metadata=BuildMetadata(
            run_id="test", version="1.0", source="test"
        ),
    )

    return cfm, fp_id


class TestStoryGenerator:
    def test_generates_title(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "# User Story: Place Order" in story

    def test_includes_description(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "As a Customer, I want to Place a new order" in story

    def test_includes_actor_names(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "Customer" in story

    def test_includes_operations(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "Validate Input" in story

    def test_includes_business_rules(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "Order must be at least $10" in story

    def test_includes_data_groups(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "Order Data" in story

    def test_includes_relationships(self):
        cfm, fp_id = _make_cfm()
        fp = cfm.functional_processes[fp_id]
        story = generate_story(fp, cfm)
        assert "communicates_with" in story

    def test_empty_cfm_fp(self):
        ev = _make_evidence()
        fp_id = _uid()
        fp = FunctionalProcess(
            id=fp_id, name="Empty", evidence=ev
        )
        cfm = CanonicalFunctionalModel(
            run_id="test",
            actors={},
            functional_processes={fp_id: fp},
            business_rules={},
            data_groups={},
            operations={},
            relationships=[],
            metadata=BuildMetadata(
                run_id="test", version="1.0", source="test"
            ),
        )
        story = generate_story(fp, cfm)
        assert "# User Story: Empty" in story
