# Research Report: Evidence Graph Store

**Date**: 2026-07-15 | **Feature**: [spec.md](spec.md)

---

## 1. Graph Library: NetworkX

**Decision**: Use NetworkX for the in-memory graph representation.

**Rationale**: NetworkX is already referenced in the project tech stack (constitution §Architecture & Technology) and provides:
- Directed graph (`DiGraph`) with node/edge attributes — fits the Evidence Graph requirement of typed nodes and relationship edges
- Built-in traversal algorithms (BFS, DFS, shortest path) for provenance chain queries
- Serialization to JSON via `node_link_data()` / `node_link_graph()` — enables file persistence
- Mature, well-tested library with no external native dependencies

**Alternatives considered**:
- **Custom graph implementation**: Would require writing BFS/DFS, cycle detection, serialization from scratch. Not justified when the interface is abstracted (see §2).
- **iGraph**: Faster for large graphs but introduces a native dependency and heavier build. Overkill for 10k-node scale.
- **simple-graph (custom dict-of-dicts)**: Too minimal — no traversal algorithms, no serialization, no validation. Would require reimplementing everything NetworkX provides.

---

## 2. Interface Abstraction

**Decision**: Wrap NetworkX behind a `GraphBackend` Protocol to allow alternative implementations.

**Rationale**: The spec assumption states "the interface is abstracted to allow alternative implementations." This is consistent with the project's Protocol-based patterns (F02 `PluginRegistry`, F03 `SpecificationAdapter`, F04 `ExtractionProvider`). A lightweight Protocol with the minimum required operations (add_node, add_edge, query, traverse) keeps the core stable while allowing future backends (e.g., iGraph for large graphs, Neo4j for persistent queryable graphs).

**Required Protocol methods**:
- `add_node(node_id, attrs)` — Add a node with typed attributes
- `add_edge(source_id, target_id, attrs)` — Add a directed edge
- `get_node(node_id)` — Retrieve node by ID
- `query_nodes(filters)` — Query by type, document_id, etc.
- `traverse(start_id, direction)` — BFS/DFS traversal for provenance chains
- `to_serializable()` / `from_serializable(data)` — Convert to/from JSON-compatible structure

---

## 3. Persistence Format: JSON Lines

**Decision**: Use JSON Lines (JSONL) for persistence — one line per node or edge.

**Rationale**:
- Streaming write/read: No need to hold the full serialized graph in memory
- Append-friendly: Incremental updates append new node/edge records
- Human-readable: Each line is a valid JSON object, debuggable with standard tools
- Compact: No schema overhead, no database dependency

**Structure**:
```
{"type": "node", "id": "...", "node_type": "extracted_element", "attrs": {...}}
{"type": "edge", "source": "...", "target": "...", "edge_type": "derived_from", "attrs": {...}}
```

**Alternatives considered**:
- **Single JSON file**: Simple but requires loading entire graph to memory for serialization (defeats streaming for persistence). Both are viable at spec scale.
- **SQLite**: Adds a dependency, requires schema migrations, complicates the offline-capable constraint. Future option for large-scale deployments.
- **Pickle**: Python-specific, not human-readable, version-dependent. Violates Open by Default principle.

---

## 4. Node Identity Strategy

**Decision**: Use a composite fingerprint `(document_id, section_id, text_fragment_sha256, semantic_type)` as the canonical node identifier.

**Rationale**:
- Enables deterministic de-duplication (FR-009) without cross-run state
- Stable across pipeline runs — same document always produces same node IDs
- Allows incremental updates to identify which nodes to replace

**Alternatives considered**:
- **UUID4 per node**: Non-deterministic — same document produces different IDs across runs. Breaks incremental updates and determinism.
- **Auto-increment integers**: Simple but not stable across runs. Requires maintaining a sequence which complicates persistence.

---

## 5. Incremental Update Strategy

**Decision**: Document-scoped replacement — remove all nodes with matching `document_id`, then insert new nodes from the re-extracted document.

**Rationale**: The F04 ExtractionResult provides document-level granularity. This is the simplest correct approach that satisfies FR-008:
1. Query all nodes where `document_id == <target>`
2. Remove matching nodes and their edges
3. Insert new nodes and edges from the updated extraction result

This is O(n) in the number of nodes per document — acceptable at spec scale (typically <200 nodes per document).

---

## 6. Pipeline Stage Integration

**Decision**: Implement as a `PipelineEvent` handler registered for `EventType.SEMANTIC_EXTRACTION_COMPLETED`.

**Rationale**: Follows the same pattern as F04's `ExtractionStage`:
- `handled_event_type` → `EventType.SEMANTIC_EXTRACTION_COMPLETED`
- `handler_id` → `"evidence_graph_stage"`
- `stage_name` → `"evidence_graph"`
- `handle(event)` → consumes `ExtractionResult` payload, builds graph, updates `PipelineContext`, publishes `EVIDENCE_GRAPH_BUILT` event

Supports both full build (no existing graph) and incremental update (existing graph loaded from persistence).
