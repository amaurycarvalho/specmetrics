# Data Model: Evidence Graph Store

**Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
SemanticExtraction (F04)
    │
    ├── publishes SEMANTIC_EXTRACTION_COMPLETED event
    │   └── payload: ExtractionResult
    │
    ▼
EvidenceGraphStage (EventHandler)
    │
    ├── receives ExtractionResult
    ├── builds graph via GraphBackend
    │
    ▼
EvidenceGraph
    │
    ├── nodes: list[GraphNode]
    │   ├── type: "extracted_element"
    │   │   ├── fact
    │   │   ├── entity
    │   │   ├── relationship
    │   │   └── operation
    │   └── type: "evidence"
    │       └── source text fragment
    ├── edges: list[GraphEdge]
    │   ├── "derived_from" (element → evidence)
    │   ├── "references"  (element → element)
    │   └── "composed_of" (element → sub-element)
    │
    ▼
    ├── persisted via GraphStore (JSONL file)
    ├── queried via GraphQueryEngine
    │
    ▼
    └── published as EVIDENCE_GRAPH_BUILT event
        └── consumed by Canonical Functional Model (F06)
```

---

## EvidenceGraph

The root container for a single pipeline run's evidence graph.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | `str` | Yes | Unique identifier for this pipeline run |
| `nodes` | `dict[str, GraphNode]` | Yes | Map of node ID to GraphNode |
| `edges` | `list[GraphEdge]` | Yes | Directed edges connecting nodes |
| `metadata` | `GraphMetadata` | Yes | Processing statistics and provenance |

**Validation Rules**:
- `run_id` must be unique per pipeline execution
- Every edge `source` and `target` must reference an existing node ID
- Node IDs must be unique within the graph

---

## GraphNode

A single node in the evidence graph. Can represent either an extracted semantic element or an evidence text fragment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique node identifier (composite fingerprint) |
| `node_type` | `Literal["extracted_element", "evidence"]` | Yes | Type of node |
| `semantic_type` | `Literal["fact", "entity", "relationship", "operation"]` | No | Semantic type (only for `extracted_element` nodes) |
| `document_id` | `str` | Yes | Originating document identifier |
| `section_id` | `str` | No | Section identifier within the document |
| `text` | `str` | Yes | Evidence text fragment or element content |
| `confidence` | `float` | No | Confidence score (0.0–1.0, only for `extracted_element` nodes) |
| `element_id` | `str` | No | Original element ID from F04 extraction (only for `extracted_element` nodes) |

**Validation Rules**:
- `id` must be globally unique within the graph
- `node_type` must be one of the two defined types
- `semantic_type` must be present when `node_type` is `extracted_element`; must be absent when `node_type` is `evidence`
- `confidence` must be in range [0.0, 1.0] when present
- `document_id` must have a non-empty value

**Identity Strategy**: Node ID is a SHA-256 fingerprint of `(document_id, section_id, text, semantic_type)`. This ensures deterministic node identity across pipeline runs, enabling incremental updates and de-duplication.

---

## GraphEdge

A directed relationship between two GraphNodes.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `str` | Yes | Source node ID |
| `target` | `str` | Yes | Target node ID |
| `edge_type` | `Literal["derived_from", "references", "composed_of"]` | Yes | Semantic type of the relationship |
| `metadata` | `dict[str, Any]` | No | Additional edge attributes |

**Validation Rules**:
- `source` and `target` must reference existing node IDs in the graph
- `edge_type` must be one of the three defined types
- Self-loops (source == target) are not allowed

**Edge Type Semantics**:
- `derived_from`: An extracted element was derived from an evidence text fragment (element → evidence)
- `references`: An extracted element references another extracted element (element → element)
- `composed_of`: An extracted element is composed of sub-elements (parent → child)

---

## GraphMetadata

Processing statistics and provenance for the evidence graph.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | `str` | Yes | Pipeline run identifier |
| `node_count` | `int` | Yes | Total number of nodes in the graph |
| `edge_count` | `int` | Yes | Total number of edges in the graph |
| `documents_covered` | `list[str]` | Yes | Document IDs that contributed to this graph |
| `created_at` | `datetime` | Yes | Timestamp when the graph was built |
| `pipeline_version` | `str` | No | Version of the pipeline that produced this graph |

---

## GraphQueryEngine

Query interface for the evidence graph. Supports the following operations:

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_node` | `(node_id: str) -> GraphNode \| None` | Node or None | Retrieve a single node by ID |
| `query_by_document` | `(document_id: str) -> list[GraphNode]` | List of nodes | All nodes from a specific document |
| `query_by_type` | `(semantic_type: str) -> list[GraphNode]` | List of nodes | All nodes of a given semantic type |
| `query_by_evidence` | `(text_pattern: str) -> list[GraphNode]` | List of nodes | Nodes whose text matches a pattern |
| `traverse_provenance` | `(node_id: str, depth: int) -> list[GraphNode]` | Path of nodes | Provenance chain from a node back to evidence |
| `find_references` | `(node_id: str) -> list[GraphNode]` | Related nodes | Nodes that reference or are referenced by the given node |

**Behavioral Contracts**:
- All queries are read-only — they MUST NOT modify the graph
- Queries MUST complete within performance targets defined in spec Success Criteria
- Queries for non-existent node IDs MUST return empty results (not raise errors)
- `traverse_provenance` MUST follow `derived_from` edges in reverse direction (target → source)

---

## GraphStore (Persistence)

Persistence interface for save/load operations.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `save` | `(graph: EvidenceGraph, path: str) -> None` | None | Persist graph to file |
| `load` | `(path: str) -> EvidenceGraph` | EvidenceGraph | Load graph from file |
| `list_graphs` | `(directory: str) -> list[str]` | List of paths | List available persisted graphs |
| `delete` | `(path: str) -> None` | None | Delete a persisted graph |

**Storage Format**: JSON Lines (JSONL), one JSON object per line:
- Node records: `{"type": "node", "id": "...", "node_type": "...", ...}`
- Edge records: `{"type": "edge", "source": "...", "target": "...", "edge_type": "...", ...}`
- Metadata record: `{"type": "metadata", "run_id": "...", "node_count": ..., ...}` (first line)

**Behavioral Contracts**:
- `save` MUST be atomic — if writing fails, the file MUST NOT contain partial data
- `load` MUST validate that all edge references resolve to existing nodes
- `load` MUST raise a descriptive error if the file format is invalid or corrupted
- `list_graphs` MUST return only valid evidence graph files (not arbitrary JSONL files)

---

## EvidenceGraphStage (Pipeline Event Handler)

Structural interface for the pipeline stage.

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `handled_event_type` | Property | `EventType` | Returns `EventType.SEMANTIC_EXTRACTION_COMPLETED` |
| `handler_id` | Property | `str` | Returns `"evidence_graph_stage"` |
| `stage_name` | Property | `str` | Returns `"evidence_graph"` |
| `handle` | `(event: PipelineEvent) -> PipelineContext` | `PipelineContext` | Process the event, build/update graph, publish result |

**Behavioral Contracts**:
- `handle()` MUST NOT modify the input event payload
- `handle()` MUST be idempotent — same input + same existing graph → same output
- On first invocation (no existing graph), MUST perform a full build
- On subsequent invocations with a document-scoped change, MUST perform an incremental update
- MUST publish `EVIDENCE_GRAPH_BUILT` event with graph metadata on completion
