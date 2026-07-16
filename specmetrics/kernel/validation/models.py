from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel

RuleCategory = Literal["STRUCTURAL", "CONSTITUTIONAL", "FORMAT"]
RuleSeverity = Literal["ERROR", "WARNING"]


class SpecificationDocument(BaseModel):
    path: Path
    content: str
    format: str = "spec-markdown"
    size_bytes: int = 0
    line_count: int = 0


class ValidationRule(BaseModel):
    name: str
    description: str
    category: RuleCategory
    severity: RuleSeverity = "ERROR"
    enabled: bool = True

    def validate(self, document: SpecificationDocument) -> ValidationResult:
        raise NotImplementedError


class EvidenceRef(BaseModel):
    section: str | None = None
    line: int | None = None
    detail: str = ""


class ValidationResult(BaseModel):
    rule_name: str
    passed: bool
    message: str = ""
    evidence: list[EvidenceRef] = []
    severity: RuleSeverity = "ERROR"


class ReportSummary(BaseModel):
    total_rules: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    duration_ms: int = 0


class ValidationReport(BaseModel):
    document_path: Path
    overall_passed: bool = False
    results: list[ValidationResult] = []
    summary: ReportSummary = ReportSummary()


class BatchReport(BaseModel):
    reports: list[ValidationReport] = []
    total_documents: int = 0
    passed_documents: int = 0
    failed_documents: int = 0
    duration_ms: int = 0
