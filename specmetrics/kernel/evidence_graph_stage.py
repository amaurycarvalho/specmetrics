from __future__ import annotations

import networkx as nx
import structlog

from .events import EventType, PipelineEvent
from .evidence_graph import (
    EvidenceGraph,
    GraphBackend,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    NodeAlreadyExistsError,
    NodeNotFoundError,
    SelfLoopError,
    fingerprint_node,
)
from .extraction_provider import ExtractedElement
from .graph_persistence import GraphStore
from .pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


class NetworkXBackend:
    """Graph backend implementation using NetworkX DiGraph.

    Implements the GraphBackend protocol.
    """

    def __init__(self) -> None:
        self._graph = nx.DiGraph()

    def add_node(self, node_id: str, attrs: dict) -> None:
        if self._graph.has_node(node_id):
            raise NodeAlreadyExistsError(node_id)
        self._graph.add_node(node_id, **attrs)

    def add_edge(self, source: str, target: str, attrs: dict) -> None:
        if not self._graph.has_node(source):
            raise NodeNotFoundError(source)
        if not self._graph.has_node(target):
            raise NodeNotFoundError(target)
        if source == target:
            raise SelfLoopError(source)
        self._graph.add_edge(source, target, **attrs)

    def get_node(self, node_id: str) -> dict | None:
        if not self._graph.has_node(node_id):
            return None
        return {"id": node_id, **dict(self._graph.nodes[node_id])}

    def query_nodes(self, filters: dict) -> list[dict]:
        results = []
        for node_id, data in self._graph.nodes(data=True):
            matches = all(data.get(k) == v for k, v in filters.items())
            if matches:
                results.append({"id": node_id, **data})
        return results

    def traverse(
        self, start_id: str, direction: str, max_depth: int
    ) -> list[list[dict]]:
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

    def to_serializable(self) -> dict:
        return nx.node_link_data(self._graph)

    def from_serializable(self, data: dict) -> None:
        self._graph = nx.node_link_graph(data)

    def remove_node(self, node_id: str) -> None:
        if self._graph.has_node(node_id):
            self._graph.remove_node(node_id)

    def remove_edge(self, source: str, target: str) -> None:
        if self._graph.has_edge(source, target):
            self._graph.remove_edge(source, target)


