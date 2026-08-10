from __future__ import annotations

from specmetrics.kernel.cfm._entities import (
    _build_actor,
    _build_business_rule,
    _build_data_group,
    _build_functional_processes,
    _build_operation,
    _extract_relationship_endpoints,
    _fp_evidence,
    _group_by_document,
    _infer_operation_direction,
    _infer_semantic_marker,
)
from specmetrics.kernel.cfm.model import (
    EvidenceRef,
    Operation,
)
from specmetrics.kernel.evidence_graph import (
    EvidenceGraph,
    GraphEdge,
    GraphMetadata,
    GraphNode,
)


def _evidence(document_id: str = "doc1") -> EvidenceRef:
    return EvidenceRef(graph_node_id="g1", document_id=document_id, text="t")


def _node() -> GraphNode:
    return GraphNode(
        id="n1",
        node_type="extracted_element",
        semantic_type="fact",
        document_id="doc1",
        text="the text",
    )


class _OpStub:
    def __init__(self, evidence: object | None) -> None:
        self.evidence = evidence


class _NoEvidence:
    evidence = None


def test_infer_operation_direction_defaults_to_input() -> None:
    """Kills _infer_operation_direction__mutmut_2/3 (``return "input"`` literal)."""
    assert _infer_operation_direction("plain text without any pattern") == "input"


def test_infer_operation_direction_matches_pattern() -> None:
    """Kills _infer_operation_direction__mutmut_1 (pattern search)."""
    assert _infer_operation_direction("Precondition **GIVEN** state") == "input"
    assert _infer_operation_direction("Result **THEN** output") == "output"
    assert _infer_operation_direction("#### Scenario: first") == "query"


def test_infer_semantic_marker_matches_section_pattern() -> None:
    """Kills _infer_semantic_marker__mutmut_6/7/8/9 (lower-casing and membership checks)."""
    result = _infer_semantic_marker(
        "actor",
        "user story",
        [({"actor"}, {"User Story"}, "actor_marker")],
        {"actor": "fallback"},
    )
    assert result == "actor_marker"


def test_infer_semantic_marker_uses_fallback_map() -> None:
    """Kills _infer_semantic_marker__mutmut_10/11/13 (fallback.get key/default)."""
    result = _infer_semantic_marker(
        "actor",
        None,
        [({"actor"}, {"User Story"}, "m")],
        {"actor": "custom_fallback"},
    )
    assert result == "custom_fallback"


def test_infer_semantic_marker_unknown_category_default() -> None:
    """Kills _infer_semantic_marker__mutmut_14/15 (``"operational_feature"`` literal)."""
    assert _infer_semantic_marker("unknown_cat", None) == "operational_feature"


def test_build_actor_sets_semantic_marker() -> None:
    """Kills _build_actor__mutmut_8 (metadata arg) and mutmut_15/16/17 (infer args)."""
    actor = _build_actor(
        "a1",
        _node(),
        "Actor",
        _evidence(),
        "User Story",
        [({"actor"}, {"User Story"}, "actor_marker")],
        {"actor": "actor_fallback"},
    )
    assert actor.metadata["semantic_marker"] == "actor_marker"


def test_build_actor_uses_fallback_when_no_marker_match() -> None:
    """Kills _build_actor__mutmut_18 (fallback_map arg deletion)."""
    actor = _build_actor(
        "a1",
        _node(),
        "Actor",
        _evidence(),
        "Other Section",
        [({"actor"}, {"User Story"}, "actor_marker")],
        {"actor": "actor_fallback"},
    )
    assert actor.metadata["semantic_marker"] == "actor_fallback"


def test_build_business_rule_description_and_marker() -> None:
    """Kills _build_business_rule__mutmut_8 (description arg) and mutmut_10 (metadata arg), mutmut_17/18/19 (infer args)."""
    rule = _build_business_rule(
        "br1",
        _node(),
        "Rule",
        _evidence(),
        "User Story",
        [({"business_rule"}, {"User Story"}, "br_marker")],
        {"business_rule": "br_fallback"},
    )
    assert rule.description == "the text"
    assert rule.metadata["semantic_marker"] == "br_marker"


def test_build_business_rule_uses_fallback_when_no_marker_match() -> None:
    """Kills _build_business_rule__mutmut_20 (fallback_map arg deletion)."""
    rule = _build_business_rule(
        "br1",
        _node(),
        "Rule",
        _evidence(),
        "Other Section",
        [({"business_rule"}, {"User Story"}, "br_marker")],
        {"business_rule": "br_fallback"},
    )
    assert rule.metadata["semantic_marker"] == "br_fallback"


def test_build_data_group_sets_semantic_marker() -> None:
    """Kills _build_data_group__mutmut_8 (metadata arg) and mutmut_15/16/17 (infer args)."""
    group = _build_data_group(
        "dg1",
        _node(),
        "Group",
        _evidence(),
        "Data Model",
        [({"data_group"}, {"Data Model"}, "dg_marker")],
        {"data_group": "dg_fallback"},
    )
    assert group.metadata["semantic_marker"] == "dg_marker"


def test_build_data_group_uses_fallback_when_no_marker_match() -> None:
    """Kills _build_data_group__mutmut_18 (fallback_map arg deletion)."""
    group = _build_data_group(
        "dg1",
        _node(),
        "Group",
        _evidence(),
        "Other Section",
        [({"data_group"}, {"Data Model"}, "dg_marker")],
        {"data_group": "dg_fallback"},
    )
    assert group.metadata["semantic_marker"] == "dg_fallback"


