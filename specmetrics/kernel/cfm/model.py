from __future__ import annotations

from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel

from .metadata import BuildMetadata


ActorType = Literal["person", "system", "role"]
RuleType = Literal["constraint", "condition", "policy", "derivation"]
DataType = Literal["internal", "external", "shared"]
RelationshipType = Literal[
    "triggers", "composed_of", "governs", "uses", "communicates_with"
]


class EvidenceRef(BaseModel):
    graph_node_id: str
    document_id: str
    section_id: Optional[str] = None
    text: str


class Actor(BaseModel):
    id: str
    name: str
    actor_type: ActorType = "role"
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class Operation(BaseModel):
    id: str
    name: str
    description: str = ""
    parent_process_id: str
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class FunctionalProcess(BaseModel):
    id: str
    name: str
    description: str = ""
    actor_ids: list[str] = []
    operation_ids: list[str] = []
    data_group_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class BusinessRule(BaseModel):
    id: str
    name: str
    description: str = ""
    rule_type: RuleType = "constraint"
    related_process_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class DataGroup(BaseModel):
    id: str
    name: str
    description: str = ""
    data_type: DataType = "internal"
    related_process_ids: list[str] = []
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class Relationship(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType = "references"
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class UnclassifiedElement(BaseModel):
    id: str
    original_type: str
    content: str
    evidence: EvidenceRef
    metadata: dict[str, str] = {}


class CanonicalFunctionalModel(BaseModel):
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

    def get_element(self, element_id: str) -> Any | None:
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

    def get_elements_by_category(self, category: str) -> dict[str, Any]:
        mapping = {
            "actors": self.actors,
            "functional_processes": self.functional_processes,
            "business_rules": self.business_rules,
            "data_groups": self.data_groups,
            "operations": self.operations,
            "unclassified": self.unclassified,
        }
        return mapping.get(category, {})

    def get_elements_by_evidence(self, document_id: str) -> list[Any]:
        result: list[Any] = []
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

    def trace_evidence(self, element_id: str) -> EvidenceRef | None:
        element = self.get_element(element_id)
        if element is None:
            return None
        return element.evidence

    def get_relationships_for_element(self, element_id: str) -> list[Relationship]:
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

    def consume(self, cfm: CanonicalFunctionalModel) -> Any: ...
