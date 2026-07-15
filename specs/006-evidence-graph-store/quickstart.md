# Quickstart: Evidence Graph Store

## Prerequisites

- Python 3.13+
- Dependencies installed (`pytest`, `networkx`)
- F01 (Kernel & Pipeline Engine) implemented and tested
- F04 (Semantic Extraction) implemented and tested — produces `ExtractionResult` as input
- Test virtualenv activated

## Setup

```bash
source .venv/bin/activate
```

## Validation Scenarios

### Scenario 1: Graph Backend Protocol Compliance

```bash
pytest tests/unit/test_evidence_graph.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `NetworkXBackend` implements all required Protocol methods
- Nodes can be added, retrieved, and queried
- Edges enforce source/target existence and reject self-loops
- Traversal produces correct provenance chains
- Serialization round-trips preserve graph structure

### Scenario 2: Evidence Graph Build from Extraction Result

```bash
pytest tests/unit/test_evidence_graph.py -v -k test_build
```

**Expected outcome**: All tests pass. Verifies that:
- A valid `ExtractionResult` produces a graph with correct node and edge counts
- Each `ExtractedElement` becomes a graph node with `node_type="extracted_element"`
- Each `EvidenceReference` becomes a graph node with `node_type="evidence"`
- An edge of type `derived_from` connects each element to its evidence
- Duplicate elements (same fingerprint) are de-duplicated
- Empty extraction result produces an empty graph (no error)

### Scenario 3: Query Engine

```bash
pytest tests/unit/test_graph_query_engine.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `query_by_document` returns all and only nodes from the specified document
- `query_by_type` returns nodes of the correct semantic type
- `traverse_provenance` traces from an element back through evidence chain
- `find_references` returns related nodes correctly
- Queries for non-existent IDs return empty results

### Scenario 4: Persistence Round-Trip

```bash
pytest tests/unit/test_graph_persistence.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- A graph saved to JSONL can be loaded back with identical nodes and edges
- Metadata record is correctly written and read
- Loading a corrupted file raises a descriptive error
- `list_graphs` finds only valid graph files
- Save is atomic (partial writes do not produce valid files)

### Scenario 5: Incremental Update

```bash
pytest tests/unit/test_evidence_graph.py -v -k test_incremental
```

**Expected outcome**: All tests pass. Verifies that:
- Replacing nodes from a specific document removes old nodes and inserts new ones
- Nodes from other documents remain unchanged
- Empty replacement (document has no elements) removes all nodes for that document

### Scenario 6: Pipeline Integration

```bash
pytest tests/integration/test_evidence_graph_pipeline.py -v
```

**Expected outcome**: All tests pass. Verifies that:
- `EvidenceGraphStage` registers as an `EventHandler` for `SEMANTIC_EXTRACTION_COMPLETED`
- Stage produces an `EVIDENCE_GRAPH_BUILT` event with correct metadata
- Graph metadata contains correct node/edge counts and document list
- Pipeline continues correctly after evidence graph stage

### Scenario 7: All Tests

```bash
pytest tests/
```

**Expected outcome**: All previous F01, F02, F03, and F04 tests pass — no regressions.

## Contracts Reference

- [Graph Backend Protocol](contracts/graph-backend-protocol.md) — How graph backends must be structured

## Data Model Reference

- [Data Model](data-model.md) — EvidenceGraph, GraphNode, GraphEdge, GraphQueryEngine, GraphStore definitions