def test_build_operation_metadata_and_fields() -> None:
    """Kills _build_operation__mutmut_10 (description arg), mutmut_12 (metadata arg), mutmut_13 (parent_process_id), mutmut_23/24/25 (infer args)."""
    operation = _build_operation(
        "op1",
        _node(),
        "Op",
        _evidence(),
        "Functional Requirements",
        [({"operation"}, {"Functional Requirements"}, "op_marker")],
        {"operation": "op_fallback"},
    )
    assert operation.description == "the text"
    assert operation.parent_process_id == ""
    assert operation.metadata["direction"] == "input"
    assert operation.metadata["semantic_marker"] == "op_marker"


def test_build_operation_uses_fallback_when_no_marker_match() -> None:
    """Kills _build_operation__mutmut_26 (fallback_map arg deletion)."""
    operation = _build_operation(
        "op1",
        _node(),
        "Op",
        _evidence(),
        "Other Section",
        [({"operation"}, {"Functional Requirements"}, "op_marker")],
        {"operation": "op_fallback"},
    )
    assert operation.metadata["semantic_marker"] == "op_fallback"


def test_group_by_document_uses_evidence_document_id() -> None:
    """Kills _group_by_document__mutmut_2 (``doc_id = None``)."""
    item = _OpStub(_evidence(document_id="docX"))
    grouped = _group_by_document([("a1", item)])
    assert grouped == {"docX": [("a1", item)]}


def test_group_by_document_unknown_for_missing_evidence() -> None:
    """Kills _group_by_document__mutmut_3/4 (``"unknown"`` literal)."""
    item = _NoEvidence()
    grouped = _group_by_document([("a1", item)])
    assert grouped == {"unknown": [("a1", item)]}


def test_fp_evidence_reuses_operation_evidence() -> None:
    """Kills _fp_evidence__mutmut_5..11 (fallback EvidenceRef construction is skipped when evidence exists)."""
    operation = Operation(id="op1", name="Op", parent_process_id="", evidence=_evidence())
    assert _fp_evidence("fp1", "doc1", [("op1", operation)]) is operation.evidence


def test_fp_evidence_builds_ref_without_operation_evidence() -> None:
    """Kills _fp_evidence__mutmut_5 (graph_node_id=None), mutmut_6 (document_id=None), mutmut_7 (text=None), mutmut_8/9/10 (arg deletions), mutmut_11 (text literal)."""
    ev = _fp_evidence("fp1", "doc1", [("op1", _OpStub(None))])
    assert ev.graph_node_id == "fp1"
    assert ev.document_id == "doc1"
    assert ev.text == ""


def test_build_functional_processes_empty_input() -> None:
    """Kills _build_functional_processes__mutmut_1 (``if not operations`` -> ``if operations``)."""
    assert _build_functional_processes({}, {}, {}) == {}


def test_build_functional_processes_groups_by_document() -> None:
    """Kills _build_functional_processes__mutmut_1, mutmut_19 (data_groups_by_doc key), mutmut_24 (actors_by_doc key), mutmut_37/38/39 (arg deletions)."""
    ops = {"op1": _OpStub(_evidence("doc1"))}
    dgs = {"dg1": _OpStub(_evidence("doc1"))}
    actors = {"act1": _OpStub(_evidence("doc1"))}
    fps = _build_functional_processes(ops, dgs, actors)
    assert set(fps) == {"fp_doc1"}
    fp = fps["fp_doc1"]
    assert fp.operation_ids == ["op1"]
    assert fp.data_group_ids == ["dg1"]
    assert fp.actor_ids == ["act1"]


def test_build_functional_processes_evidence_ref_without_op_evidence() -> None:
    """Kills _build_functional_processes__mutmut_12/13 (None substituted _fp_evidence args)."""
    ops = {"op1": _OpStub(None)}
    fps = _build_functional_processes(ops, {}, {})
    fp = fps["fp_unknown"]
    assert fp.evidence.graph_node_id == "fp_unknown"
    assert fp.evidence.document_id == "unknown"
    assert fp.evidence.text == ""


def _graph_with_edges(*edges: GraphEdge) -> EvidenceGraph:
    return EvidenceGraph(
        run_id="r",
        nodes={"a": _node(), "b": GraphNode(id="b", node_type="extracted_element", semantic_type="fact", document_id="doc1", text="t"), "c": GraphNode(id="c", node_type="extracted_element", semantic_type="fact", document_id="doc1", text="t")},
        edges=list(edges),
        metadata=GraphMetadata(run_id="r", node_count=3, edge_count=len(edges), documents_covered=["doc1"]),
    )


def test_extract_relationship_endpoints_outgoing() -> None:
    """Kills _extract_relationship_endpoints__mutmut_2 (``source ==`` -> ``source !=``) and mutmut_3 (``target !=`` -> ``target ==``)."""
    graph = _graph_with_edges(GraphEdge(source="a", target="b", edge_type="references"))
    assert _extract_relationship_endpoints("a", graph) == ("a", "b")


def test_extract_relationship_endpoints_incoming() -> None:
    """Kills _extract_relationship_endpoints__mutmut_5 (``target ==`` -> ``target !=``) and mutmut_6 (``source !=`` -> ``source ==``)."""
    graph = _graph_with_edges(GraphEdge(source="b", target="a", edge_type="references"))
    assert _extract_relationship_endpoints("a", graph) == ("b", "a")


def test_extract_relationship_endpoints_none_for_self_loop() -> None:
    """Kills _extract_relationship_endpoints__mutmut_1/4 (``and`` -> ``or``) and mutmut_7/8 (return literals)."""
    graph = _graph_with_edges(GraphEdge(source="a", target="a", edge_type="references"))
    assert _extract_relationship_endpoints("a", graph) == ("", "")
