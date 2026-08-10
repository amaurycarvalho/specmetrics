"""Tests for specmetrics.kernel.evidence_graph_stage."""

from __future__ import annotations

import datetime as dt

import structlog

from specmetrics.kernel import evidence_graph_stage as stage_module
from specmetrics.kernel.events import EventType, PipelineEvent
from specmetrics.kernel.evidence_graph import (
    GraphNode,
    NodeAlreadyExistsError,
    fingerprint_node,
)
from specmetrics.kernel.evidence_graph_backend import NetworkXBackend
from specmetrics.kernel.evidence_graph_stage import EvidenceGraphStage
from specmetrics.kernel.extraction_provider import ExtractedElement
from specmetrics.kernel.pipeline_context import PipelineContext


class FakeBackend:
    """In-memory GraphBackend double used to isolate the stage from networkx."""

    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []

    def add_node(self, node_id: str, attrs: dict) -> None:
        if node_id in self.nodes:
            raise NodeAlreadyExistsError(node_id)
        self.nodes[node_id] = dict(attrs)

    def add_edge(self, source: str, target: str, attrs: dict) -> None:
        if not isinstance(source, str) or not isinstance(target, str):
            raise TypeError("invalid edge endpoints")
        if not isinstance(attrs, dict):
            raise TypeError("invalid edge attrs")
        self.edges.append(
            {"source": source, "target": target, "edge_type": attrs.get("edge_type")}
        )

    def get_node(self, node_id: str) -> dict | None:
        if node_id in self.nodes:
            return {"id": node_id, **self.nodes[node_id]}
        return None

    def query_nodes(self, filters: dict) -> list[dict]:
        return [
            {"id": nid, **data}
            for nid, data in self.nodes.items()
            if all(data.get(k) == v for k, v in filters.items())
        ]

    def to_serializable(self) -> dict:
        return {
            "nodes": [{"id": nid, **data} for nid, data in self.nodes.items()],
            "edges": list(self.edges),
        }

    def from_serializable(self, data: dict) -> None:
        pass

    def remove_node(self, node_id: str) -> None:
        self.nodes.pop(node_id, None)

    def traverse(self, start_id: str, direction: str, max_depth: int) -> list[list[dict]]:
        return []


class _IdLessBackend(FakeBackend):
    """Backend whose query_nodes does not inject an 'id' key."""

    def query_nodes(self, filters: dict) -> list[dict]:
        return [dict(data) for data in self.nodes.values()]


class _EdgeFailBackend(FakeBackend):
    """Backend whose add_edge always fails."""

    def add_edge(self, source: str, target: str, attrs: dict) -> None:
        raise RuntimeError("edge failure")


def test_add_element_nodes_edge_failure_zero_count():
    """Kills EvidenceGraphStage::_add_element_nodes__mutmut_61 (edge_added 0 -> 1)."""
    stage = _stage(_EdgeFailBackend())
    result = stage._add_element_nodes(_element())
    assert result == (2, 0)


