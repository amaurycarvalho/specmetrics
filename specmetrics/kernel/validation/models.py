"""Data models for validation rules and reports."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

from pydantic import BaseModel

RuleCategory = Literal["STRUCTURAL", "CONSTITUTIONAL", "FORMAT"]
RuleSeverity = Literal["ERROR", "WARNING"]


class SpecificationDocument(BaseModel):
    """A specification document to validate."""

    path: Path
    content: str
    format: str = "spec-markdown"
    size_bytes: int = 0
    line_count: int = 0


class ValidationRule(BaseModel):
    """A named validation rule with a category and severity."""

    name: str
    description: str
    category: RuleCategory
    severity: RuleSeverity = "ERROR"
    enabled: bool = True

    def validate(self: Self, document: SpecificationDocument) -> ValidationResult:
        """Validate the rule against a document, returning a ValidationResult."""
        raise NotImplementedError


class EvidenceRef(BaseModel):
    """A reference to evidence for a validation result."""

    section: str | None = None
    line: int | None = None
    detail: str = ""


class ValidationResult(BaseModel):
    """Outcome of running a single validation rule."""

    rule_name: str
    passed: bool
    message: str = ""
    evidence: list[EvidenceRef] = []
    severity: RuleSeverity = "ERROR"


class ReportSummary(BaseModel):
    """Summary counts for a validation report."""

    total_rules: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    duration_ms: int = 0


class ValidationReport(BaseModel):
    """Report of validation results for a single document."""

    document_path: Path
    overall_passed: bool = False
    results: list[ValidationResult] = []
    summary: ReportSummary = ReportSummary()


class BatchReport(BaseModel):
    """Report of validation results across multiple documents."""

    reports: list[ValidationReport] = []
    total_documents: int = 0
    passed_documents: int = 0
    failed_documents: int = 0
    duration_ms: int = 0
