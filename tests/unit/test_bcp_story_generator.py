from __future__ import annotations

import uuid

from specmetrics.kernel.cfm.model import (
    Actor,
    BuildMetadata,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
)
from specmetrics.plugins.measurement.bcp.story_generator import (
    _resolve_actor_names,
    _resolve_relationships,
    generate_story,
)


def _uid() -> str:
    return str(uuid.uuid4())


def _make_evidence(text: str = "ev") -> EvidenceRef:
    return EvidenceRef(graph_node_id="gn-001", document_id="doc-001", text=text)


def _make_cfm() -> tuple[CanonicalFunctionalModel, str]:
    ev = _make_evidence()
    actor_id = _uid()
    op_id = _uid()
    dg_id = _uid()
    fp_id = _uid()
    br_id = _uid()
    rel_id = _uid()

    actors = {actor_id: Actor(id=actor_id, name="Customer", evidence=ev)}
    operations = {
        op_id: Operation(
            id=op_id,
            name="Validate Input",
            parent_process_id=fp_id,
            evidence=ev,
        )
    }
    data_groups = {dg_id: DataGroup(id=dg_id, name="Order Data", evidence=ev)}
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
        metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
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
        fp = FunctionalProcess(id=fp_id, name="Empty", evidence=ev)
        cfm = CanonicalFunctionalModel(
            run_id="test",
            actors={},
            functional_processes={fp_id: fp},
            business_rules={},
            data_groups={},
            operations={},
            relationships=[],
            metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
        )
        story = generate_story(fp, cfm)
        assert "# User Story: Empty" in story

    def test_uses_exact_section_headers(self):
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "## Acceptance Criteria" in story
        assert "### Business Rules" in story
        assert "### Data Groups" in story
        assert "### Relationships" in story
        assert "XXXX" not in story

    def test_no_mutation_markers(self):
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "XX" not in story

    def test_multiple_actors_joined_with_comma(self):
        ev = _make_evidence()
        a1 = _uid()
        a2 = _uid()
        fp_id = _uid()
        actors = {
            a1: Actor(id=a1, name="Staff", evidence=ev),
            a2: Actor(id=a2, name="Customer", evidence=ev),
        }
        fp = FunctionalProcess(id=fp_id, name="P", actor_ids=[a2, a1], evidence=ev)
        cfm = CanonicalFunctionalModel(
            run_id="test",
            actors=actors,
            functional_processes={fp_id: fp},
            metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
        )
        story = generate_story(fp, cfm)
        assert "As a Customer, Staff" in story

    def test_resolve_actor_names_empty_when_unknown(self):
        cfm, fp_id = _make_cfm()
        ev = _make_evidence()
        fp = FunctionalProcess(id=fp_id, name="P", actor_ids=["missing"], evidence=ev)
        assert _resolve_actor_names(fp, cfm) == ""

    def test_relationships_include_target_side(self):
        ev = _make_evidence()
        other = _uid()
        fp_id = _uid()
        rel_id = _uid()
        fp = FunctionalProcess(id=fp_id, name="P", evidence=ev)
        rel = Relationship(
            id=rel_id,
            source_id=other,
            target_id=fp_id,
            relationship_type="communicates_with",
            evidence=ev,
        )
        cfm = CanonicalFunctionalModel(
            run_id="test",
            functional_processes={fp_id: fp},
            relationships=[rel],
            metadata=BuildMetadata(run_id="test", version="1.0", source="test"),
        )
        rels = _resolve_relationships(fp, cfm)
        assert len(rels) == 1
        assert "communicates_with" in rels[0]


class TestExactSectionFormatting:
    def test_actor_section_followed_by_blank_line(self):
        """Kills _append_actor__mutmut_10 (blank line replaced with XXXX)."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert (
            "As a Customer, I want to Place a new order\n\n## Acceptance Criteria:"
            in story
        )

    def test_operations_section_header_and_blank_line(self):
        """Kills _append_operations__mutmut_7/8/9/12 (header + blank line)."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "## Acceptance Criteria:\n- Validate Input\n" in story

    def test_business_rules_section_header_and_blank_line(self):
        """Kills _append_business_rules__mutmut_7/8/9/12 (header + blank line)."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "### Business Rules:\n- Order must be at least $10\n" in story

    def test_data_groups_section_header_and_blank_line(self):
        """Kills _append_data_groups__mutmut_7/8/9/12 (header + blank line)."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "### Data Groups:\n- Order Data\n" in story

    def test_relationships_section_header(self):
        """Kills _append_relationships__mutmut_7/8/9 (header literal)."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "### Relationships:\n" in story

    def test_sections_separated_by_blank_lines(self):
        """Kills _append_actor/_operations/_business_rules/_data_groups blank-line mutants."""
        cfm, fp_id = _make_cfm()
        story = generate_story(cfm.functional_processes[fp_id], cfm)
        assert "\n\n## Acceptance Criteria:" in story
        assert "\n\n### Business Rules:" in story
        assert "\n\n### Data Groups:" in story
        assert "\n\n### Relationships:" in story