def test_build_payload_semantic_type_flows():
    """Kills EvidenceGraphStage::_build_payload__mutmut_27/28/29
    (semantic_type get variants)."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node(
        "n1",
        {
            "node_type": "extracted_element",
            "semantic_type": "fact",
            "document_id": "d",
            "text": "t",
        },
    )
    payload = stage._build_payload("r", 1, 0, set())
    assert payload["nodes"][0]["semantic_type"] == "fact"


def _element(
    element_id: str = "e1",
    doc: str = "docA",
    section: str | None = "s1",
    text: str = "hello",
    content: str = "hello",
    type_: str = "fact",
) -> ExtractedElement:
    return ExtractedElement(
        id=element_id,
        type=type_,
        confidence=0.9,
        evidence=_evidence(doc, section, text),
        content=content,
    )


def _evidence(
    doc: str, section: str | None, text: str
) -> dict[str, str | None]:
    evidence = {"document_id": doc, "text": text}
    if section is not None:
        evidence["section_id"] = section
    return evidence


def _element_data(
    element_id: str = "e1",
    doc: str = "docA",
    section: str | None = "s1",
    text: str = "hello",
    content: str = "hello",
    type_: str = "fact",
) -> dict:
    return {
        "id": element_id,
        "type": type_,
        "confidence": 0.9,
        "evidence": _evidence(doc, section, text),
        "content": content,
    }


def _stage(backend=None) -> EvidenceGraphStage:
    return EvidenceGraphStage(backend=backend or FakeBackend())


def test_default_max_memory_nodes():
    """Kills EvidenceGraphStage::__init____mutmut_1 (50_000 -> 50001)."""
    stage = EvidenceGraphStage(backend=FakeBackend())
    assert stage._max_memory_nodes == 50_000


def test_custom_max_memory_nodes():
    """Verifies the constructor accepts an explicit threshold."""
    stage = EvidenceGraphStage(backend=FakeBackend(), max_memory_nodes=10)
    assert stage._max_memory_nodes == 10


def test_default_backend_is_networkx():
    """Verifies a NetworkXBackend is created when none is provided."""
    stage = EvidenceGraphStage()
    assert isinstance(stage._backend, NetworkXBackend)


def test_handled_event_type():
    """Kills EvidenceGraphStage::__init____mutmut_5 (_handled_event_type -> None)."""
    assert _stage().handled_event_type == EventType.SEMANTIC_EXTRACTION_COMPLETED


def test_handler_id():
    """Kills EvidenceGraphStage::__init____mutmut_6/7/8 (handler_id literal)."""
    assert _stage().handler_id == "evidence_graph_stage"


def test_stage_name():
    """Kills EvidenceGraphStage::__init____mutmut_9/10/11 (stage_name literal)."""
    assert _stage().stage_name == "evidence_graph"


def test_insert_elements_counts():
    """Kills EvidenceGraphStage::_insert_elements__mutmut_26 (node_count = delta)
    and __mutmut_28/29 (edge_count)."""
    backend = FakeBackend()
    stage = _stage(backend)
    data = {
        "docA": {"elements": [_element_data("a", text="one"), _element_data("b", text="two")]}
    }
    node_count, edge_count, docs = stage._insert_elements(data)
    assert node_count == 4
    assert edge_count == 2
    assert docs == {"docA"}
    assert len(backend.nodes) == 4
    assert len(backend.edges) == 2


def test_insert_elements_multiple_documents():
    """Verifies docs_covered aggregates across documents."""
    stage = _stage()
    data = {
        "docA": {"elements": [_element_data(doc="docA")]},
        "docB": {"elements": [_element_data(doc="docB")]},
    }
    _, _, docs = stage._insert_elements(data)
    assert docs == {"docA", "docB"}


def test_insert_elements_valid_element_no_broken_log():
    """Kills EvidenceGraphStage::_insert_elements__mutmut_14 (or -> document_id or)
    and __mutmut_15 (or -> not document_id or text)."""
    stage = _stage()
    with structlog.testing.capture_logs() as logs:
        stage._insert_elements({"docA": {"elements": [_element_data()]}})
    assert all("broken_evidence_reference" not in log["event"] for log in logs)


def test_add_element_nodes_returns_counts():
    """Kills EvidenceGraphStage::_add_element_nodes__mutmut_11 (added 0 -> 1),
    __mutmut_34 (+= 1 -> += 2), __mutmut_57 (added = 1), __mutmut_59 (+= 2),
    __mutmut_60 (edge_added 0 -> None) and __mutmut_73 (edge_added 1 -> 2)."""
    backend = FakeBackend()
    stage = _stage(backend)
    element = _element()
    result = stage._add_element_nodes(element)
    assert result == (2, 1)
    assert len(backend.nodes) == 2
    assert len(backend.edges) == 1


def test_add_element_nodes_edge_attrs():
    """Kills EvidenceGraphStage::_add_element_nodes__mutmut_62/63/64/65/66/67
    (add_edge call variants) and __mutmut_68/69 (edge_type literal)."""
    backend = FakeBackend()
    stage = _stage(backend)
    element = _element()
    assert stage._add_element_nodes(element) == (2, 1)
    edge = backend.edges[0]
    assert edge["source"] == fingerprint_node("docA", "s1", "hello", "fact")
    assert edge["target"] == fingerprint_node("docA", "s1", "hello", None)
    assert edge["edge_type"] == "derived_from"


def test_add_element_nodes_duplicate_element_nodes():
    """Verifies duplicate nodes do not increment counts."""
    backend = FakeBackend()
    stage = _stage(backend)
    element = _element()
    stage._add_element_nodes(element)
    assert stage._add_element_nodes(element) == (0, 1)


def test_build_payload_node_fields():
    """Kills EvidenceGraphStage::_build_payload__mutmut_3/4/5/6/7/8/9 (id lookup)
    and __mutmut_16/17/18/19/20/21/22/23/24 (node_type),
    __mutmut_25/26/27/28/29 (semantic_type), __mutmut_30/31/32/33/34
    (document_id), __mutmut_35/36/37/38/39 (section_id) and
    __mutmut_40/41/43/44/45 (text lookup)."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node(
        "n1",
        {
            "node_type": "evidence",
            "semantic_type": None,
            "document_id": "docA",
            "section_id": "s1",
            "text": "sample text",
        },
    )
    payload = stage._build_payload("run1", 1, 0, {"docA"})
    assert payload["run_id"] == "run1"
    assert payload["node_count"] == 1
    assert payload["edge_count"] == 0
    assert payload["documents_covered"] == ["docA"]
    assert payload["nodes"] == [
        {
            "id": "n1",
            "node_type": "evidence",
            "semantic_type": None,
            "document_id": "docA",
            "section_id": "s1",
            "text": "sample text",
        }
    ]


