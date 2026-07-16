from __future__ import annotations

import structlog

from specmetrics.kernel.cfm.model import CanonicalFunctionalModel
from specmetrics.kernel.evidence_graph import EvidenceGraph

from .models import EvidenceReference

logger = structlog.get_logger(__name__)


class EvidenceTracer:
    def __init__(self, graph: EvidenceGraph | None = None):
        self._graph = graph

    @property
    def graph(self) -> EvidenceGraph | None:
        return self._graph

    @graph.setter
    def graph(self, value: EvidenceGraph | None) -> None:
        self._graph = value

    def trace_element(
        self,
        element_id: str,
        cfm: CanonicalFunctionalModel | None = None,
        max_depth: int = 3,
    ) -> list[EvidenceReference]:
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
            for node in self._graph.nodes.values():
                if node.element_id == element_id:
                    refs.append(
                        EvidenceReference(
                            document_id=node.document_id,
                            section_id=node.section_id,
                            text=node.text,
                            node_id=node.id,
                            confidence=node.confidence,
                        )
                    )

        return refs

    def trace_metric(
        self,
        element_ids: list[str],
        cfm: CanonicalFunctionalModel | None = None,
        max_depth: int = 3,
    ) -> dict[str, list[EvidenceReference]]:
        result: dict[str, list[EvidenceReference]] = {}
        for eid in element_ids:
            refs = self.trace_element(eid, cfm=cfm, max_depth=max_depth)
            if not refs:
                logger.warning("orphan_element_no_evidence", element_id=eid)
            result[eid] = refs
        return result
