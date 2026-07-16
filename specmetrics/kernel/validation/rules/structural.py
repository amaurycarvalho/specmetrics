from __future__ import annotations

from specmetrics.kernel.validation.models import (
    EvidenceRef,
    SpecificationDocument,
    ValidationResult,
    ValidationRule,
)

MANDATORY_SECTIONS = [
    "User Scenarios & Testing",
    "Constitution Check",
    "Requirements",
    "Success Criteria",
    "Assumptions",
]


def file_readable(document: SpecificationDocument) -> ValidationResult:
    evidence: list[EvidenceRef] = []
    if not document.path.exists():
        evidence.append(EvidenceRef(detail=f"File not found: {document.path}"))
        return ValidationResult(
            rule_name="file-readable",
            passed=False,
            message=f"File does not exist: {document.path}",
            evidence=evidence,
        )
    if not document.path.is_file():
        evidence.append(EvidenceRef(detail=f"Path is not a file: {document.path}"))
        return ValidationResult(
            rule_name="file-readable",
            passed=False,
            message=f"Path is not a file: {document.path}",
            evidence=evidence,
        )
    return ValidationResult(
        rule_name="file-readable",
        passed=True,
        message=f"File is readable: {document.path}",
        evidence=[EvidenceRef(detail=f"File exists at {document.path}")],
    )


def file_not_empty(document: SpecificationDocument) -> ValidationResult:
    if not document.content.strip():
        return ValidationResult(
            rule_name="file-not-empty",
            passed=False,
            message="Specification document is empty",
            evidence=[EvidenceRef(detail="Document content is blank or whitespace-only")],
        )
    return ValidationResult(
        rule_name="file-not-empty",
        passed=True,
        message="Document has content",
        evidence=[EvidenceRef(detail=f"Document contains {document.line_count} lines")],
    )


def parseable_markdown(document: SpecificationDocument) -> ValidationResult:
    try:
        from markdown_it import MarkdownIt

        parser = MarkdownIt()
        parser.parse(document.content)
        return ValidationResult(
            rule_name="parseable-markdown",
            passed=True,
            message="Document is valid markdown",
        )
    except Exception as exc:
        return ValidationResult(
            rule_name="parseable-markdown",
            passed=False,
            message=f"Document is not valid markdown: {exc}",
            evidence=[EvidenceRef(detail=str(exc))],
        )


def _find_section_headings(content: str) -> list[str]:
    headings: list[str] = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading_text = stripped.removeprefix("## ").strip()
            if heading_text:
                headings.append(heading_text)
    return headings


def mandatory_sections_exist(document: SpecificationDocument) -> ValidationResult:
    headings = _find_section_headings(document.content)
    missing = [s for s in MANDATORY_SECTIONS if s not in headings]
    if missing:
        evidence = [
            EvidenceRef(detail=f"Missing mandatory section: {s}") for s in missing
        ]
        return ValidationResult(
            rule_name="mandatory-sections-exist",
            passed=False,
            message=f"Missing mandatory sections: {', '.join(missing)}",
            evidence=evidence,
        )
    return ValidationResult(
        rule_name="mandatory-sections-exist",
        passed=True,
        message="All mandatory sections are present",
        evidence=[EvidenceRef(detail=f"Found {len(MANDATORY_SECTIONS)} mandatory sections")],
    )


def no_unknown_sections(document: SpecificationDocument) -> ValidationResult:
    headings = _find_section_headings(document.content)
    unknown = [h for h in headings if h not in MANDATORY_SECTIONS]
    if unknown:
        return ValidationResult(
            rule_name="no-unknown-sections",
            passed=False,
            message=f"Unrecognized sections: {', '.join(unknown)}",
            evidence=[EvidenceRef(detail=f"Unknown section: {s}") for s in unknown],
            severity="WARNING",
        )
    return ValidationResult(
        rule_name="no-unknown-sections",
        passed=True,
        message="All sections are recognized",
    )


BUILTIN_STRUCTURAL_RULES: list[ValidationRule] = [
    ValidationRule(
        name="file-readable",
        description="Document file exists, is readable, and has valid encoding",
        category="FORMAT",
    ),
    ValidationRule(
        name="file-not-empty",
        description="Document content is not empty",
        category="FORMAT",
    ),
    ValidationRule(
        name="parseable-markdown",
        description="Document can be parsed as markdown",
        category="FORMAT",
    ),
    ValidationRule(
        name="mandatory-sections-exist",
        description="All required template sections are present",
        category="STRUCTURAL",
    ),
    ValidationRule(
        name="no-unknown-sections",
        description="No unrecognized section headings",
        category="STRUCTURAL",
        severity="WARNING",
    ),
]

STRUCTURAL_RULE_FN = {
    "file-readable": file_readable,
    "file-not-empty": file_not_empty,
    "parseable-markdown": parseable_markdown,
    "mandatory-sections-exist": mandatory_sections_exist,
    "no-unknown-sections": no_unknown_sections,
}
