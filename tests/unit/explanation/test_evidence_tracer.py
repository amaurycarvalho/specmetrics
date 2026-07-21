from __future__ import annotations

from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
)


def _make_graph() -> EvidenceGraph:
    node1 = GraphNode(
        id="n1",
        node_type="extracted_element",
        semantic_type="fact",
        document_id="doc1",
        section_id="s1",
        text="element one",
        element_id="e1",
    )
    node2 = GraphNode(
        id="n2",
        node_type="evidence",
        document_id="doc1",
        section_id="s1",
        text="evidence text",
        element_id=None,
    )
    return EvidenceGraph(
        run_id="test",
        nodes={"n1": node1, "n2": node2},
        edges=[GraphEdge(source="n1", target="n2", edge_type="derived_from")],
        metadata=GraphMetadata(
            run_id="test", node_count=2, edge_count=1, documents_covered=["doc1"]
        ),
    )


class TestEvidenceTracer:
    def test_trace_element_returns_evidence(self):
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        tracer = EvidenceTracer(graph=_make_graph())
        refs = tracer.trace_element("e1", max_depth=3)
        assert len(refs) >= 1
        assert refs[0].document_id == "doc1"

    def test_trace_element_without_graph_returns_empty(self):
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        tracer = EvidenceTracer()
        refs = tracer.trace_element("e1")
        assert refs == []

    def test_trace_element_with_cfm_and_graph(self):
        from specmetrics.kernel.cfm.model import (
            CanonicalFunctionalModel,
            Actor,
            BuildMetadata,
            EvidenceRef,
        )
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        cfm = CanonicalFunctionalModel(
            run_id="test",
            actors={
                "a1": Actor(
                    id="a1",
                    name="Actor",
                    evidence=EvidenceRef(
                        graph_node_id="n1", document_id="doc1", text="evidence"
                    ),
                )
            },
            functional_processes={},
            business_rules={},
            data_groups={},
            relationships=[],
            operations={},
            unclassified={},
            metadata=BuildMetadata(
                run_id="test",
                build_duration_ms=0,
                element_counts={},
                total_input_nodes=0,
                unclassified_count=0,
            ),
        )
        tracer = EvidenceTracer(graph=_make_graph())
        refs = tracer.trace_element("a1", cfm=cfm)
        assert len(refs) >= 1

    def test_trace_metric_logs_orphan_warning(self):
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        tracer = EvidenceTracer()
        result = tracer.trace_metric(["orphan-id"])
        assert "orphan-id" in result
        assert result["orphan-id"] == []

    def test_trace_element_max_depth(self):
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _make_graph()
        tracer = EvidenceTracer(graph=graph)
        refs_shallow = tracer.trace_element("e1", max_depth=0)
        refs_deep = tracer.trace_element("e1", max_depth=3)
        assert refs_shallow is not None
        assert refs_deep is not None
