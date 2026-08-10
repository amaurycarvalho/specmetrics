from __future__ import annotations

from specmetrics.kernel import evidence_graph_backend as mod
from specmetrics.kernel.evidence_graph_backend import (
    NetworkXBackend,
    build_edges_from_serialized,
    persist_graph,
    truncate_text,
)
from specmetrics.kernel.graph_persistence import GraphStore


def test_load_nx_imports_networkx_when_unset(monkeypatch) -> None:
    """Kills _load_nx__mutmut_1..8 (cached-import condition and import call mutations)."""
    monkeypatch.setattr(mod, "_nx", None)
    monkeypatch.setattr(mod, "_nx_lock", None)
    nx = mod._load_nx()
    assert nx is not None
    assert nx.__name__ == "networkx"


def test_add_edge_preserves_attrs() -> None:
    """Kills NetworkXBackend::add_edge__mutmut_10 (``**attrs`` argument deletion)."""
    backend = NetworkXBackend()
    backend.add_node("a", {})
    backend.add_node("b", {})
    backend.add_edge("a", "b", {"weight": 5, "kind": "derived"})
    edge = backend._graph.get_edge_data("a", "b")
    assert edge["weight"] == 5
    assert edge["kind"] == "derived"


def test_traverse_backward_uses_predecessors() -> None:
    """Kills NetworkXBackend::traverse__mutmut_19 (``predecessors(last_id)`` -> ``predecessors(None)``)."""
    backend = NetworkXBackend()
    for nid in ("a", "b", "c"):
        backend.add_node(nid, {})
    backend.add_edge("a", "b", {})
    backend.add_edge("b", "c", {})
    paths = backend.traverse("c", "backward", 1)
    assert [p["id"] for p in paths[0]] == ["c", "b"]


def test_truncate_text_preserves_none() -> None:
    """Kills truncate_text__mutmut_1 (``if s is None`` -> ``if s is not None``)."""
    assert truncate_text(None) is None


def test_truncate_text_at_200_chars_unchanged() -> None:
    """Kills truncate_text__mutmut_2 (``len(s) > 200`` -> ``len(s) >= 200``)."""
    assert truncate_text("x" * 200) == "x" * 200
    assert truncate_text("x" * 201) == "x" * 200


def test_build_edges_uses_edge_type_default() -> None:
    """Kills build_edges_from_serialized__mutmut_13 (default -> None), mutmut_15 (default arg dropped), mutmut_18/19 (default literal)."""
    known = {"n1": object(), "n2": object()}
    serialized = {"edges": [{"source": "n1", "target": "n2"}]}
    edges = build_edges_from_serialized(serialized, known)
    assert len(edges) == 1
    assert edges[0].source == "n1"
    assert edges[0].target == "n2"
    assert edges[0].edge_type == "derived_from"


def test_build_edges_uses_provided_edge_type() -> None:
    """Kills build_edges_from_serialized__mutmut_12 (``get(None, ...)``), mutmut_16/17 (edge_type key renamed), mutmut_24/25 (edges key renamed)."""
    known = {"n1": object(), "n2": object()}
    serialized = {
        "edges": [{"source": "n1", "target": "n2", "edge_type": "references"}]
    }
    edges = build_edges_from_serialized(serialized, known)
    assert len(edges) == 1
    assert edges[0].edge_type == "references"


def test_build_edges_defaults_to_empty_when_no_edges_key() -> None:
    """Kills build_edges_from_serialized__mutmut_20 (``get(None, [])``), mutmut_21 (default -> None), mutmut_23 (default arg dropped)."""
    assert build_edges_from_serialized({"nodes": []}, {"n1": object()}) == []


def test_build_edges_skips_when_target_unknown() -> None:
    """Kills build_edges_from_serialized__mutmut_26 (``and`` -> ``or``) and mutmut_32 (``target in known`` -> ``target not in known``)."""
    known = {"n1": object(), "n2": object()}
    serialized = {"edges": [{"source": "n1", "target": "missing"}]}
    assert build_edges_from_serialized(serialized, known) == []


def test_build_edges_skips_when_source_unknown() -> None:
    """Kills build_edges_from_serialized__mutmut_29 (``source in known`` -> ``source not in known``)."""
    known = {"n1": object(), "n2": object()}
    serialized = {"edges": [{"source": "missing", "target": "n2"}]}
    assert build_edges_from_serialized(serialized, known) == []


def test_persist_graph_writes_to_expected_path(tmp_path, monkeypatch) -> None:
    """Kills persist_graph__mutmut_1..12, mutmut_14, mutmut_17..25 (graphs_dir computation, makedirs, save_path, GraphStore.save)."""
    monkeypatch.chdir(tmp_path)
    saved: list = []
    monkeypatch.setattr(
        GraphStore,
        "save",
        lambda graph, path: saved.append((graph, path)),
    )
    graph = object()
    run_id = "run-abc"
    persist_graph(graph, run_id, 3)
    expected_dir = tmp_path / ".specmetrics" / "evidence_graphs"
    assert expected_dir.is_dir()
    assert saved == [(graph, str(expected_dir / f"{run_id}.jsonl"))]


def test_persist_graph_is_idempotent(tmp_path, monkeypatch) -> None:
    """Kills persist_graph__mutmut_13 (``exist_ok=None``), mutmut_15 (arg dropped), mutmut_16 (``exist_ok=False``)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(GraphStore, "save", lambda graph, path: None)
    persist_graph(object(), "r1", 0)
    persist_graph(object(), "r2", 0)
