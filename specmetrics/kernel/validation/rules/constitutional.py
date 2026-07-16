from __future__ import annotations

import re

from specmetrics.kernel.validation.models import (
    EvidenceRef,
    SpecificationDocument,
    ValidationResult,
    ValidationRule,
)

CONSTITUTION_PRINCIPLES = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV",
]

PRINCIPLE_TITLES = {
    "I": "Specification First",
    "II": "Specification as a Measurable Asset",
    "III": "Semantic Before Structural",
    "IV": "LLM-Assisted, Deterministic Results",
    "V": "Evidence First",
    "VI": "Explainability by Design",
    "VII": "Canonical Representation",
    "VIII": "Plugin-Oriented Architecture",
    "IX": "Rule Externalization",
    "X": "AI-Friendly by Design",
    "XI": "Observability as a Native Capability",
    "XII": "Open by Default",
    "XIII": "Evolution Without Disruption",
    "XIV": "Layer Independence",
}


def constitution_engaged(document: SpecificationDocument) -> ValidationResult:
    content = document.content

    pattern = re.compile(
        r"(?:\*{0,2})Engaged\s*Principles(?:\*{0,2})\s*[:：]\s*(.+)",
        re.IGNORECASE,
    )
    match = pattern.search(content)
    if not match:
        return ValidationResult(
            rule_name="constitution-engaged",
            passed=False,
            message="No 'Engaged Principles' section found in specification",
            evidence=[EvidenceRef(detail="Missing Engaged Principles declaration")],
        )

    principles_text = match.group(1)
    found_principles = re.findall(r"\b(?:X{0,3}I{0,3}|IV|VI{0,3})\b", principles_text)
    tokens = [p.strip("() ") for p in re.split(r"[,;\s]+", principles_text) if p.strip("() ")]
    found_principles = [
        p for p in tokens
        if re.match(r"^(I{1,3}|IV|V|VI{0,3}|X{0,3}I{0,3}|XI{1,2}|XII|XIII|XIV)$", p)
    ]

    if not found_principles:
        return ValidationResult(
            rule_name="constitution-engaged",
            passed=False,
            message="No valid constitution principles found in Engaged Principles declaration",
            evidence=[EvidenceRef(detail="Expected Roman numeral principles (I-XIV)")],
        )

    unknown = [p for p in found_principles if p not in CONSTITUTION_PRINCIPLES]
    if unknown:
        return ValidationResult(
            rule_name="constitution-engaged",
            passed=False,
            message=f"Unknown constitution principles referenced: {', '.join(unknown)}",
            evidence=[EvidenceRef(detail=f"Unrecognized principle: {p}") for p in unknown],
        )

    return ValidationResult(
        rule_name="constitution-engaged",
        passed=True,
        message=f"Constitution principles engaged: {', '.join(found_principles)}",
        evidence=[EvidenceRef(detail=f"Found {len(found_principles)} engaged principles")],
    )


def constitution_compliance_notes(document: SpecificationDocument) -> ValidationResult:
    content = document.content

    if "Compliance Note" not in content and "compliance" not in content.lower():
        return ValidationResult(
            rule_name="constitution-compliance-notes",
            passed=False,
            message="No compliance notes found for engaged constitution principles",
            evidence=[EvidenceRef(detail="Missing Compliance Notes section")],
        )

    engagement_section = _find_section(content, "Constitution Check")
    if not engagement_section:
        return ValidationResult(
            rule_name="constitution-compliance-notes",
            passed=False,
            message="Constitution Check section not found — compliance notes cannot be verified",
            evidence=[EvidenceRef(detail="Missing Constitution Check section")],
        )

    if "Engaged Principles" in engagement_section and "Compliance Note" not in engagement_section:
        has_principles_notes = any(
            principle in engagement_section for principle in CONSTITUTION_PRINCIPLES
        )
        if has_principles_notes and (
            "compliance" in engagement_section.lower() or "satisfied" in engagement_section.lower()
        ):
            return ValidationResult(
                rule_name="constitution-compliance-notes",
                passed=True,
                message="Constitution compliance notes are present",
                evidence=[EvidenceRef(detail="Compliance descriptions found for engaged principles")],
            )

    return ValidationResult(
        rule_name="constitution-compliance-notes",
        passed=True,
        message="Constitution compliance documentation found",
    )


def _find_section(content: str, section_name: str) -> str | None:
    lines = content.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## ") and section_name in stripped:
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## "):
                break
            section_lines.append(line)
    return "\n".join(section_lines) if section_lines else None


BUILTIN_CONSTITUTIONAL_RULES: list[ValidationRule] = [
    ValidationRule(
        name="constitution-engaged",
        description="Engaged principles are listed and addressed",
        category="CONSTITUTIONAL",
    ),
    ValidationRule(
        name="constitution-compliance-notes",
        description="Compliance notes explain how each principle is satisfied",
        category="CONSTITUTIONAL",
    ),
]

CONSTITUTIONAL_RULE_FN = {
    "constitution-engaged": constitution_engaged,
    "constitution-compliance-notes": constitution_compliance_notes,
}