def test_build_payload_truncates_text():
    """Kills EvidenceGraphStage::_build_payload__mutmut_42 (truncate_text(None))."""
    backend = FakeBackend()
    stage = _stage(backend)
    long_text = "x" * 500
    stage._backend.add_node(
        "n1", {"node_type": "evidence", "document_id": "d", "text": long_text}
    )
    payload = stage._build_payload("r", 1, 0, set())
    assert payload["nodes"][0]["text"] == "x" * 200


def test_build_payload_skips_node_without_id():
    """Kills EvidenceGraphStage::_build_payload__mutmut_10 (default '' -> 'XXXX')."""
    backend = _IdLessBackend()
    stage = _stage(backend)
    backend.nodes["no-id"] = {"node_type": "evidence", "text": "x"}
    payload = stage._build_payload("r", 0, 0, set())
    assert payload["nodes"] == []


def test_build_payload_continues_past_missing_id():
    """Kills EvidenceGraphStage::_build_payload__mutmut_12 (continue -> break)."""
    backend = _IdLessBackend()
    stage = _stage(backend)
    backend.nodes["no-id"] = {"node_type": "evidence", "text": "x"}
    backend.nodes["n1"] = {"id": "n1", "node_type": "evidence", "text": "t"}
    payload = stage._build_payload("r", 0, 0, set())
    assert [node["id"] for node in payload["nodes"]] == ["n1"]


def test_build_payload_missing_optional_fields():
    """Verifies missing optional node attributes serialize as None/empty."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node("n1", {"node_type": "evidence", "text": "t"})
    payload = stage._build_payload("r", 1, 0, set())
    node = payload["nodes"][0]
    assert node["node_type"] == "evidence"
    assert node["semantic_type"] is None
    assert node["document_id"] is None
    assert node["section_id"] is None


def test_build_payload_empty_node_type():
    """Kills EvidenceGraphStage::_build_payload__mutmut_18/19/20/21/22/23/24
    (node_type get variants)."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node("n1", {"text": "t"})
    payload = stage._build_payload("r", 1, 0, set())
    assert payload["nodes"][0]["node_type"] == ""


