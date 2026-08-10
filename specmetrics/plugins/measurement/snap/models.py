"""Data models for the SNAP measurement plugin."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator

SemanticMarker = Literal[
    "presentation_interface",
    "formatting_rule",
    "data_operation",
    "data_transform",
    "operational_feature",
    "technical_interface",
    "integration_point",
]

CategoryId = Literal[
    "presentation",
    "data_operations",
    "operational_capabilities",
    "technical_interaction",
]

SEMANTIC_MARKER_TO_CATEGORY: dict[SemanticMarker, CategoryId] = {
    "presentation_interface": "presentation",
    "formatting_rule": "presentation",
    "data_operation": "data_operations",
    "data_transform": "data_operations",
    "operational_feature": "operational_capabilities",
    "technical_interface": "technical_interaction",
    "integration_point": "technical_interaction",
}


class EvidenceRef(BaseModel):
    """Reference to the evidence supporting an assessed item."""

    model_config = {"frozen": True}

    graph_node_id: str
    document_id: str
    section_id: str | None = None
    text: str


class AssessmentWarning(BaseModel):
    """A non-fatal warning raised during SNAP assessment."""

    code: str
    message: str
    cfm_element_id: str | None = None
    details: dict[str, str] | None = None


class AssessmentError(BaseModel):
    """An error raised during SNAP assessment."""

    code: str
    message: str
    cfm_element_id: str | None = None
    recoverable: bool = False


class AssessedItem(BaseModel):
    """A single element assessed for SNAP points."""

    id: str
    name: str
    category_id: CategoryId
    contribution: float
    cfm_element_id: str
    cfm_semantic_marker: SemanticMarker
    evidence_refs: list[EvidenceRef] = []
    rule_applied: str | None = None
    excluded: bool = False

    @model_validator(mode="after")
    def validate_assessed_item(self: Self) -> AssessedItem:
        """Validate that excluded items have zero contribution."""
        if self.excluded and self.contribution != 0:
            raise ValueError("excluded items must have contribution=0")
        return self


class CategoryBreakdown(BaseModel):
    """Item count and total SNAP for a single category."""

    item_count: int
    total_snap: float


class AssessmentSummary(BaseModel):
    """Aggregated summary of a SNAP assessment run."""

    total_item_count: int
    total_active_count: int
    total_snap: float
    by_category: dict[CategoryId, CategoryBreakdown] = {}


class CategoryAssessment(BaseModel):
    """Assessed items grouped under a single SNAP category."""

    category_id: CategoryId
    category_name: str
    category_version: str
    items: list[AssessedItem] = []
    total_contribution: float = 0.0

    @model_validator(mode="after")
    def validate_category(self: Self) -> CategoryAssessment:
        """Validate that a category contains at least one item."""
        if not self.items:
            raise ValueError("category must have non-empty items list")
        return self


class AssessmentExplanation(BaseModel):
    """Explanation of how a single item was assessed."""

    item_id: str
    cfm_element_id: str
    cfm_element_name: str
    identification_reason: str
    contribution_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class SNAPMeasurementResult(BaseModel):
    """Full result of a SNAP assessment run."""

    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: str | None = None
    categories: list[CategoryAssessment] = []
    assessed_items: list[AssessedItem] = []
    summary: AssessmentSummary
    explanations: list[AssessmentExplanation] = []
    warnings: list[AssessmentWarning] = []
    errors: list[AssessmentError] = []
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @model_validator(mode="after")
    def validate_consistency(self: Self) -> SNAPMeasurementResult:
        """Validate internal consistency of the assessment result."""
        if self.errors and self.summary.total_snap is not None:
            raise ValueError("Cannot have total_snap when errors are present")
        ids = [a.id for a in self.assessed_items]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate assessed_item ids")
        if self.summary.total_item_count != len(self.assessed_items):
            raise ValueError("summary.total_item_count must match len(assessed_items)")
        for cat in self.categories:
            if not cat.items:
                raise ValueError("every category must have non-empty items list")
        return self


class CategoryDefinition(BaseModel):
    """Definition of a SNAP assessment category."""

    id: CategoryId
    name: str
    description: str
    version: str
    default_contribution: float

    @model_validator(mode="after")
    def validate_version(self: Self) -> CategoryDefinition:
        """Validate that the category version is a valid SemVer string."""
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        if not re.match(pattern, self.version):
            raise ValueError(
                f"Invalid SemVer version for category '{self.id}': '{self.version}'"
            )
        return self


DEFAULT_CATEGORIES: list[CategoryDefinition] = [
    CategoryDefinition(
        id="presentation",
        name="Presentation",
        description="Interface presentation and formatting characteristics",
        version="1.0.0",
        default_contribution=4.0,
    ),
    CategoryDefinition(
        id="data_operations",
        name="Data Operations",
        description="Data manipulation and transformation complexity",
        version="1.0.0",
        default_contribution=4.0,
    ),
    CategoryDefinition(
        id="operational_capabilities",
        name="Operational Capabilities",
        description="Installation, configuration, and operational features",
        version="1.0.0",
        default_contribution=7.0,
    ),
    CategoryDefinition(
        id="technical_interaction",
        name="Technical Interaction",
        description="Technical interface and integration complexity",
        version="1.0.0",
        default_contribution=6.0,
    ),
]


class RulePack(BaseModel):
    """Rule pack that tunes SNAP assessment behavior."""

    id: str
    methodology: str = "SNAP"
    contribution_overrides: dict[str, float] | None = None
    excluded_categories: list[str] = []
    item_exclusions: dict[str, list[str]] | None = None
    inclusion_policies: list[dict[str, str]] | None = None
