"""Evidence and fingerprint helpers for Story Points calculation."""
from __future__ import annotations

import hashlib

from specmetrics.kernel.cfm.model import FunctionalProcess

from .models import EvidenceRef


def fingerprint(fp: FunctionalProcess) -> str:
    """Compute a stable fingerprint for a functional process."""
    ev = fp.evidence
    doc_id = getattr(ev, "document_id", "")
    section_id = getattr(ev, "section_id", "") or ""
    text = getattr(ev, "text", "")
    raw = f"{doc_id}|{section_id}|{text}|functional_process"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def evidence_ref_from_fp(fp: FunctionalProcess) -> EvidenceRef:
    """Build an evidence reference from a functional process."""
    ev = fp.evidence
    return EvidenceRef(
        graph_node_id=getattr(ev, "graph_node_id", ""),
        document_id=getattr(ev, "document_id", ""),
        section_id=getattr(ev, "section_id", None),
        text=getattr(ev, "text", ""),
    )


def evidence_ref_from_csm_evidence(refs: list) -> EvidenceRef | None:
    """Build an evidence reference from the first CSM evidence reference."""
    if not refs:
        return None
    r = refs[0]
    return EvidenceRef(
        graph_node_id=getattr(r, "graph_node_id", r.id if hasattr(r, "id") else ""),
        document_id=getattr(r, "document_id", ""),
        section_id=getattr(r, "section_id", None),
        text=getattr(r, "text", ""),
    )


def evidence_ref_from_cfm_evidence(ev: object) -> EvidenceRef:
    """Build an evidence reference from CFM evidence."""
    return EvidenceRef(
        graph_node_id=getattr(ev, "graph_node_id", ""),
        document_id=getattr(ev, "document_id", ""),
        section_id=getattr(ev, "section_id", None),
        text=getattr(ev, "text", ""),
    )