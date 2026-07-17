from __future__ import annotations


from specmetrics.kernel.csm.builder import build
from specmetrics.kernel.csm.model import CanonicalSpecificationModel
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
)

UUID_BASE = "00000000-0000-4000-8000-{:012d}"


def _uid(n: int) -> str:
    return UUID_BASE.format(n)


def _make_element_node(
    node_id: str,
    text: str,
    semantic_type: str | None = None,
) -> GraphNode:
    return GraphNode(
        id=node_id,
        node_type="extracted_element",
        semantic_type=semantic_type,  # type: ignore[arg-type]
        document_id="doc1",
        section_id="s1",
        text=text,
    )


def _make_evidence_node(
    node_id: str,
    text: str,
) -> GraphNode:
    return GraphNode(
        id=node_id,
        node_type="evidence",
        document_id="doc1",
        section_id="s1",
        text=text,
    )


def _make_graph(
    nodes: dict[str, GraphNode],
    edges: list[GraphEdge] | None = None,
    run_id: str = "test-run-1",
) -> EvidenceGraph:
    return EvidenceGraph(
        run_id=run_id,
        nodes=nodes,
        edges=edges or [],
        metadata=GraphMetadata(
            run_id=run_id,
            node_count=len(nodes),
            edge_count=len(edges or []),
        ),
    )


class TestBuild:
    def test_build_from_openspec_graph(self):
        nodes = {
            _uid(1): _make_element_node(_uid(1), "We decided to use Python", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "Assume 99.9% uptime", semantic_type="fact"),
            _uid(3): _make_element_node(_uid(3), "What is the target latency?", semantic_type="fact"),
            _uid(4): _make_element_node(_uid(4), "Given user is authenticated, when they request data, then return 200", semantic_type="fact"),
            _uid(5): _make_element_node(_uid(5), "Explore authentication options", semantic_type="fact"),
        }
        graph = _make_graph(nodes)
        csm = build(graph)

        assert isinstance(csm, CanonicalSpecificationModel)
        assert csm.run_id == "test-run-1"
        assert len(csm.decisions) >= 1
        assert len(csm.assumptions) >= 1
        assert len(csm.open_questions) >= 1
        assert len(csm.acceptance_criteria) >= 1
        assert csm.metadata.total_input_nodes == 5

    def test_framework_normalization(self):
        openspec_nodes = {
            _uid(1): _make_element_node(_uid(1), "We decided to use Python", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "Explore requirements", semantic_type="fact"),
        }
        speckit_nodes = {
            _uid(1): _make_element_node(_uid(1), "We decided to use Python", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "Explore requirements", semantic_type="fact"),
        }

        openspec_csm = build(_make_graph(openspec_nodes, run_id="openspec-run"))
        speckit_csm = build(_make_graph(speckit_nodes, run_id="speckit-run"))

        assert isinstance(openspec_csm, type(speckit_csm))
        assert set(openspec_csm.decisions.keys()) == set(speckit_csm.decisions.keys())
        assert set(openspec_csm.get_elements("decisions").keys()) == set(
            speckit_csm.get_elements("decisions").keys()
        )

    def test_empty_graph(self):
        graph = _make_graph({})
        csm = build(graph)

        assert isinstance(csm, CanonicalSpecificationModel)
        assert len(csm.decisions) == 0
        assert len(csm.assumptions) == 0
        assert len(csm.open_questions) == 0
        assert len(csm.acceptance_criteria) == 0
        assert len(csm.specification_activities) == 0
        assert len(csm.constraints) == 0
        assert len(csm.risks) == 0
        assert len(csm.glossary_terms) == 0
        assert len(csm.references) == 0
        assert csm.metadata.element_counts["decisions"] == 0

    def test_empty_graph_no_errors(self):
        graph = _make_graph({})
        csm = build(graph)
        assert csm.run_id == "test-run-1"

    def test_unclassifiable_elements_preserved(self):
        nodes = {
            _uid(1): _make_element_node(_uid(1), "Some random description text", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "More arbitrary content here", semantic_type="fact"),
        }
        edges = [
            GraphEdge(source=_uid(1), target=_uid(2), edge_type="references"),
        ]
        graph = _make_graph(nodes, edges)
        csm = build(graph)

        assert len(csm.references) >= 1
        for ref in csm.references.values():
            assert ref.description != ""
            assert len(ref.evidence_references) > 0

    def test_specification_activity_linking(self):
        nodes = {
            _uid(1): _make_element_node(_uid(1), "Explore and analyze requirements", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "We decided to use Python", semantic_type="fact"),
            _uid(3): _make_element_node(_uid(3), "Assume 99% uptime SLA", semantic_type="fact"),
        }
        edges = [
            GraphEdge(source=_uid(1), target=_uid(2), edge_type="derived_from"),
            GraphEdge(source=_uid(1), target=_uid(3), edge_type="derived_from"),
        ]
        graph = _make_graph(nodes, edges)
        csm = build(graph)

        assert len(csm.specification_activities) >= 1
        assert len(csm.decisions) >= 1
        assert len(csm.assumptions) >= 1

    def test_build_metadata_populated(self):
        nodes = {
            _uid(1): _make_element_node(_uid(1), "We decided to use Python", semantic_type="fact"),
            _uid(2): _make_element_node(_uid(2), "Some random unclassifiable text", semantic_type="fact"),
        }
        graph = _make_graph(nodes)
        csm = build(graph)

        meta = csm.metadata
        assert meta.run_id == "test-run-1"
        assert meta.total_input_nodes == 2
        assert meta.build_duration_ms >= 0
        assert "decisions" in meta.element_counts

    def test_performance_500_elements(self):
        import time

        nodes = {}
        for i in range(500):
            texts = [
                f"We decided on option {i}",
                f"Assume condition {i}",
                f"What is the value of {i}?",
                f"Given input {i}, when processed, then output",
                f"Explore feature {i}",
                f"Risk of failure in scenario {i}",
                f"Must comply with regulation {i}",
                f"Glossary Term {i}: Definition of concept {i}",
            ]
            text = texts[i % len(texts)]
            nid = _uid(i)
            nodes[nid] = _make_element_node(nid, text)

        graph = _make_graph(nodes)

        start = time.time()
        csm = build(graph)
        elapsed = time.time() - start

        assert isinstance(csm, CanonicalSpecificationModel)
        assert elapsed < 3.0, f"Performance benchmark failed: {elapsed:.3f}s (limit: 3.0s)"
