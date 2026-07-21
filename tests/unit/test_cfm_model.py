from __future__ import annotations

import pytest

from specmetrics.kernel.cfm.metadata import BuildMetadata
from specmetrics.kernel.cfm.model import (
    Actor,
    BusinessRule,
    CanonicalFunctionalModel,
    DataGroup,
    EvidenceRef,
    Operation,
    Relationship,
)


@pytest.fixture
def sample_cfm() -> CanonicalFunctionalModel:
    ev = EvidenceRef(
        graph_node_id="n0", document_id="doc1", section_id="s1", text="source"
    )
    return CanonicalFunctionalModel(
        run_id="test",
        actors={"a1": Actor(id="a1", name="Admin", evidence=ev)},
        functional_processes={},
        business_rules={"b1": BusinessRule(id="b1", name="Rule1", evidence=ev)},
        data_groups={"d1": DataGroup(id="d1", name="Data1", evidence=ev)},
        relationships=[],
        operations={
            "o1": Operation(id="o1", name="Op1", parent_process_id="", evidence=ev)
        },
        metadata=BuildMetadata(run_id="test"),
    )


class TestCanonicalFunctionalModel:
    def test_get_element_by_id(self, sample_cfm: CanonicalFunctionalModel) -> None:
        assert sample_cfm.get_element("a1") is not None
        assert isinstance(sample_cfm.get_element("a1"), Actor)

    def test_get_element_returns_none_for_missing(
        self, sample_cfm: CanonicalFunctionalModel
    ) -> None:
        assert sample_cfm.get_element("nonexistent") is None

    def test_get_elements_by_category(
        self, sample_cfm: CanonicalFunctionalModel
    ) -> None:
        actors = sample_cfm.get_elements_by_category("actors")
        assert len(actors) == 1
        assert "a1" in actors

    def test_get_elements_by_category_unknown(
        self, sample_cfm: CanonicalFunctionalModel
    ) -> None:
        assert sample_cfm.get_elements_by_category("invalid") == {}

    def test_get_elements_by_evidence(
        self, sample_cfm: CanonicalFunctionalModel
    ) -> None:
        result = sample_cfm.get_elements_by_evidence("doc1")
        assert len(result) == 4

    def test_get_elements_by_evidence_no_match(
        self, sample_cfm: CanonicalFunctionalModel
    ) -> None:
        assert sample_cfm.get_elements_by_evidence("nonexistent") == []

    def test_trace_evidence(self, sample_cfm: CanonicalFunctionalModel) -> None:
        ref = sample_cfm.trace_evidence("a1")
        assert ref is not None
        assert ref.document_id == "doc1"
        assert ref.text == "source"

    def test_trace_evidence_missing(self, sample_cfm: CanonicalFunctionalModel) -> None:
        assert sample_cfm.trace_evidence("nonexistent") is None

    def test_get_relationships_for_element(self) -> None:
        ev = EvidenceRef(graph_node_id="n0", document_id="doc1", text="src")
        cfm = CanonicalFunctionalModel(
            run_id="test",
            actors={},
            functional_processes={},
            business_rules={},
            data_groups={},
            relationships=[
                Relationship(id="r1", source_id="a1", target_id="b1", evidence=ev),
                Relationship(id="r2", source_id="b1", target_id="d1", evidence=ev),
            ],
            metadata=BuildMetadata(run_id="test"),
        )
        rels = cfm.get_relationships_for_element("a1")
        assert len(rels) == 1
        assert rels[0].id == "r1"

    def test_immutability(self, sample_cfm: CanonicalFunctionalModel) -> None:
        with pytest.raises((TypeError, AttributeError, ValueError)):
            sample_cfm.actors = {}
