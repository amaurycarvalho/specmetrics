from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Literal, Optional

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
    model_config = {"frozen": True}

    graph_node_id: str
    document_id: str
    section_id: Optional[str] = None
    text: str


class AssessmentWarning(BaseModel):
    code: str
    message: str
    cfm_element_id: Optional[str] = None
    details: Optional[dict[str, str]] = None


class AssessmentError(BaseModel):
    code: str
    message: str
    cfm_element_id: Optional[str] = None
    recoverable: bool = False


class AssessedItem(BaseModel):
    id: str
    name: str
    category_id: CategoryId
    contribution: float
    cfm_element_id: str
    cfm_semantic_marker: SemanticMarker
    evidence_refs: list[EvidenceRef] = []
    rule_applied: Optional[str] = None
    excluded: bool = False

    @model_validator(mode="after")
    def validate_assessed_item(self) -> AssessedItem:
        if self.excluded and self.contribution != 0:
            raise ValueError("excluded items must have contribution=0")
        return self


class CategoryBreakdown(BaseModel):
    item_count: int
    total_snap: float


class AssessmentSummary(BaseModel):
    total_item_count: int
    total_active_count: int
    total_snap: float
    by_category: dict[CategoryId, CategoryBreakdown] = {}


class CategoryAssessment(BaseModel):
    category_id: CategoryId
    category_name: str
    category_version: str
    items: list[AssessedItem] = []
    total_contribution: float = 0.0

    @model_validator(mode="after")
    def validate_category(self) -> CategoryAssessment:
        if not self.items:
            raise ValueError("category must have non-empty items list")
        return self


class AssessmentExplanation(BaseModel):
    item_id: str
    cfm_element_id: str
    cfm_element_name: str
    identification_reason: str
    contribution_reason: str
    rule_exceptions: list[str] = []
    evidence_chain: list[str] = []


class SNAPMeasurementResult(BaseModel):
    model_config = {"frozen": True}

    run_id: str
    cfm_run_id: str
    rule_pack_id: Optional[str] = None
    categories: list[CategoryAssessment] = []
    assessed_items: list[AssessedItem] = []
    summary: AssessmentSummary
    explanations: list[AssessmentExplanation] = []
    warnings: list[AssessmentWarning] = []
    errors: list[AssessmentError] = []
    assessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def validate_consistency(self) -> SNAPMeasurementResult:
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
    id: CategoryId
    name: str
    description: str
    version: str
    default_contribution: float

    @model_validator(mode="after")
    def validate_version(self) -> CategoryDefinition:
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
    id: str
    methodology: str = "SNAP"
    contribution_overrides: Optional[dict[str, float]] = None
    excluded_categories: list[str] = []
    item_exclusions: Optional[dict[str, list[str]]] = None
    inclusion_policies: Optional[list[dict[str, str]]] = None