def test_load_graph_nodes_valid():
    """Kills EvidenceGraphStage::_load_graph_nodes__mutmut_2 (dropped 0 -> None),
    __mutmut_3 (dropped 0 -> 1), __mutmut_5/6/7/8/9/10/11/12 (id lookup),
    __mutmut_15/16/17/18 (attrs filter) and __mutmut_20/21/22 (GraphNode call)."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node(
        "n1",
        {
            "node_type": "evidence",
            "semantic_type": None,
            "document_id": "docA",
            "section_id": "s1",
            "text": "hello",
        },
    )
    graph_nodes, dropped = stage._load_graph_nodes()
    assert dropped == 0
    assert "n1" in graph_nodes
    node = graph_nodes["n1"]
    assert isinstance(node, GraphNode)
    assert node.id == "n1"
    assert node.node_type == "evidence"
    assert node.document_id == "docA"
    assert node.section_id == "s1"
    assert node.text == "hello"


def test_load_graph_nodes_skips_without_id():
    """Kills EvidenceGraphStage::_load_graph_nodes__mutmut_14 (continue -> break)."""
    backend = _IdLessBackend()
    stage = _stage(backend)
    backend.nodes["no-id"] = {"node_type": "evidence", "text": "x"}
    backend.nodes["n1"] = {
        "id": "n1",
        "node_type": "evidence",
        "document_id": "d",
        "text": "t",
    }
    graph_nodes, dropped = stage._load_graph_nodes()
    assert list(graph_nodes.keys()) == ["n1"]
    assert dropped == 0


def test_load_graph_nodes_drops_invalid():
    """Kills EvidenceGraphStage::_load_graph_nodes__mutmut_23 (dropped = 1),
    __mutmut_24 (dropped -= 1) and __mutmut_25 (dropped += 2)."""
    backend = FakeBackend()
    stage = _stage(backend)
    stage._backend.add_node("bad1", {"node_type": "bogus", "text": "x"})
    stage._backend.add_node("bad2", {"node_type": "evidence", "document_id": "d"})
    graph_nodes, dropped = stage._load_graph_nodes()
    assert dropped == 2
    assert graph_nodes == {}


def test_handle_builds_payload_and_context(monkeypatch):
    """Exercises the full handle flow including metadata and stage output."""
    backend = FakeBackend()
    stage = _stage(backend)
    monkeypatch.setattr(stage_module, "persist_graph", lambda *a, **k: None)
    context = PipelineContext(
        extraction_result={
            "results": {
                "docB": {"elements": [_element_data("a", doc="docB")]},
                "docA": {"elements": [_element_data("b", doc="docA")]},
            }
        }
    )
    event = PipelineEvent(
        event_type=EventType.SEMANTIC_EXTRACTION_COMPLETED,
        publisher="some_other_stage",
        payload={},
        context=context,
        timestamp=dt.datetime(2024, 1, 2, 3, 4, 5, tzinfo=dt.UTC),
    )
    result = stage.handle(event)
    assert result.evidence_graph["run_id"] == str(int(event.timestamp.timestamp()))
    assert result.evidence_graph["node_count"] == 4
    assert result.evidence_graph["edge_count"] == 2
    assert result.evidence_graph["documents_covered"] == ["docA", "docB"]
    assert len(result.evidence_graph["nodes"]) == 4


def test_handle_memory_threshold_warning(monkeypatch):
    """Verifies the memory threshold warning fires above the limit."""
    backend = FakeBackend()
    stage = EvidenceGraphStage(backend=backend, max_memory_nodes=1)
    monkeypatch.setattr(stage_module, "persist_graph", lambda *a, **k: None)
    context = PipelineContext(extraction_result={"results": {"d": {"elements": [_element_data()]}}})
    event = PipelineEvent(
        event_type=EventType.SEMANTIC_EXTRACTION_COMPLETED,
        publisher="x",
        payload={},
        context=context,
    )
    with structlog.testing.capture_logs() as logs:
        stage.handle(event)
    assert any(
        log["event"] == "evidence_graph_exceeded_memory_threshold" for log in logs
    )
