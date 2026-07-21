from __future__ import annotations

import json
import os
import tempfile

import pytest

from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
    InvalidGraphDataError,
)
from specmetrics.kernel.graph_persistence import GraphStore


@pytest.fixture
def sample_graph() -> EvidenceGraph:
    nodes = {
        "n1": GraphNode(
            id="n1", node_type="evidence", document_id="doc1", text="source text"
        ),
        "n2": GraphNode(
            id="n2",
            node_type="extracted_element",
            semantic_type="fact",
            document_id="doc1",
            text="fact content",
        ),
    }
    edges = [
        GraphEdge(source="n2", target="n1", edge_type="derived_from"),
    ]
    meta = GraphMetadata(
        run_id="test-run-1",
        node_count=2,
        edge_count=1,
        documents_covered=["doc1"],
    )
    return EvidenceGraph(run_id="test-run-1", nodes=nodes, edges=edges, metadata=meta)


class TestGraphStore:
    def test_save_writes_correct_format(self, sample_graph: EvidenceGraph) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            GraphStore.save(sample_graph, path)
            with open(path, "r") as f:
                lines = f.readlines()
            assert len(lines) == 4
            first = json.loads(lines[0])
            assert first["type"] == "metadata"
            assert first["run_id"] == "test-run-1"
            second = json.loads(lines[1])
            assert second["type"] == "node"
            assert second["id"] == "n1"
            third = json.loads(lines[2])
            assert third["type"] == "node"
            assert third["id"] == "n2"
            fourth = json.loads(lines[3])
            assert fourth["type"] == "edge"
            assert fourth["source"] == "n2"
            assert fourth["target"] == "n1"
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_reconstructs_identical_graph(
        self, sample_graph: EvidenceGraph
    ) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            GraphStore.save(sample_graph, path)
            loaded = GraphStore.load(path)
            assert loaded.run_id == sample_graph.run_id
            assert len(loaded.nodes) == len(sample_graph.nodes)
            assert len(loaded.edges) == len(sample_graph.edges)
            for nid, node in sample_graph.nodes.items():
                assert nid in loaded.nodes
                assert loaded.nodes[nid].text == node.text
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_corrupted_file_raises_error(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write("not valid json\n")
            path = f.name
        try:
            with pytest.raises(InvalidGraphDataError):
                GraphStore.load(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_load_missing_metadata_raises_error(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as f:
            f.write('{"type": "node", "id": "n1"}\n')
            path = f.name
        try:
            with pytest.raises(InvalidGraphDataError):
                GraphStore.load(path)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_list_graphs_finds_only_valid_graphs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            valid_path = os.path.join(tmpdir, "valid.jsonl")
            invalid_path = os.path.join(tmpdir, "invalid.jsonl")
            graph = EvidenceGraph(
                run_id="test",
                nodes={},
                edges=[],
                metadata=GraphMetadata(
                    run_id="test",
                    node_count=0,
                    edge_count=0,
                    documents_covered=[],
                ),
            )
            GraphStore.save(graph, valid_path)
            with open(invalid_path, "w") as f:
                f.write("garbage\n")
            graphs = GraphStore.list_graphs(tmpdir)
            assert valid_path in graphs
            assert invalid_path not in graphs

    def test_round_trip_preserves_all_data(self, sample_graph: EvidenceGraph) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            GraphStore.save(sample_graph, path)
            loaded = GraphStore.load(path)
            assert loaded.metadata.run_id == sample_graph.metadata.run_id
            assert loaded.metadata.node_count == sample_graph.metadata.node_count
            assert loaded.metadata.edge_count == sample_graph.metadata.edge_count
            assert set(loaded.metadata.documents_covered) == set(
                sample_graph.metadata.documents_covered
            )
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def test_delete_removes_file(self, sample_graph: EvidenceGraph) -> None:
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        GraphStore.save(sample_graph, path)
        assert os.path.isfile(path)
        GraphStore.delete(path)
        assert not os.path.exists(path)
