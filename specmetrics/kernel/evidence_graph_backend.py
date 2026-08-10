"""Shared graph backend and serialization helpers for the evidence graph stage."""

from __future__ import annotations

from types import ModuleType
from typing import Self

import structlog

from .evidence_graph import (
    GraphEdge,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopError,
)

logger = structlog.get_logger(__name__)

_NODE_TEXT_TRUNCATE = 200

_nx = None
_nx_lock = None


def _load_nx() -> ModuleType:
    """Import networkx lazily so the evidence graph does not block kernel import."""
    import importlib
    import threading

    global _nx, _nx_lock
    if _nx is None:
        if _nx_lock is None:
            _nx_lock = threading.Lock()
        with _nx_lock:
            if _nx is None:
                _nx = importlib.import_module("networkx")
    return _nx


class NetworkXBackend:
    """Graph backend implementation using NetworkX DiGraph.

    Implements the GraphBackend protocol.
    """

    def __init__(self: Self) -> None:
        """Initialize an empty NetworkX directed graph."""
        self._graph = _load_nx().DiGraph()

    def add_node(self: Self, node_id: str, attrs: dict) -> None:
        """Add a node with the given ID and attributes, raising on duplicates."""
        if self._graph.has_node(node_id):
            raise NodeAlreadyExistsError(node_id)
        self._graph.add_node(node_id, **attrs)

    def add_edge(self: Self, source: str, target: str, attrs: dict) -> None:
        """Add a directed edge between two nodes with the given attributes."""
        if not self._graph.has_node(source):
            raise NodeNotFoundError(source)
        if not self._graph.has_node(target):
            raise NodeNotFoundError(target)
        if source == target:
            raise SelfLoopError(source)
        self._graph.add_edge(source, target, **attrs)

    def get_node(self: Self, node_id: str) -> dict | None:
        """Return the node with the given ID, or None if it does not exist."""
        if not self._graph.has_node(node_id):
            return None
        return {"id": node_id, **dict(self._graph.nodes[node_id])}

    def query_nodes(self: Self, filters: dict) -> list[dict]:
        """Return nodes whose attributes match all the given filters."""
        results = []
        for node_id, data in self._graph.nodes(data=True):
            matches = all(data.get(k) == v for k, v in filters.items())
            if matches:
                results.append({"id": node_id, **data})
        return results

    def traverse(
        self: Self, start_id: str, direction: str, max_depth: int
    ) -> list[list[dict]]:
        """Return all paths from the start node following the given direction."""
        if not self._graph.has_node(start_id):
            raise NodeNotFoundError(start_id)
        paths = [[{"id": start_id, **dict(self._graph.nodes[start_id])}]]
        for _ in range(max_depth):
            new_paths = []
            for path in paths:
                last_id = path[-1]["id"]
                neighbors = (
                    self._graph.successors(last_id)
                    if direction == "forward"
                    else self._graph.predecessors(last_id)
                )
                for nid in neighbors:
                    if nid not in {n["id"] for n in path}:
                        new_paths.append(
                            path + [{"id": nid, **dict(self._graph.nodes[nid])}]
                        )
            if not new_paths:
                break
            paths = new_paths
        return paths

    def to_serializable(self: Self) -> dict:
        """Serialize the graph to a JSON-serializable structure."""
        return _load_nx().node_link_data(self._graph)

    def from_serializable(self: Self, data: dict) -> None:
        """Restore the graph from a serialized structure."""
        self._graph = _load_nx().node_link_graph(data)

    def remove_node(self: Self, node_id: str) -> None:
        """Remove the node with the given ID if it exists."""
        if self._graph.has_node(node_id):
            self._graph.remove_node(node_id)

    def remove_edge(self: Self, source: str, target: str) -> None:
        """Remove the edge between the given nodes if it exists."""
        if self._graph.has_edge(source, target):
            self._graph.remove_edge(source, target)


def truncate_text(s: str | None) -> str | None:
    """Truncate text to the stage node text limit, preserving None."""
    if s is None:
        return None
    return s[:_NODE_TEXT_TRUNCATE] if len(s) > _NODE_TEXT_TRUNCATE else s


def build_edges_from_serialized(
    serialized: dict, graph_nodes: dict[str, object]
) -> list[GraphEdge]:
    """Reconstruct graph edges from a serialized payload using known nodes."""
    known = {nid for nid in graph_nodes}
    return [
        GraphEdge(
            source=e["source"],
            target=e["target"],
            edge_type=e.get("edge_type", "derived_from"),
        )
        for e in serialized.get("edges", [])
        if e["source"] in known and e["target"] in known
    ]


def persist_graph(
    evidence_graph: object, run_id: str, node_count: int
) -> None:
    """Persist the built evidence graph to disk for a given run."""
    import os

    from .graph_persistence import GraphStore

    graphs_dir = os.path.join(os.getcwd(), ".specmetrics", "evidence_graphs")
    os.makedirs(graphs_dir, exist_ok=True)
    save_path = os.path.join(graphs_dir, f"{run_id}.jsonl")
    GraphStore.save(evidence_graph, save_path)
    logger.info("evidence_graph_saved", path=save_path, node_count=node_count)