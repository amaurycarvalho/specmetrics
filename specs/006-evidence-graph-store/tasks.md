---

description: "Task list for Evidence Graph Store (F05) implementation"

---

# Tasks: Evidence Graph Store

**Input**: Design documents from `specs/006-evidence-graph-store/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature defines a new pipeline stage (4th in the measurement pipeline) and requires verification of graph construction correctness, query engine accuracy, persistence round-trips, and incremental update semantics.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/application/`,
  `specmetrics/sdk/`, `specmetrics/plugins/`,
  `specmetrics/cli/`, `specmetrics/mcp/`,
  `specmetrics/infrastructure/`, `specmetrics/tests/`
  at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create skeleton files for the evidence graph module

- [ ] T001 [P] Create `specmetrics/kernel/evidence_graph.py` — EvidenceGraph structure with NodeAlreadyExistsError, NodeNotFoundError, EdgeAlreadyExistsError, SelfLoopError, InvalidGraphDataError exception classes
- [ ] T002 [P] Create `specmetrics/kernel/graph_query_engine.py` — GraphQueryEngine skeleton class
- [ ] T003 [P] Create `specmetrics/kernel/graph_persistence.py` — GraphStore skeleton class
- [ ] T004 Create `specmetrics/kernel/evidence_graph_stage.py` — EvidenceGraphStage EventHandler skeleton (placeholder handle method)
- [ ] T005 Update `specmetrics/kernel/__init__.py` — Export all new classes

**Checkpoint**: Evidence graph module namespace is in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and graph backend that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 [P] [US1] Create `GraphNode` Pydantic model in `specmetrics/kernel/evidence_graph.py` — id, node_type (extracted_element/evidence), semantic_type (fact/entity/relationship/operation, optional), document_id, section_id (optional), text, confidence (optional), element_id (optional) per data-model.md
- [ ] T007 [P] [US1] Create `GraphEdge` Pydantic model in `specmetrics/kernel/evidence_graph.py` — source, target, edge_type (derived_from/references/composed_of), metadata (optional dict)
- [ ] T008 [P] [US1] Create `GraphMetadata` Pydantic model in `specmetrics/kernel/evidence_graph.py` — run_id, node_count, edge_count, documents_covered, created_at, pipeline_version (optional)
- [ ] T009 [P] [US1] Create `GraphBackend` Protocol in `specmetrics/kernel/evidence_graph.py` — add_node(), add_edge(), get_node(), query_nodes(), traverse(), to_serializable(), from_serializable() per contracts/graph-backend-protocol.md
- [ ] T010 [P] [US1] Create `EvidenceGraph` root model in `specmetrics/kernel/evidence_graph.py` — run_id, nodes (dict[str, GraphNode]), edges (list[GraphEdge]), metadata (GraphMetadata)
- [ ] T011 [US1] Implement `NetworkXBackend` in `specmetrics/kernel/evidence_graph.py` — wraps networkx.DiGraph, implements GraphBackend Protocol

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Build evidence graph from extracted semantic elements (Priority: P1) 🎯 MVP

**Goal**: A developer triggers the measurement pipeline. The EvidenceGraphStage receives ExtractionResult from Semantic Extraction (F04) and builds a traceable graph where each fact, entity, relationship, and operation is a node connected to its evidence references.

**Independent Test**: Can be tested by providing a known set of extracted semantic elements, running the evidence graph build stage, and verifying that every element appears as a graph node with correct evidence references and relationships.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T012 [P] [US1] Test: NetworkXBackend.add_node() stores node with correct attributes in `tests/unit/test_evidence_graph.py`
- [ ] T013 [P] [US1] Test: NetworkXBackend.add_node() raises NodeAlreadyExistsError for duplicate IDs in `tests/unit/test_evidence_graph.py`
- [ ] T014 [P] [US1] Test: NetworkXBackend.add_edge() raises NodeNotFoundError for missing source in `tests/unit/test_evidence_graph.py`
- [ ] T015 [P] [US1] Test: NetworkXBackend.add_edge() raises SelfLoopError for source==target in `tests/unit/test_evidence_graph.py`
- [ ] T016 [P] [US1] Test: NetworkXBackend.get_node() returns correct node attributes in `tests/unit/test_evidence_graph.py`
- [ ] T017 [P] [US1] Test: NetworkXBackend.get_node() returns None for non-existent ID in `tests/unit/test_evidence_graph.py`
- [ ] T018 [P] [US1] Test: NetworkXBackend.to_serializable() / from_serializable() round-trip preserves graph structure in `tests/unit/test_evidence_graph.py`
- [ ] T019 [US1] Test: Building graph from valid ExtractionResult produces correct node count and edge count in `tests/unit/test_evidence_graph.py`

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement NetworkXBackend in `specmetrics/kernel/evidence_graph.py` — add_node, add_edge, get_node, query_nodes, traverse, to_serializable, from_serializable with all validation rules from the contract
- [ ] T021 [P] [US1] Implement EvidenceGraph node identity fingerprint function — SHA-256 of (document_id, section_id, text, semantic_type) in `specmetrics/kernel/evidence_graph.py`
- [ ] T022 [US1] Implement EvidenceGraphStage.handle() — receives ExtractionResult, creates graph nodes for each ExtractedElement and EvidenceReference, links via derived_from edges, deduplicates by fingerprint, populates GraphMetadata in `specmetrics/kernel/evidence_graph_stage.py`

