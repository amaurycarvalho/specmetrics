from __future__ import annotations

from typing import Any

from .evidence_graph import GraphBackend


class GraphQueryEngine:
    """Query interface for the evidence graph.

    Provides read-only operations for querying nodes by document,
    semantic type, evidence text, provenance chains, and references.
    """

    def __init__(self, backend: GraphBackend) -> None:
        self._backend = backend

    def get_node(self, node_id: str) -> dict | None:
        return self._backend.get_node(node_id)

    def query_by_document(self, document_id: str) -> list[dict]:
        return self._backend.query_nodes({"document_id": document_id})

    def query_by_type(self, semantic_type: str) -> list[dict]:
        return self._backend.query_nodes({"semantic_type": semantic_type})

    def query_by_evidence(self, text_pattern: str) -> list[dict]:
        all_nodes = self._backend.query_nodes({})
        return [n for n in all_nodes if text_pattern.lower() in n.get("text", "").lower()]

    def traverse_provenance(self, node_id: str, max_depth: int = 10) -> list[list[dict]]:
        return self._backend.traverse(node_id, direction="forward", max_depth=max_depth)

    def find_references(self, node_id: str) -> dict[str, list[dict]]:
        node = self._backend.get_node(node_id)
        if node is None:
            return {"incoming": [], "outgoing": []}
        data = self._backend.to_serializable()
        incoming = []
        outgoing = []
        for edge in data.get("edges", []):
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if tgt == node_id:
                src_node = self._backend.get_node(src)
                if src_node:
                    incoming.append(src_node)
            if src == node_id:
                tgt_node = self._backend.get_node(tgt)
                if tgt_node:
                    outgoing.append(tgt_node)
        return {"incoming": incoming, "outgoing": outgoing}
