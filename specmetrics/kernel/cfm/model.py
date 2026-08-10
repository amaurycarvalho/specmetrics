"""Canonical Functional Model (CFM) data structures.

Defines the pydantic models that represent a canonical functional model derived
from extracted evidence, along with the consumer protocol used by downstream
measurement engine plugins.
"""

from __future__ import annotations

from typing import Literal, Protocol, Self

from pydantic import BaseModel

from .metadata import BuildMetadata

ActorType = Literal["person", "system", "role"]
RuleType = Literal["constraint", "condition", "policy", "derivation"]
DataType = Literal["internal", "external", "shared"]
RelationshipType = Literal[
    "triggers", "composed_of", "governs", "uses", "communicates_with"
]


class EvidenceRef(BaseModel):
    """Reference to the evidence supporting a canonical functional model element."""

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class Actor(BaseModel):
    """An actor that participates in functional processes."""

    id: str
    name: str
    actor_type: ActorType = "role"
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class Operation(BaseModel):
    """An operation performed within a functional process."""

    id: str
    name: str
    description: str = ""
    parent_process_id: str
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class FunctionalProcess(BaseModel):
    """A functional process grouping actors, operations, and data groups."""

    id: str
    name: str
    description: str = ""
    actor_ids: list[str] = []
    operation_ids: list[str] = []
    data_group_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class BusinessRule(BaseModel):
    """A business rule governing functional behavior."""

    id: str
    name: str
    description: str = ""
    rule_type: RuleType = "constraint"
    related_process_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class DataGroup(BaseModel):
    """A group of related data entities."""

    id: str
    name: str
    description: str = ""
    data_type: DataType = "internal"
    related_process_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class Relationship(BaseModel):
    """A relationship between two functional model elements."""

    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType = "references"
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class UnclassifiedElement(BaseModel):
    """An element that could not be classified into a known category."""

    id: str
    original_type: str
    content: str
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class CanonicalFunctionalModel(BaseModel):
    """The canonical functional model holding all extracted elements."""

    model_config = {"frozen": True}

    run_id: str
    actors: dict[str, Actor] = {}
    functional_processes: dict[str, FunctionalProcess] = {}
    business_rules: dict[str, BusinessRule] = {}
    data_groups: dict[str, DataGroup] = {}
    relationships: list[Relationship] = []
    operations: dict[str, Operation] = {}
    unclassified: dict[str, UnclassifiedElement] = {}
    metadata: BuildMetadata
    evidence_graph_ref: str = ""

    def get_element(self: Self, element_id: str) -> object | None:
        """Return the element with the given id across all collections."""
        for collection in (
            self.actors,
            self.functional_processes,
            self.business_rules,
            self.data_groups,
            self.operations,
            self.unclassified,
        ):
            if element_id in collection:
                return collection[element_id]
        for rel in self.relationships:
            if rel.id == element_id:
                return rel
        return None

    def get_elements_by_category(self: Self, category: str) -> dict[str, object]:
        """Return the collection of elements for a given category."""
        mapping = {
            "actors": self.actors,
            "functional_processes": self.functional_processes,
            "business_rules": self.business_rules,
            "data_groups": self.data_groups,
            "operations": self.operations,
            "unclassified": self.unclassified,
        }
        return mapping.get(category, {})

    def get_elements_by_evidence(self: Self, document_id: str) -> list[object]:
        """Return all elements referencing evidence from the given document."""
        result: list[object] = []
        for collection in (
            self.actors,
            self.functional_processes,
            self.business_rules,
            self.data_groups,
            self.operations,
            self.unclassified,
        ):
            for element in collection.values():
                if element.evidence.document_id == document_id:
                    result.append(element)
        for rel in self.relationships:
            if rel.evidence.document_id == document_id:
                result.append(rel)
        return result

    def trace_evidence(self: Self, element_id: str) -> EvidenceRef | None:
        """Return the evidence reference for the given element id."""
        element = self.get_element(element_id)
        if element is None:
            return None
        return element.evidence

    def get_relationships_for_element(self: Self, element_id: str) -> list[Relationship]:
        """Return the relationships connected to the given element id."""
        return [
            rel
            for rel in self.relationships
            if rel.source_id == element_id or rel.target_id == element_id
        ]


class CFMConsumer(Protocol):
    """Stable public interface for downstream measurement engine plugins.

    Any consumer that implements this protocol can consume a
    CanonicalFunctionalModel without framework-specific dependencies.
    """

    def consume(self: Self, cfm: CanonicalFunctionalModel) -> object:
        """Consume the canonical functional model."""
        ...