**Checkpoint**: User Story 1 is complete — evidence graph can be built from extraction results.

---

## Phase 4: User Story 2 — Query the evidence graph by document, element type, or provenance (Priority: P1)

**Goal**: An analyst inspects a measurement result and queries the evidence graph to find all facts from a document section, all entities of a type, or trace a provenance chain back to source text.

**Independent Test**: Can be tested by building a known graph, executing queries against it, and verifying returned nodes match expectations.

### Tests for User Story 2

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T023 [P] [US2] Test: query_by_document returns all and only nodes from the specified document in `tests/unit/test_graph_query_engine.py`
- [ ] T024 [P] [US2] Test: query_by_type returns nodes of the correct semantic type in `tests/unit/test_graph_query_engine.py`
- [ ] T025 [P] [US2] Test: query_by_evidence matches text fragments correctly in `tests/unit/test_graph_query_engine.py`
- [ ] T026 [P] [US2] Test: traverse_provenance traces from element back through evidence chain in `tests/unit/test_graph_query_engine.py`
- [ ] T027 [P] [US2] Test: traverse_provenance with max_depth stops at correct depth in `tests/unit/test_graph_query_engine.py`
- [ ] T028 [P] [US2] Test: traverse_provenance handles cyclic graphs without infinite loops in `tests/unit/test_graph_query_engine.py`
- [ ] T029 [US2] Test: find_references returns both forward and backward related nodes in `tests/unit/test_graph_query_engine.py`

### Implementation for User Story 2

- [ ] T030 [P] [US2] Implement GraphQueryEngine.query_by_document() in `specmetrics/kernel/graph_query_engine.py` — queries nodes by document_id using GraphBackend.query_nodes()
- [ ] T031 [P] [US2] Implement GraphQueryEngine.query_by_type() in `specmetrics/kernel/graph_query_engine.py` — queries nodes by semantic_type
- [ ] T032 [P] [US2] Implement GraphQueryEngine.query_by_evidence() in `specmetrics/kernel/graph_query_engine.py` — substring match on node text field
- [ ] T033 [P] [US2] Implement GraphQueryEngine.traverse_provenance() in `specmetrics/kernel/graph_query_engine.py` — reverse traversal over derived_from edges, returns ordered path
- [ ] T034 [P] [US2] Implement GraphQueryEngine.find_references() in `specmetrics/kernel/graph_query_engine.py` — finds nodes with edges to/from the given node
- [ ] T035 [US2] Wire GraphQueryEngine into EvidenceGraphStage — expose query methods on the stage output in `specmetrics/kernel/evidence_graph_stage.py`

**Checkpoint**: User Story 2 is complete — evidence graph is fully queryable.

---

## Phase 5: User Story 3 — Evidence graph persists and survives pipeline restarts (Priority: P2)

**Goal**: A team runs the measurement pipeline daily. The evidence graph produced by each run is persisted so analysts can compare results, audit measurements, and track changes over time.

**Independent Test**: Can be tested by running the pipeline to produce a graph, persisting it, restarting the system, loading the persisted graph, and verifying all nodes and edges are intact.

### Tests for User Story 3

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T036 [P] [US3] Test: JSONL save writes metadata, nodes, and edges in correct format in `tests/unit/test_graph_persistence.py`
- [ ] T037 [P] [US3] Test: JSONL load reconstructs identical graph with all nodes and edges in `tests/unit/test_graph_persistence.py`
- [ ] T038 [P] [US3] Test: Loading corrupted JSONL file raises InvalidGraphDataError in `tests/unit/test_graph_persistence.py`
- [ ] T039 [P] [US3] Test: list_graphs returns only valid graph files in `tests/unit/test_graph_persistence.py`
- [ ] T040 [P] [US3] Test: Save is atomic — interruption leaves no partial file in `tests/unit/test_graph_persistence.py`
- [ ] T041 [P] [US3] Test: GraphStore round-trip produces node-for-node, edge-for-edge identical graph in `tests/unit/test_graph_persistence.py`

