"""Trace evidence references for elements using CFM and evidence graph data."""

from __future__ import annotations

from typing import Self

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.evidence_graph import EvidenceGraph

from .models import EvidenceReference

logger = structlog.get_logger(__name__)


class EvidenceTracer:
    """Trace evidence references for elements and metrics."""

    def __init__(self: Self, graph: EvidenceGraph | None = None) -> None:
        """Initialize the tracer with an optional evidence graph."""
        self._graph = graph

    @property
    def graph(self: Self) -> EvidenceGraph | None:
        """Return the current evidence graph, if any."""
        return self._graph

    @graph.setter
    def graph(self: Self, value: EvidenceGraph | None) -> None:
        """Set the evidence graph used for tracing."""
        self._graph = value

    def trace_element(
        self: Self,
        element_id: str,
        cfm: CanonicalFunctionalModel | None = None,
        max_depth: int = 3,
    ) -> list[EvidenceReference]:
        """Trace evidence references for a single element id."""
        refs: list[EvidenceReference] = []

        if cfm is not None:
            evidence_ref = cfm.trace_evidence(element_id)
            if evidence_ref is not None:
                refs.append(
                    EvidenceReference(
                        document_id=evidence_ref.document_id,
                        section_id=evidence_ref.section_id,
                        text=evidence_ref.text,
                        node_id=evidence_ref.graph_node_id,
                    )
                )

        if self._graph is not None:
            refs.extend(self._trace_graph(element_id, max_depth))

        return refs

    def _trace_graph(
        self: Self, element_id: str, max_depth: int
    ) -> list[EvidenceReference]:
        """Breadth-first search over the evidence graph for matching nodes."""
        refs: list[EvidenceReference] = []
        visited: set[str] = set()
        to_visit: list[tuple[str, int]] = [(element_id, 0)]
        while to_visit:
            current_id, depth = to_visit.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            refs.extend(self._trace_graph_node(current_id, depth, max_depth, to_visit))
        return refs

    def _trace_graph_node(
        self: Self,
        current_id: str,
        depth: int,
        max_depth: int,
        to_visit: list[tuple[str, int]],
    ) -> list[EvidenceReference]:
        """Collect evidence for one node and queue its reachable neighbors."""
        refs: list[EvidenceReference] = []
        for node in self._graph.nodes.values():
            if node.element_id == current_id:
                refs.append(
                    EvidenceReference(
                        document_id=node.document_id,
                        section_id=node.section_id,
                        text=node.text,
                        node_id=node.id,
                        confidence=node.confidence,
                    )
                )

            if depth < max_depth:
                for edge in self._graph.edges:
                    if edge.source == node.id:
                        target_node = self._graph.nodes.get(edge.target)
                        if target_node and target_node.element_id:
                            to_visit.append((target_node.element_id, depth + 1))
        return refs

    def trace_metric(
        self: Self,
        element_ids: list[str],
        cfm: CanonicalFunctionalModel | None = None,
        max_depth: int = 3,
    ) -> dict[str, list[EvidenceReference]]:
        """Trace evidence references for multiple element ids grouped by id."""
        result: dict[str, list[EvidenceReference]] = {}
        for eid in element_ids:
            refs = self.trace_element(eid, cfm=cfm, max_depth=max_depth)
            if not refs:
                logger.warning("orphan_element_no_evidence", element_id=eid)
            result[eid] = refs
        return result
