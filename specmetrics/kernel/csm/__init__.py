"""Canonical Specification Model (CSM) package."""

from .builder import CsmBuilderStage, build
from .classifier import classify_all_categories, classify_node, strip_framework_labels
from .metadata import BuildMetadata, ClassificationConflict
from .model import (
    AcceptanceCriterion,
    Assumption,
    CanonicalSpecificationModel,
    Constraint,
    CsmConsumer,
    CsmElement,
    Decision,
    EvidenceRef,
    GlossaryTerm,
    OpenQuestion,
    Reference,
    Risk,
    SpecificationActivity,
)

__all__ = [
    "AcceptanceCriterion",
    "Assumption",
    "BuildMetadata",
    "CanonicalSpecificationModel",
    "ClassificationConflict",
    "Constraint",
    "CsmBuilderStage",
    "CsmConsumer",
    "CsmElement",
    "Decision",
    "EvidenceRef",
    "GlossaryTerm",
    "OpenQuestion",
    "Reference",
    "Risk",
    "SpecificationActivity",
    "build",
    "classify_all_categories",
    "classify_node",
    "strip_framework_labels",
]
