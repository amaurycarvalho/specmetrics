"""Core data model and backend protocol for the evidence graph."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal, Protocol, Self

from pydantic import BaseModel, Field


class EvidenceGraphError(Exception):
    """Base exception for evidence graph operations."""


class NodeNotFoundError(EvidenceGraphError):
    """Raised when a referenced node ID does not exist in the graph."""

    def __init__(self: Self, node_id: str) -> None:
        """Initialize the error with the missing node ID."""
        super().__init__(f"Node not found: {node_id}")
        self.node_id = node_id


class NodeAlreadyExistsError(EvidenceGraphError):
    """Raised when adding a node with an ID that already exists."""

    def __init__(self: Self, node_id: str) -> None:
        """Initialize the error with the duplicate node ID."""
        super().__init__(f"Node already exists: {node_id}")
        self.node_id = node_id


class EdgeAlreadyExistsError(EvidenceGraphError):
    """Raised when adding a duplicate edge."""

    def __init__(self: Self, source: str, target: str) -> None:
        """Initialize the error with the duplicate edge endpoints."""
        super().__init__(source, target)
        self.source = source
        self.target = target


class SelfLoopError(EvidenceGraphError):
    """Raised when adding an edge where source equals target."""

    def __init__(self: Self, node_id: str) -> None:
        """Initialize the error with the self-loop node ID."""
        super().__init__(f"Self-loop not allowed: {node_id}")
        self.node_id = node_id


class InvalidGraphDataError(EvidenceGraphError):
    """Raised when graph data is invalid or corrupted."""


class GraphNode(BaseModel):
    """A node in the evidence graph."""

    id: str
    node_type: Literal["extracted_element", "evidence"]
    semantic_type: Literal["fact", "entity", "relationship", "operation"] | None = (
        None
    )
    document_id: str
    section_id: str | None = None
    text: str
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    element_id: str | None = None


class GraphEdge(BaseModel):
    """A directed edge in the evidence graph."""

    source: str
    target: str
    edge_type: Literal["derived_from", "references", "composed_of"]
    metadata: dict[str, Any] | None = None


class GraphMetadata(BaseModel):
    """Metadata describing the provenance of an evidence graph."""

    run_id: str
    node_count: int = 0
    edge_count: int = 0
    documents_covered: list[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    pipeline_version: str | None = None


class EvidenceGraph(BaseModel):
    """Container for an evidence graph and its metadata."""

    run_id: str
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    metadata: GraphMetadata


class GraphBackend(Protocol):
    """Protocol for graph data structure backends.

    The reference implementation uses NetworkX. Alternative backends
    (iGraph, SQL, Neo4j) can be swapped in by implementing this interface.
    """

    def add_node(self: Self, node_id: str, attrs: dict) -> None:
        """Add a node with the given ID and attributes."""

    def add_edge(self: Self, source: str, target: str, attrs: dict) -> None:
        """Add a directed edge between two nodes with the given attributes."""

    def get_node(self: Self, node_id: str) -> dict | None:
        """Return the node with the given ID, or None if it does not exist."""

    def query_nodes(self: Self, filters: dict) -> list[dict]:
        """Return nodes matching all the given filter attributes."""

    def traverse(
        self: Self,
        start_id: str,
        direction: Literal["forward", "reverse"],
        max_depth: int,
    ) -> list[list[dict]]:
        """Return all paths from the start node up to the given depth."""

    def to_serializable(self: Self) -> dict:
        """Serialize the graph to a JSON-serializable structure."""

    def from_serializable(self: Self, data: dict) -> None:
        """Restore the graph from a serialized structure."""


def fingerprint_node(
    document_id: str, section_id: str | None, text: str, semantic_type: str | None
) -> str:
    """Generate a deterministic UUID-style fingerprint for a node."""
    import hashlib
    import uuid

    raw = f"{document_id}|{section_id or ''}|{text}|{semantic_type or ''}"
    full_hash = hashlib.sha256(raw.encode("utf-8")).digest()
    b = bytearray(full_hash[:16])
    b[6] = (b[6] & 0x0F) | 0x40
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))
