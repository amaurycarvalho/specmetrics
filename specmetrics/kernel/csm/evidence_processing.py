from __future__ import annotations

from typing import Optional

from specmetrics.kernel.evidence_graph import EvidenceGraph, GraphNode
from .model import EvidenceRef


def get_evidence_references(
    node_id: str, graph: EvidenceGraph
) -> list[EvidenceRef]:
    refs: list[EvidenceRef] = []

    for edge in graph.edges:
        if edge.source == node_id and edge.edge_type in ("derived_from", "references"):
            target_node = graph.nodes.get(edge.target)
            if target_node is not None:
                refs.append(
                    EvidenceRef(
                        graph_node_id=target_node.id,
                        document_id=target_node.document_id,
                        section_id=target_node.section_id,
                        text=target_node.text,
                    )
                )

    node = graph.nodes.get(node_id)
    if node is not None:
        refs.append(
            EvidenceRef(
                graph_node_id=node.id,
                document_id=node.document_id,
                section_id=node.section_id,
                text=node.text,
            )
        )

    return refs


def get_neighbors(
    node_id: str, graph: EvidenceGraph, edge_type: Optional[str] = None
) -> list[GraphNode]:
    neighbors: list[GraphNode] = []

    for edge in graph.edges:
        if edge.source == node_id:
            if edge_type is None or edge.edge_type == edge_type:
                target = graph.nodes.get(edge.target)
                if target is not None:
                    neighbors.append(target)
        elif edge.target == node_id:
            if edge_type is None or edge.edge_type == edge_type:
                source = graph.nodes.get(edge.source)
                if source is not None:
                    neighbors.append(source)

    return neighbors


def get_nodes_by_type(
    graph: EvidenceGraph, node_type: str
) -> list[GraphNode]:
    return [
        node for node in graph.nodes.values() if node.node_type == node_type
    ]
