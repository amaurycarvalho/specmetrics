"""Evidence and content extraction helpers for Cognitive Points."""
from __future__ import annotations

from .models import EvidenceRef


def csm_evidence(evidence_refs: list) -> EvidenceRef | None:
    """Build an EvidenceRef from the first CSM evidence reference."""
    if not evidence_refs:
        return None
    ref = evidence_refs[0]
    return EvidenceRef(
        graph_node_id=getattr(ref, "graph_node_id", ""),
        document_id=getattr(ref, "document_id", ""),
        section_id=getattr(ref, "section_id", None),
        text=getattr(ref, "text", ""),
    )


def cfm_evidence(evidence: object) -> EvidenceRef | None:
    """Build an EvidenceRef from CFM evidence."""
    if evidence is None:
        return None
    return EvidenceRef(
        graph_node_id=getattr(evidence, "graph_node_id", ""),
        document_id=getattr(evidence, "document_id", ""),
        section_id=getattr(evidence, "section_id", None),
        text=getattr(evidence, "text", ""),
    )


def extract_content_text_csm(elem: object) -> str:
    """Extract a content string from a CSM element."""
    name = getattr(elem, "name", None) or ""
    description = getattr(elem, "description", None) or ""
    return (name + " " + description).strip()


def extract_content_text_cfm(elem: object, collection_name: str) -> str:
    """Extract a content string from a CFM element."""
    if collection_name == "relationships":
        name = getattr(elem, "name", None) or ""
        return name.strip()
    name = getattr(elem, "name", None) or ""
    description = getattr(elem, "description", None) or ""
    return (name + " " + description).strip()