class EvidenceGraphStage:
    """Pipeline stage that builds and manages the evidence graph.

    Consumes SEMANTIC_EXTRACTION_COMPLETED events, constructs a provenance
    graph from extracted elements, and persists it for downstream stages.
    """

    def __init__(
        self,
        backend: GraphBackend | None = None,
        max_memory_nodes: int = 50_000,
    ) -> None:
        self._backend = backend or NetworkXBackend()
        self._max_memory_nodes = max_memory_nodes
        self._handled_event_type = EventType.SEMANTIC_EXTRACTION_COMPLETED
        self._handler_id = "evidence_graph_stage"
        self._stage_name = "evidence_graph"

    @property
    def handled_event_type(self) -> EventType:
        return self._handled_event_type

    @property
    def handler_id(self) -> str:
        return self._handler_id

    @property
    def stage_name(self) -> str:
        return self._stage_name

    def handle(self, event: PipelineEvent) -> PipelineContext:
        context = event.context
        extraction_ctx = getattr(context, "extraction_result", None) or {}
        extraction_data = extraction_ctx.get("results", {})
        run_id = str(int(event.timestamp.timestamp()))
        docs_covered: set[str] = set()
        node_count = 0
        edge_count = 0

        for provider_id, result_data in extraction_data.items():
            elements_data = result_data.get("elements", [])
            for elem_data in elements_data:
                element = ExtractedElement(**elem_data)
                if not element.evidence.document_id or not element.evidence.text:
                    logger.warning(
                        "broken_evidence_reference",
                        element_id=element.id,
                        document_id=element.evidence.document_id,
                    )
                nid = fingerprint_node(
                    element.evidence.document_id,
                    element.evidence.section_id,
                    element.evidence.text,
                    element.type,
                )
                try:
                    self._backend.add_node(
                        nid,
                        {
                            "node_type": "extracted_element",
                            "semantic_type": element.type,
                            "document_id": element.evidence.document_id,
                            "section_id": element.evidence.section_id,
                            "text": element.content,
                            "confidence": element.confidence,
                            "element_id": element.id,
                        },
                    )
                    node_count += 1
                except NodeAlreadyExistsError:
                    pass

                eid = fingerprint_node(
                    element.evidence.document_id,
                    element.evidence.section_id,
                    element.evidence.text,
                    None,
                )
                try:
                    self._backend.add_node(
                        eid,
                        {
                            "node_type": "evidence",
                            "document_id": element.evidence.document_id,
                            "section_id": element.evidence.section_id,
                            "text": element.evidence.text,
                        },
                    )
                    node_count += 1
                except NodeAlreadyExistsError:
                    pass

                try:
                    self._backend.add_edge(
                        nid, eid, {"edge_type": "derived_from"}
                    )
                    edge_count += 1
                except Exception:
                    pass

                docs_covered.add(element.evidence.document_id)

        metadata = GraphMetadata(
            run_id=run_id,
            node_count=node_count,
            edge_count=edge_count,
            documents_covered=sorted(docs_covered),
        )

        payload_out = {
            "run_id": run_id,
            "node_count": node_count,
            "edge_count": edge_count,
            "documents_covered": sorted(docs_covered),
        }

        dropped_nodes = 0
        graph_nodes = {}
        for node_data in self._backend.query_nodes({}):
            nid = node_data.get("id", "")
            if nid:
                attrs = {k: v for k, v in node_data.items() if k != "id"}
                try:
                    graph_nodes[nid] = GraphNode(id=nid, **attrs)
                except Exception:
                    dropped_nodes += 1
        if dropped_nodes:
            logger.warning("evidence_graph_dropped_invalid_nodes", count=dropped_nodes)
        serialized = self._backend.to_serializable()
        graph_edges = [
            GraphEdge(source=e["source"], target=e["target"], edge_type=e.get("edge_type", "derived_from"))
            for e in serialized.get("edges", [])
            if e["source"] in graph_nodes and e["target"] in graph_nodes
        ]
        evidence_graph = EvidenceGraph(
            run_id=run_id,
            nodes=graph_nodes,
            edges=graph_edges,
            metadata=metadata,
        )

        try:
            import os
            graphs_dir = os.path.join(os.getcwd(), ".specmetrics", "evidence_graphs")
            os.makedirs(graphs_dir, exist_ok=True)
            save_path = os.path.join(graphs_dir, f"{run_id}.jsonl")
            GraphStore.save(evidence_graph, save_path)
            logger.info("evidence_graph_saved", path=save_path, node_count=node_count)
        except Exception as exc:
            logger.warning("evidence_graph_save_failed", error=str(exc))

        if node_count > self._max_memory_nodes:
            logger.warning(
                "evidence_graph_exceeded_memory_threshold",
                node_count=node_count,
                max_memory_nodes=self._max_memory_nodes,
                hint="Consider increasing max_memory_nodes or switching to a persistent database backend",
            )

        built_event = PipelineEvent(
            event_type=EventType.EVIDENCE_GRAPH_BUILT,
            publisher=self._handler_id,
            payload=payload_out,
            context=context,
        )
        return context.with_stage_output(
            field_name="evidence_graph",
            value=payload_out,
            event=built_event,
        )

    def update_for_document(self, document_id: str, extraction_result_data: dict) -> None:
        nodes_to_remove = [
            n["id"] for n in self._backend.query_nodes({"document_id": document_id})
            if n.get("id")
        ]
        for nid in nodes_to_remove:
            try:
                self._backend.remove_node(nid)
            except Exception:
                pass
        for elem_data in extraction_result_data.get("elements", []):
            element = ExtractedElement(**elem_data)
            nid = fingerprint_node(
                element.evidence.document_id,
                element.evidence.section_id,
                element.evidence.text,
                element.type,
            )
            try:
                self._backend.add_node(
                    nid,
                    {
                        "node_type": "extracted_element",
                        "semantic_type": element.type,
                        "document_id": element.evidence.document_id,
                        "section_id": element.evidence.section_id,
                        "text": element.content,
                        "confidence": element.confidence,
                        "element_id": element.id,
                    },
                )
            except NodeAlreadyExistsError:
                pass
            eid = fingerprint_node(
                element.evidence.document_id,
                element.evidence.section_id,
                element.evidence.text,
                None,
            )
            try:
                self._backend.add_node(
                    eid,
                    {
                        "node_type": "evidence",
                        "document_id": element.evidence.document_id,
                        "section_id": element.evidence.section_id,
                        "text": element.evidence.text,
                    },
                )
            except NodeAlreadyExistsError:
                pass
            try:
                self._backend.add_edge(nid, eid, {"edge_type": "derived_from"})
            except Exception:
                pass
