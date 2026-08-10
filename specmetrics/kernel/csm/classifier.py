"""Heuristic classifiers for canonical specification model elements."""

from __future__ import annotations

import re

from specmetrics.kernel.evidence_graph import GraphNode

FRAMEWORK_PATTERNS = [
    re.compile(
        r"^(?:OpenSpec|SpecKit|SpecMetrics)\s+(?:Section|Document|Measurement|Feature|Element|Concept):\s*",
        re.IGNORECASE,
    ),
    re.compile(r"^(?:open_spec|speckit|specmetrics)[_.].*", re.IGNORECASE),
]

DECISION_PATTERNS = re.compile(r"(?i)(decided|chosen|selected|agreed|resolved)\b.*")

ASSUMPTION_PATTERNS = re.compile(
    r"(?i)(assume|assumed|presume|taken\s+as\s+true|we\s+believe)\b"
)

CONSTRAINT_PATTERNS = re.compile(
    r"(?i)\b(must|shall|required|limited|cannot|restricted|only)\b"
)

RISK_PATTERNS = re.compile(
    r"(?i)(risk|uncertainty|concern|might|potential\s+issue|if\s+.*\s+when)\b"
)

OPEN_QUESTION_PATTERNS = re.compile(
    r"(?i)(\?|unresolved\b|needs\s+decision\b|TBD\b|open\s+question\b)"
)

ACCEPTANCE_PATTERNS = re.compile(
    r"(?i)\b(given|when|then|verify|validated|acceptance)\b"
)

GLOSSARY_PATTERNS = re.compile(r"(?i)^[A-Z][a-zA-Z]*(?:\s+[a-z][a-zA-Z]*)?\s*[:\-–—]")

SPEC_ACTIVITY_PATTERNS = re.compile(r"(?i)(explore|clarify|refine|review|validate)\b")

CLASSIFIER_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("decision", DECISION_PATTERNS),
    ("assumption", ASSUMPTION_PATTERNS),
    ("constraint", CONSTRAINT_PATTERNS),
    ("risk", RISK_PATTERNS),
    ("open_question", OPEN_QUESTION_PATTERNS),
    ("acceptance_criterion", ACCEPTANCE_PATTERNS),
    ("glossary_term", GLOSSARY_PATTERNS),
    ("specification_activity", SPEC_ACTIVITY_PATTERNS),
]


def classify_node(node: GraphNode) -> str | None:
    """Classify a graph node into a CSM category, or None if unclassified."""
    if node.node_type != "extracted_element":
        return None

    for category_name, pattern in CLASSIFIER_PATTERNS:
        if category_name == "glossary_term":
            if pattern.match(node.text):
                return category_name
        elif pattern.search(node.text):
            return category_name

    return None


def classify_all_categories(node: GraphNode) -> list[str]:
    """Return all categories matched by a node's text."""
    if node.node_type != "extracted_element":
        return []

    matched: list[str] = []
    for category_name, pattern in CLASSIFIER_PATTERNS:
        if category_name == "glossary_term":
            if pattern.match(node.text):
                matched.append(category_name)
        elif pattern.search(node.text):
            matched.append(category_name)

    return matched


def strip_framework_labels(text: str) -> str:
    """Remove framework-specific prefixes from a node text."""
    for pattern in FRAMEWORK_PATTERNS:
        text = pattern.sub("", text)
    return text.strip()
