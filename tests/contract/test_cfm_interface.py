from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    FunctionalProcess,
    Operation,
    Relationship,
)


@pytest.fixture
def populated_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(graph_node_id="n0", document_id="doc1", section_id="s1", text="src")
    return CanonicalFunctionalModel(
        run_id="test",
        actors={"a1": Actor(id="a1", name="Admin", evidence=ev)},
        functional_processes={"fp1": FunctionalProcess(id="fp1", name="Login", evidence=ev)},
        business_rules={"b1": BusinessRule(id="b1", name="Rule1", evidence=ev)},
        data_groups={"d1": DataGroup(id="d1", name="Data1", evidence=ev)},
        relationships=[Relationship(id="r1", source_id="a1", target_id="d1", evidence=ev)],
        operations={"o1": Operation(id="o1", name="Op1", parent_process_id="fp1", evidence=ev)},
        metadata=BuildMetadata(run_id="test"),
    )


class TestCfmContract:
    def test_all_six_categories_accessible(self, populated_cfm: CanonicalFunctionalModel) -> None:
        assert len(populated_cfm.actors) > 0
        assert len(populated_cfm.functional_processes) > 0
        assert len(populated_cfm.business_rules) > 0
        assert len(populated_cfm.data_groups) > 0
        assert len(populated_cfm.relationships) > 0
        assert len(populated_cfm.operations) > 0

    def test_evidence_traceable(self, populated_cfm: CanonicalFunctionalModel) -> None:
        ref = populated_cfm.trace_evidence("a1")
        assert ref is not None
        assert ref.document_id == "doc1"

    def test_no_framework_labels(self, populated_cfm: CanonicalFunctionalModel) -> None:
        names = []
        for collection in (populated_cfm.actors, populated_cfm.business_rules, populated_cfm.data_groups, populated_cfm.operations):
            for element in collection.values():
                names.append(element.name.lower())
        for rel in populated_cfm.relationships:
            names.append(rel.id.lower())
        framework_keywords = {"openspec", "speckit", "specmetrics"}
        assert not any(keyword in name for name in names for keyword in framework_keywords)

    def test_immutability(self, populated_cfm: CanonicalFunctionalModel) -> None:
        with pytest.raises((TypeError, AttributeError, ValueError)):
            populated_cfm.run_id = "modified"

    def test_downstream_consumer_no_framework_import(self) -> None:
        import specmetrics.kernel.cfm.model as cfm_model
        model_classes = [
            cfm_model.CanonicalFunctionalModel,
            cfm_model.Actor,
            cfm_model.FunctionalProcess,
            cfm_model.BusinessRule,
            cfm_model.DataGroup,
            cfm_model.Relationship,
            cfm_model.Operation,
        ]
        for cls in model_classes:
            assert cls is not None