### Implementation for User Story 3

- [ ] T042 [P] [US3] Implement GraphStore.save() in `specmetrics/kernel/graph_persistence.py` — serializes EvidenceGraph to JSONL, writes to temporary file then atomic rename
- [ ] T043 [P] [US3] Implement GraphStore.load() in `specmetrics/kernel/graph_persistence.py` — reads JSONL, reconstructs EvidenceGraph, validates all edge references resolve
- [ ] T044 [P] [US3] Implement GraphStore.list_graphs() in `specmetrics/kernel/graph_persistence.py` — scans directory for valid graph files
- [ ] T045 [P] [US3] Implement GraphStore.delete() in `specmetrics/kernel/graph_persistence.py` — removes a persisted graph file
- [ ] T046 [US3] Integrate persistence into EvidenceGraphStage — auto-save after build in `specmetrics/kernel/evidence_graph_stage.py`

**Checkpoint**: User Story 3 is complete — evidence graph is persistable and reloadable.

---

## Phase 6: User Story 4 — Graph supports incremental updates (Priority: P3)

**Goal**: A developer modifies a single specification document. Rather than rebuilding the entire graph, the pipeline updates only the affected subgraph, preserving all unchanged evidence from previous runs.

**Independent Test**: Can be tested by building an initial graph, removing one document's contributions, running incremental update, and verifying the graph no longer contains elements from the removed document while all other elements remain.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T047 [P] [US4] Test: Incremental update replaces nodes from specified document in `tests/unit/test_evidence_graph.py`
- [ ] T048 [P] [US4] Test: Incremental update preserves nodes from other documents in `tests/unit/test_evidence_graph.py`
- [ ] T049 [P] [US4] Test: Incremental update with empty replacement removes all nodes for that document in `tests/unit/test_evidence_graph.py`
- [ ] T050 [US4] Integration test: Full pipeline with incremental update produces correct graph state in `tests/integration/test_evidence_graph_pipeline.py`

### Implementation for User Story 4

- [ ] T051 [P] [US4] Implement EvidenceGraphStage.update_for_document() in `specmetrics/kernel/evidence_graph_stage.py` — removes nodes by document_id, inserts new nodes from updated extraction
- [ ] T052 [US4] Implement incremental update mode in EvidenceGraphStage.handle() — detect if graph exists, route to full build vs incremental update, auto-save after update in `specmetrics/kernel/evidence_graph_stage.py`

**Checkpoint**: User Story 4 is complete — evidence graph supports incremental document-level updates.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T053 [P] Add docstrings to all public evidence graph classes and methods
- [ ] T054 Run quickstart.md validation scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (build) and US2 (query) can proceed in parallel once Foundational is done
  - US3 (persistence) depends on US1 (needs graph construction logic)
  - US4 (incremental updates) depends on US3 (needs persistence to detect existing graph)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — builds graph from ExtractionResult
- **User Story 2 (P1)**: Can start after Foundational — independent from US1 (queries via GraphBackend interface)
- **User Story 3 (P2)**: Depends on US1 (needs EvidenceGraph to persist)
- **User Story 4 (P3)**: Depends on US1 + US3 (needs graph construction and persistence for incremental mode)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002, T003 can run in parallel
- T006–T011 (data models and Protocol) can run in parallel
- US1 (build) and US2 (query) can proceed in parallel once Foundational is complete
- All tests within a story marked [P] can be written in parallel
- GraphQueryEngine methods (T030–T034) can each be implemented independently

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T012 [P] [US1] Test: add_node stores attributes"
Task: "T013 [P] [US1] Test: add_node raises on duplicate"
Task: "T014 [P] [US1] Test: add_edge raises on missing source"
Task: "T015 [P] [US1] Test: add_edge raises self-loop"
Task: "T016 [P] [US1] Test: get_node returns attributes"
Task: "T017 [P] [US1] Test: get_node returns None"
Task: "T018 [P] [US1] Test: serialization round-trip"
Task: "T019 [US1] Test: build from ExtractionResult"

# Launch implementation tasks in parallel:
Task: "T020 [P] [US1] Implement NetworkXBackend"
Task: "T021 [P] [US1] Implement fingerprint function"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (build graph)
4. **STOP and VALIDATE**: Test graph build independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Build graph from extraction (MVP!)
3. Add User Story 2 → Test independently → Query the evidence graph
4. Add User Story 3 → Test independently → Persist and reload graphs
5. Add User Story 4 → Test independently → Incremental document updates
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
