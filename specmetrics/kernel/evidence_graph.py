from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional, Protocol

from pydantic import BaseModel, Field


class EvidenceGraphError(Exception):
    """Base exception for evidence graph operations."""


class NodeNotFoundError(EvidenceGraphError):
    """Raised when a referenced node ID does not exist in the graph."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node not found: {node_id}")
        self.node_id = node_id


class NodeAlreadyExistsError(EvidenceGraphError):
    """Raised when adding a node with an ID that already exists."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"Node already exists: {node_id}")
        self.node_id = node_id


class EdgeAlreadyExistsError(EvidenceGraphError):
    """Raised when adding a duplicate edge."""

    def __init__(self, source: str, target: str) -> None:
        super().__init__(f"Edge already exists: {source} -> {target}")
        self.source = source
        self.target = target


class SelfLoopError(EvidenceGraphError):
    """Raised when adding an edge where source equals target."""

    def __init__(self, node_id: str) -> None:
        super().__init__(f"Self-loop not allowed: {node_id}")
        self.node_id = node_id


class InvalidGraphDataError(EvidenceGraphError):
    """Raised when graph data is invalid or corrupted."""


class GraphNode(BaseModel):
    id: str
    node_type: Literal["extracted_element", "evidence"]
    semantic_type: Optional[Literal["fact", "entity", "relationship", "operation"]] = None
    document_id: str
    section_id: Optional[str] = None
    text: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    element_id: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    edge_type: Literal["derived_from", "references", "composed_of"]
    metadata: Optional[dict[str, Any]] = None


class GraphMetadata(BaseModel):
    run_id: str
    node_count: int = 0
    edge_count: int = 0
    documents_covered: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pipeline_version: Optional[str] = None


class EvidenceGraph(BaseModel):
    run_id: str
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    metadata: GraphMetadata


class GraphBackend(Protocol):
    """Protocol for graph data structure backends.

    The reference implementation uses NetworkX. Alternative backends
    (iGraph, SQL, Neo4j) can be swapped in by implementing this interface.
    """

    def add_node(self, node_id: str, attrs: dict) -> None: ...

    def add_edge(self, source: str, target: str, attrs: dict) -> None: ...

    def get_node(self, node_id: str) -> dict | None: ...

    def query_nodes(self, filters: dict) -> list[dict]: ...

    def traverse(
        self, start_id: str, direction: Literal["forward", "reverse"], max_depth: int
    ) -> list[list[dict]]: ...

    def to_serializable(self) -> dict: ...

    def from_serializable(self, data: dict) -> None: ...


def fingerprint_node(document_id: str, section_id: str | None, text: str, semantic_type: str | None) -> str:
    import hashlib

    raw = f"{document_id}|{section_id or ''}|{text}|{semantic_type or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
