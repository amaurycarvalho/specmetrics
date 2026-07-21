from __future__ import annotations

from specmetrics.kernel.evidence_graph import GraphNode
from specmetrics.kernel.cfm.classifier import _classify_entity


def _node(text: str, section_id: str | None = None) -> GraphNode:
    return GraphNode(
        id="test",
        node_type="extracted_element",
        semantic_type="entity",
        document_id="d1",
        section_id=section_id,
        text=text,
    )


class TestClassifierActorPatterns:
    def test_exact_actor_match(self):
        assert _classify_entity(_node("admin")) == "actor"
        assert _classify_entity(_node("User")) == "actor"
        assert _classify_entity(_node("SYSTEM")) == "actor"

    def test_expanded_actor_patterns(self):
        assert _classify_entity(_node("stakeholder")) == "actor"
        assert _classify_entity(_node("moderator")) == "actor"
        assert _classify_entity(_node("subscriber")) == "actor"
        assert _classify_entity(_node("visitor")) == "actor"
        assert _classify_entity(_node("guest")) == "actor"
        assert _classify_entity(_node("consumer")) == "actor"
        assert _classify_entity(_node("provider")) == "actor"
        assert _classify_entity(_node("vendor")) == "actor"
        assert _classify_entity(_node("partner")) == "actor"


class TestClassifierSectionContext:
    def test_section_actor(self):
        node = _node("CustomEntity", section_id="Actors and Roles")
        assert _classify_entity(node) == "actor"

    def test_section_user(self):
        node = _node("SomeThing", section_id="User Management")
        assert _classify_entity(node) == "actor"

    def test_section_persona(self):
        node = _node("SomeThing", section_id="Persona Definitions")
        assert _classify_entity(node) == "actor"

    def test_section_role(self):
        node = _node("SomeThing", section_id="Role Descriptions")
        assert _classify_entity(node) == "actor"

    def test_no_section_falls_through(self):
        node = _node("ReportData", section_id=None)
        assert _classify_entity(node) == "data_group"


class TestClassifierKeyPhrases:
    def test_acts_as(self):
        node = _node("System X acts as a gateway")
        assert _classify_entity(node) == "actor"

    def test_is_a_user(self):
        node = _node("John is a user of the system")
        assert _classify_entity(node) == "actor"

    def test_represents_a_person(self):
        node = _node("This entity represents a person")
        assert _classify_entity(node) == "actor"

    def test_external_system(self):
        node = _node("Payment Gateway external system")
        assert _classify_entity(node) == "actor"


class TestClassifierRoleSuffix:
    def test_er_suffix(self):
        assert _classify_entity(_node("Manager")) == "actor"

    def test_or_suffix(self):
        assert _classify_entity(_node("Supervisor")) == "actor"

    def test_ist_suffix(self):
        assert _classify_entity(_node("Scientist")) == "actor"

    def test_ian_suffix(self):
        assert _classify_entity(_node("Librarian")) == "actor"

    def test_ant_suffix(self):
        assert _classify_entity(_node("Consultant")) == "actor"

    def test_ent_suffix(self):
        assert _classify_entity(_node("Superintendent")) == "actor"

    def test_eer_suffix(self):
        assert _classify_entity(_node("Engineer")) == "actor"


class TestClassifierDataGroup:
    def test_data_like_name(self):
        assert _classify_entity(_node("UserRecord")) == "data_group"

    def test_report_suffix(self):
        assert _classify_entity(_node("MonthlyReport")) == "data_group"

    def test_account_match(self):
        assert _classify_entity(_node("AdminAccount")) == "data_group"

    def test_unknown_name_defaults_to_data_group(self):
        assert _classify_entity(_node("FooBar")) == "data_group"


class TestClassifierActorPrecedence:
    def test_actor_over_data_group(self):
        node = _node("admin", section_id="Data Model")
        assert _classify_entity(node) == "actor"
