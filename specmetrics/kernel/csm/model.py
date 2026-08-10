"""Canonical Specification Model (CSM) data structures.

Defines the pydantic models that represent a canonical specification derived
from extracted evidence, along with the consumer protocol used by downstream
measurement engine plugins.
"""

from __future__ import annotations

import uuid
from typing import Literal, Protocol, Self, runtime_checkable

from pydantic import BaseModel, field_validator

from .metadata import BuildMetadata


class EvidenceRef(BaseModel):
    """Reference to the evidence supporting a canonical model element."""

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class CsmElement(BaseModel):
    """Base class for canonical specification elements."""

    id: str
    description: str
    evidence_references: list[EvidenceRef]
    status: Literal["active", "superseded"] = "active"

    @field_validator("id")
    @classmethod
    def _validate_uuid_v4(cls: type[Self], v: str) -> str:
        val = uuid.UUID(v)
        if val.version != 4:
            raise ValueError(f"id must be a UUID v4 string, got version {val.version}")
        return v

    @field_validator("description")
    @classmethod
    def _validate_non_empty(cls: type[Self], v: str) -> str:
        if not v or not v.strip():
            raise ValueError("description must not be empty")
        return v


class SpecificationActivity(CsmElement):
    """A specification activity element."""

    activity_type: Literal[
        "exploration", "clarification", "refinement", "review", "validation"
    ]
    activity_status: Literal["open", "in_progress", "completed", "superseded"] = (
        "completed"
    )
    linked_decisions: list[str] = []
    linked_questions: list[str] = []
    linked_assumptions: list[str] = []
    linked_constraints: list[str] = []
    linked_risks: list[str] = []
    linked_acceptance_criteria: list[str] = []


class Decision(CsmElement):
    """A decision element."""

    rationale: str = ""
    alternatives: list[str] = []
    timestamp: str = ""


class Assumption(CsmElement):
    """An assumption element."""

    validated_date: str | None = None


class Constraint(CsmElement):
    """A constraint element."""

    constraint_type: Literal["regulatory", "technical", "organizational"]
    source: str = ""


class Risk(CsmElement):
    """A risk element."""

    probability: str = ""
    impact: str = ""
    mitigation: str = ""


class OpenQuestion(CsmElement):
    """An open question element."""

    resolved: bool = False
    resolution: str = ""


class AcceptanceCriterion(CsmElement):
    """An acceptance criterion element."""

    verification_method: Literal["test", "review", "inspection"] = "test"


class GlossaryTerm(CsmElement):
    """A glossary term element."""

    aliases: list[str] = []


class Reference(CsmElement):
    """A reference element."""

    original_label: str = ""


class CanonicalSpecificationModel(BaseModel):
    """The canonical specification model holding all extracted elements."""

    model_config = {"frozen": True}

    run_id: str
    specification_activities: dict[str, SpecificationActivity] = {}
    decisions: dict[str, Decision] = {}
    assumptions: dict[str, Assumption] = {}
    constraints: dict[str, Constraint] = {}
    risks: dict[str, Risk] = {}
    open_questions: dict[str, OpenQuestion] = {}
    acceptance_criteria: dict[str, AcceptanceCriterion] = {}
    glossary_terms: dict[str, GlossaryTerm] = {}
    references: dict[str, Reference] = {}
    metadata: BuildMetadata
    evidence_graph_ref: str = ""

    def get_element(self: Self, element_id: str) -> CsmElement | None:
        """Return the element with the given id across all collections."""
        for collection in (
            self.specification_activities,
            self.decisions,
            self.assumptions,
            self.constraints,
            self.risks,
            self.open_questions,
            self.acceptance_criteria,
            self.glossary_terms,
            self.references,
        ):
            if element_id in collection:
                return collection[element_id]
        return None

    def get_elements(self: Self, category: str) -> dict[str, CsmElement]:
        """Return the collection of elements for a given category."""
        mapping: dict[str, dict[str, CsmElement]] = {
            "specification_activities": self.specification_activities,
            "decisions": self.decisions,
            "assumptions": self.assumptions,
            "constraints": self.constraints,
            "risks": self.risks,
            "open_questions": self.open_questions,
            "acceptance_criteria": self.acceptance_criteria,
            "glossary_terms": self.glossary_terms,
            "references": self.references,
        }
        return mapping.get(category, {})

    def get_elements_by_evidence(self: Self, document_id: str) -> list[CsmElement]:
        """Return all elements referencing evidence from the given document."""
        result: list[CsmElement] = []
        for collection in (
            self.specification_activities,
            self.decisions,
            self.assumptions,
            self.constraints,
            self.risks,
            self.open_questions,
            self.acceptance_criteria,
            self.glossary_terms,
            self.references,
        ):
            for element in collection.values():
                for ref in element.evidence_references:
                    if ref.document_id == document_id:
                        result.append(element)
                        break
        return result

    def trace_evidence(self: Self, element_id: str) -> list[EvidenceRef] | None:
        """Return the evidence references for the given element id."""
        element = self.get_element(element_id)
        if element is None:
            return None
        return element.evidence_references


@runtime_checkable
class CsmConsumer(Protocol):
    """Protocol for consumers of a canonical specification model."""

    def consume(self: Self, csm: CanonicalSpecificationModel) -> object:
        """Consume the canonical specification model."""
        ...
