"""Persistence for evidence graphs using JSON Lines format."""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from pydantic import ValidationError

from .evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    InvalidGraphDataError,
)


class GraphStore:
    """Persistence interface for evidence graphs using JSON Lines format."""

    @staticmethod
    def save(graph: EvidenceGraph, path: str) -> None:
        """Save the evidence graph to the given path as JSON Lines."""
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".jsonl", dir=dir_path or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                meta = graph.metadata.model_dump(mode="json")
                meta["type"] = "metadata"
                f.write(json.dumps(meta) + "\n")
                for node in graph.nodes.values():
                    record = node.model_dump(mode="json")
                    record["type"] = "node"
                    f.write(json.dumps(record) + "\n")
                for edge in graph.edges:
                    record = edge.model_dump(mode="json")
                    record["type"] = "edge"
                    f.write(json.dumps(record) + "\n")
            os.replace(tmp_path, path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    @staticmethod
    def load(path: str) -> EvidenceGraph:
        """Load an evidence graph from the given JSON Lines file."""
        if not os.path.isfile(path):
            raise InvalidGraphDataError(f"File not found: {path}")
        metadata, nodes, edges = GraphStore._read_records(path)
        if metadata is None:
            raise InvalidGraphDataError("Missing metadata record (first line)")
        GraphStore._validate_edges(edges, nodes)
        node_count = len(nodes)
        edge_count = len(edges)
        documents = list({n.document_id for n in nodes.values()})
        gmeta = GraphMetadata(
            run_id=metadata.get("run_id", "unknown"),
            node_count=node_count,
            edge_count=edge_count,
            documents_covered=documents,
            created_at=metadata.get("created_at", "2026-01-01T00:00:00"),
            pipeline_version=metadata.get("pipeline_version"),
        )
        return EvidenceGraph(
            run_id=gmeta.run_id, nodes=nodes, edges=edges, metadata=gmeta
        )

    @staticmethod
    def _read_records(
        path: str,
    ) -> tuple[dict[str, Any] | None, dict[str, GraphNode], list[GraphEdge]]:
        metadata: dict[str, Any] | None = None
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                record_type, record = GraphStore._load_line(line_no, line)
                if record_type == "metadata":
                    metadata = GraphStore._parse_metadata_record(record)
                elif record_type == "node":
                    node = GraphStore._parse_node_record(record, line_no)
                    nodes[node.id] = node
                elif record_type == "edge":
                    edges.append(GraphStore._parse_edge_record(record, line_no))
                else:
                    raise InvalidGraphDataError(
                        f"Line {line_no}: unknown record type '{record_type}'"
                    )
        return metadata, nodes, edges

    @staticmethod
    def _load_line(line_no: int, line: str) -> tuple[str | None, Any]:
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InvalidGraphDataError(f"Line {line_no}: invalid JSON — {exc}") from exc
        return record.pop("type", None), record

    @staticmethod
    def _parse_metadata_record(record: dict[str, Any]) -> dict[str, Any]:
        record.pop("node_count", None)
        record.pop("edge_count", None)
        return record

    @staticmethod
    def _parse_node_record(
        record: dict[str, Any], line_no: int
    ) -> GraphNode:
        try:
            return GraphNode(**record)
        except ValidationError as exc:
            raise InvalidGraphDataError(
                f"Line {line_no}: invalid node — {exc}"
            ) from exc

    @staticmethod
    def _parse_edge_record(
        record: dict[str, Any], line_no: int
    ) -> GraphEdge:
        try:
            return GraphEdge(**record)
        except ValidationError as exc:
            raise InvalidGraphDataError(
                f"Line {line_no}: invalid edge — {exc}"
            ) from exc

    @staticmethod
    def _validate_edges(edges: list[GraphEdge], nodes: dict[str, GraphNode]) -> None:
        for edge in edges:
            if edge.source not in nodes:
                raise InvalidGraphDataError(
                    f"Edge references non-existent source node: {edge.source}"
                )
            if edge.target not in nodes:
                raise InvalidGraphDataError(
                    f"Edge references non-existent target node: {edge.target}"
                )

    @staticmethod
    def list_graphs(directory: str) -> list[str]:
        """Return sorted paths of valid evidence graph files in a directory."""
        result = []
        try:
            for entry in os.scandir(directory):
                if entry.is_file() and entry.name.endswith(".jsonl"):
                    try:
                        GraphStore.load(entry.path)
                        result.append(entry.path)
                    except (InvalidGraphDataError, Exception):
                        pass
        except FileNotFoundError:
            pass
        return sorted(result)

    @staticmethod
    def delete(path: str) -> None:
        """Delete the evidence graph file at the given path if it exists."""
        if os.path.isfile(path):
            os.remove(path)
