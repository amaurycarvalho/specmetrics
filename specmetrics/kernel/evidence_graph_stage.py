"""Pipeline stage that builds and persists the evidence graph."""

from __future__ import annotations

from typing import Self

import structlog

from .events import EventType, PipelineEvent
from .evidence_graph import (
    EvidenceGraph,
    GraphBackend,
    GraphMetadata,
    GraphNode,
    NodeAlreadyExistsError,
    fingerprint_node,
)
from .evidence_graph_backend import (
    NetworkXBackend,
    build_edges_from_serialized,
    persist_graph,
    truncate_text,
)
from .extraction_provider import ExtractedElement
from .pipeline_context import PipelineContext

logger = structlog.get_logger(__name__)


class EvidenceGraphStage:
    """Pipeline stage that builds and manages the evidence graph.

    Consumes SEMANTIC_EXTRACTION_COMPLETED events, constructs a provenance
    graph from extracted elements, and persists it for downstream stages.
    """

    def __init__(
        self: Self,
        backend: GraphBackend | None = None,
        max_memory_nodes: int = 50_000,
    ) -> None:
        """Initialize the stage with an optional backend and memory threshold."""
        self._backend = backend or NetworkXBackend()
        self._max_memory_nodes = max_memory_nodes
        self._handled_event_type = EventType.SEMANTIC_EXTRACTION_COMPLETED
        self._handler_id = "evidence_graph_stage"
        self._stage_name = "evidence_graph"

    @property
    def handled_event_type(self: Self) -> EventType:
        """Return the event type this stage handles."""
        return self._handled_event_type

    @property
    def handler_id(self: Self) -> str:
        """Return the handler ID of this stage."""
        return self._handler_id

    @property
    def stage_name(self: Self) -> str:
        """Return the name of this stage."""
        return self._stage_name

    def handle(self: Self, event: PipelineEvent) -> PipelineContext:
        """Build the evidence graph from an extraction event and persist it."""
        context = event.context
        extraction_ctx = getattr(context, "extraction_result", None) or {}
        extraction_data = extraction_ctx.get("results", {})
        run_id = str(int(event.timestamp.timestamp()))

        node_count, edge_count, docs_covered = self._insert_elements(extraction_data)

        metadata = GraphMetadata(
            run_id=run_id,
            node_count=node_count,
            edge_count=edge_count,
            documents_covered=sorted(docs_covered),
        )

        payload_out = self._build_payload(run_id, node_count, edge_count, docs_covered)

        graph_nodes, dropped_nodes = self._load_graph_nodes()
        if dropped_nodes:
            logger.warning("evidence_graph_dropped_invalid_nodes", count=dropped_nodes)
        serialized = self._backend.to_serializable()
        graph_edges = build_edges_from_serialized(serialized, graph_nodes)
        evidence_graph = EvidenceGraph(
            run_id=run_id,
            nodes=graph_nodes,
            edges=graph_edges,
            metadata=metadata,
        )

        try:
            persist_graph(evidence_graph, run_id, node_count)
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

    def _insert_elements(self: Self, extraction_data: dict) -> tuple[int, int, set[str]]:
        docs_covered: set[str] = set()
        node_count = 0
        edge_count = 0
        for result_data in extraction_data.values():
            for elem_data in result_data.get("elements", []):
                element = ExtractedElement(**elem_data)
                if not element.evidence.document_id or not element.evidence.text:
                    logger.warning(
                        "broken_evidence_reference",
                        element_id=element.id,
                        document_id=element.evidence.document_id,
                    )
                node_delta, edge_delta = self._add_element_nodes(element)
                node_count += node_delta
                edge_count += edge_delta
                docs_covered.add(element.evidence.document_id)
        return node_count, edge_count, docs_covered

    def _add_element_nodes(self: Self, element: ExtractedElement) -> tuple[int, int]:
        nid = fingerprint_node(
            element.evidence.document_id,
            element.evidence.section_id,
            element.evidence.text,
            element.type,
        )
        added = 0
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
            added += 1
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
            added += 1
        except NodeAlreadyExistsError:
            pass

        edge_added = 0
        try:
            self._backend.add_edge(nid, eid, {"edge_type": "derived_from"})
            edge_added = 1
        except Exception:
            pass
        return added, edge_added

    def _build_payload(
        self: Self,
        run_id: str,
        node_count: int,
        edge_count: int,
        docs_covered: set[str],
    ) -> dict:
        payload_nodes: list[dict] = []
        for node_data in self._backend.query_nodes({}):
            nid = node_data.get("id", "")
            if not nid:
                continue
            payload_nodes.append(
                {
                    "id": nid,
                    "node_type": node_data.get("node_type", ""),
                    "semantic_type": node_data.get("semantic_type"),
                    "document_id": node_data.get("document_id"),
                    "section_id": node_data.get("section_id"),
                    "text": truncate_text(node_data.get("text")),
                }
            )
        return {
            "run_id": run_id,
            "node_count": node_count,
            "edge_count": edge_count,
            "documents_covered": sorted(docs_covered),
            "nodes": payload_nodes,
        }

    def _load_graph_nodes(self: Self) -> tuple[dict[str, GraphNode], int]:
        graph_nodes: dict[str, GraphNode] = {}
        dropped_nodes = 0
        for node_data in self._backend.query_nodes({}):
            nid = node_data.get("id", "")
            if not nid:
                continue
            attrs = {k: v for k, v in node_data.items() if k != "id"}
            try:
                graph_nodes[nid] = GraphNode(id=nid, **attrs)
            except Exception:
                dropped_nodes += 1
        return graph_nodes, dropped_nodes

    def update_for_document(
        self: Self, document_id: str, extraction_result_data: dict
    ) -> None:
        """Replace the graph nodes for a single document with fresh extraction."""
        nodes_to_remove = [
            n["id"]
            for n in self._backend.query_nodes({"document_id": document_id})
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
