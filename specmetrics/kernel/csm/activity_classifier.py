"""Classify specification activities by exploration, review, and validation type."""

from __future__ import annotations

import re

from specmetrics.kernel.evidence_graph import EvidenceGraph, GraphNode

EXPLORATION_PATTERNS = re.compile(
    r"(?i)(discover|research|investigat|explor|alternatives?\s+considered)"
)

CLARIFICATION_PATTERNS = re.compile(
    r"(?i)(clarif|ambigu|elaborat|answer|question|resolution\s+of)"
)

REFINEMENT_PATTERNS = re.compile(
    r"(?i)(refin|restructur|rewrit|improv(e|ing)\s+clarify|rephrase)"
)

REVIEW_PATTERNS = re.compile(r"(?i)(review|evaluat|inspect|checklist|audit)")

VALIDATION_PATTERNS = re.compile(
    r"(?i)(validat|confirm|sign.?off|stakeholder\s+accept|approv)"
)


def classify_activity_type(text: str) -> str | None:
    """Classify an activity type from text, or None if unknown."""
    if EXPLORATION_PATTERNS.search(text):
        return "exploration"
    if CLARIFICATION_PATTERNS.search(text):
        return "clarification"
    if REFINEMENT_PATTERNS.search(text):
        return "refinement"
    if REVIEW_PATTERNS.search(text):
        return "review"
    if VALIDATION_PATTERNS.search(text):
        return "validation"
    return None


def classify_activity_type_with_context(
    node: GraphNode, graph: EvidenceGraph
) -> str | None:
    """Classify an activity type using text and graph context."""
    activity_type = classify_activity_type(node.text)
    if activity_type is not None:
        return activity_type

    derived_count = 0
    for edge in graph.edges:
        if edge.source == node.id and edge.edge_type == "derived_from":
            derived_count += 1

    if derived_count >= 2:
        return "refinement"
    if derived_count >= 1:
        return "clarification"

    return None
