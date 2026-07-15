from __future__ import annotations

import json
import os
import tempfile
from typing import Any

from pydantic import ValidationError

from .evidence_graph import EvidenceGraph, GraphEdge, GraphMetadata, GraphNode, InvalidGraphDataError


class GraphStore:
    """Persistence interface for evidence graphs using JSON Lines format."""

    @staticmethod
    def save(graph: EvidenceGraph, path: str) -> None:
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".jsonl", dir=dir_path or ".")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                meta = graph.metadata.model_dump(mode="json")
                meta["type"] = "metadata"
                f.write(json.dumps(meta) + "\n")
                for node_id, node in graph.nodes.items():
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
        if not os.path.isfile(path):
            raise InvalidGraphDataError(f"File not found: {path}")
        metadata: dict[str, Any] | None = None
        nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise InvalidGraphDataError(f"Line {line_no}: invalid JSON — {exc}") from exc
                record_type = record.pop("type", None)
                if record_type == "metadata":
                    record.pop("node_count", None)
                    record.pop("edge_count", None)
                    metadata = record
                elif record_type == "node":
                    try:
                        node = GraphNode(**record)
                    except ValidationError as exc:
                        raise InvalidGraphDataError(f"Line {line_no}: invalid node — {exc}") from exc
                    nodes[node.id] = node
                elif record_type == "edge":
                    try:
                        edge = GraphEdge(**record)
                    except ValidationError as exc:
                        raise InvalidGraphDataError(f"Line {line_no}: invalid edge — {exc}") from exc
                    edges.append(edge)
                else:
                    raise InvalidGraphDataError(f"Line {line_no}: unknown record type '{record_type}'")
        if metadata is None:
            raise InvalidGraphDataError("Missing metadata record (first line)")
        for edge in edges:
            if edge.source not in nodes:
                raise InvalidGraphDataError(f"Edge references non-existent source node: {edge.source}")
            if edge.target not in nodes:
                raise InvalidGraphDataError(f"Edge references non-existent target node: {edge.target}")
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
        return EvidenceGraph(run_id=gmeta.run_id, nodes=nodes, edges=edges, metadata=gmeta)

    @staticmethod
    def list_graphs(directory: str) -> list[str]:
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
        if os.path.isfile(path):
            os.remove(path)
