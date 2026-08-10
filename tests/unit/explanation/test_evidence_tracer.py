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
            Actor,
            BuildMetadata,
            CanonicalFunctionalModel,
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


def _trace_node(nid: str, eid: str | None, doc_id: str, section_id: str = "secA", confidence: float | None = 0.9):
    return GraphNode(
        id=nid,
        node_type="extracted_element",
        semantic_type="fact",
        document_id=doc_id,
        section_id=section_id,
        text="text",
        confidence=confidence,
        element_id=eid,
    )


def _trace_graph(nodes, edges):
    from specmetrics.kernel.evidence_graph import EvidenceGraph

    return EvidenceGraph(
        run_id="test",
        nodes={n.id: n for n in nodes},
        edges=edges,
        metadata=GraphMetadata(
            run_id="test",
            node_count=len(nodes),
            edge_count=len(edges),
            documents_covered=[],
        ),
    )


class TestTraceGraphInternals:
    def test_max_depth_zero_still_traces_start_node(self):
        """Kills EvidenceTracer::_trace_graph__mutmut_4/10 (start depth must be zero)."""
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=0)
        assert [r.node_id for r in refs] == ["n1"]

    def test_cycle_does_not_reprocess_visited_element(self):
        """Kills EvidenceTracer::_trace_graph__mutmut_8/12 (visited guard prevents duplicates)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [
                GraphEdge(source="n1", target="n2", edge_type="derived_from"),
                GraphEdge(source="n2", target="n1", edge_type="derived_from"),
            ],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=3)
        assert [r.node_id for r in refs] == ["n1", "n2"]

    def test_trace_continues_after_skipping_visited_node(self):
        """Kills EvidenceTracer::_trace_graph__mutmut_11 (skipped node must not stop traversal)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [
                _trace_node("n1", "e1", "d1"),
                _trace_node("n2", "e2", "d2"),
                _trace_node("n3", "e3", "d3"),
                _trace_node("n4", "e4", "d4"),
            ],
            [
                GraphEdge(source="n1", target="n2", edge_type="derived_from"),
                GraphEdge(source="n1", target="n3", edge_type="derived_from"),
                GraphEdge(source="n2", target="n1", edge_type="derived_from"),
                GraphEdge(source="n3", target="n4", edge_type="derived_from"),
            ],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=3)
        assert "n4" in [r.node_id for r in refs]

    def test_trace_returns_refs_for_matching_node(self):
        """Kills EvidenceTracer::_trace_graph__mutmut_14/17 and _trace_graph_node__mutmut_2 (matching node collected)."""
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=3)
        assert refs[0].node_id == "n1"

    def test_ref_includes_section_id_and_confidence(self):
        """Kills EvidenceTracer::_trace_graph_node__mutmut_5/8/10/13 (section_id and confidence forwarded)."""
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1", section_id="secB", confidence=0.7)],
            [],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1")
        assert refs[0].section_id == "secB"
        assert refs[0].confidence == 0.7

    def test_edge_to_node_without_element_id_not_followed(self):
        """Kills EvidenceTracer::_trace_graph_node__mutmut_18 (target without element_id must not be queued)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", None, "d2")],
            [GraphEdge(source="n1", target="n2", edge_type="derived_from")],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=2)
        assert [r.node_id for r in refs] == ["n1"]

    def test_chain_neighbors_enqueued_and_traced(self):
        """Kills EvidenceTracer::_trace_graph_node__mutmut_16/17/19 (neighbor element ids queued for traversal)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [GraphEdge(source="n1", target="n2", edge_type="derived_from")],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=3)
        assert [r.node_id for r in refs] == ["n1", "n2"]

    def test_max_depth_one_reaches_neighbor(self):
        """Kills EvidenceTracer::_trace_graph_node__mutmut_21 (neighbor depth must increment by one)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [GraphEdge(source="n1", target="n2", edge_type="derived_from")],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=1)
        assert "n2" in [r.node_id for r in refs]

    def test_max_depth_zero_limits_to_start_node(self):
        """Kills EvidenceTracer::_trace_graph_node__mutmut_20 (neighbor depth must increment, not decrement)."""
        from specmetrics.kernel.evidence_graph import GraphEdge
        from specmetrics.kernel.explanation.evidence_tracer import EvidenceTracer

        graph = _trace_graph(
            [_trace_node("n1", "e1", "d1"), _trace_node("n2", "e2", "d2")],
            [GraphEdge(source="n1", target="n2", edge_type="derived_from")],
        )
        refs = EvidenceTracer(graph=graph).trace_element("e1", max_depth=0)
        assert [r.node_id for r in refs] == ["n1"]
