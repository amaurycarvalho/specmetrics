# Feature Specification: Evidence Graph Store

**Feature Branch**: `006-evidence-graph-store`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F05"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Build evidence graph from extracted semantic elements (Priority: P1)

A developer triggers the measurement pipeline. After the Semantic Extraction stage completes, the Evidence Graph stage receives the extracted elements and builds a traceable graph where each fact, entity, relationship, and operation is a node connected to its evidence references. The graph preserves the full provenance from extraction through to final measurement.

**Why this priority**: This is the foundational stage that enables Principle V (Evidence First). Without the evidence graph, no fact can be traced back to its source, and downstream measurement cannot be audited or trusted.

**Independent Test**: Can be fully tested by providing a known set of extracted semantic elements, running the evidence graph build stage, and verifying that every element appears as a graph node with correct evidence references and relationships.

**Acceptance Scenarios**:

1. **Given** a set of extracted elements containing facts, entities, and relationships, **When** the evidence graph is built, **Then** each element is represented as a node with a unique identifier and its originating evidence reference.
2. **Given** two elements that reference overlapping evidence text from the same document, **When** the graph is built, **Then** both nodes share an evidence node with a single reference to the source document and text fragment.
3. **Given** an empty extraction result (no elements), **When** the evidence graph is built, **Then** an empty graph is produced and the stage completes without error.

---

### User Story 2 - Query the evidence graph by document, element type, or provenance (Priority: P1)

An analyst inspects a measurement result and needs to understand how a specific measurement was derived. They query the evidence graph to find all facts originating from a particular document section, or all entities of a given type, and trace each one back to its source text.

**Why this priority**: Without queryability, the evidence graph is a black box. Principle VI (Explainability by Design) requires that every measurement be explainable through the evidence that supports it.

**Independent Test**: Can be tested by building a known graph, executing queries against it, and verifying the returned nodes match expectations.

**Acceptance Scenarios**:

1. **Given** an evidence graph with elements from three documents, **When** the analyst queries by a specific document ID, **Then** all and only the elements from that document are returned.
2. **Given** an evidence graph with facts, entities, and relationships, **When** the analyst queries by semantic type (e.g., "fact"), **Then** only elements of that type are returned.
3. **Given** an evidence graph where element A was derived from element B, **When** the analyst queries the provenance chain of A, **Then** the path from A back to the source evidence is returned.

---

### User Story 3 - Evidence graph persists and survives pipeline restarts (Priority: P2)

A team runs the measurement pipeline daily. The evidence graph produced by each run must be persisted so that analysts can compare results across runs, audit historical measurements, and track changes in functional size over time.

**Why this priority**: Principle XI (Observability as a Native Capability) requires continuous visibility into measurements. Historical comparison is essential for engineering analytics.

**Independent Test**: Can be tested by running the pipeline to produce a graph, persisting it, restarting the system, loading the persisted graph, and verifying all nodes and edges are intact.

**Acceptance Scenarios**:

1. **Given** a persisted evidence graph from a previous pipeline run, **When** the system restarts and loads the graph, **Then** all nodes, edges, and evidence references from the previous run are available for query.
2. **Given** two pipeline runs on the same repository, **When** both graphs are persisted, **Then** each graph is independently queryable and identifiable by run timestamp or run ID.

---

### User Story 4 - Graph supports incremental updates (Priority: P3)

A developer modifies a single specification document. Rather than re-extracting and rebuilding the entire graph, the pipeline identifies the affected documents and updates only the relevant subgraph, preserving all unchanged evidence from previous runs.

**Why this priority**: Incremental updates reduce pipeline execution time for frequent, small changes — enabling continuous measurement workflows.

**Independent Test**: Can be tested by building an initial graph, removing one document's contributions, running incremental update, and verifying the graph no longer contains elements from the removed document while all other elements remain.

**Acceptance Scenarios**:

1. **Given** an existing evidence graph built from five documents, **When** one document is re-extracted with new elements, **Then** the graph is updated with only the new elements replacing the previous ones from that document — all other elements remain unchanged.
2. **Given** an existing graph built from five documents, **When** one document is removed from the repository, **Then** the graph removes only elements originating from that document.

---

### Edge Cases

- What happens when an extracted element has a broken evidence reference (document ID or section ID that no longer exists)? The element is still added to the graph with a warning flag indicating the reference could not be resolved — the pipeline continues.
- How does the system handle duplicate elements (identical type and evidence reference from the same document)? Duplicate detection de-duplicates based on a fingerprint of (document ID, section ID, text fragment, semantic type) — only the first occurrence is stored, subsequent duplicates are logged.
- What happens when the graph exceeds available memory for in-memory storage? The graph engine should support a configurable spill-to-disk strategy or a persistent backend option.
- How does the system handle concurrent pipeline runs writing to the same graph store? If persistence is file-based, concurrent writes use a locking mechanism. If database-backed, standard transaction isolation applies. The default recommendation is one graph per run identified by run ID.

## Constitution Check *(mandatory)*

**Engaged Principles**: I (Specification First), II (Specification as a Measurable Asset), V (Evidence First), VI (Explainability by Design), VII (Canonical Representation), XI (Observability as a Native Capability), XIV (Layer Independence)

**Compliance Notes**:
- Specification First (I): The evidence graph consumes ExtractedElements produced from specifications — it never reads source code or implementation artifacts.
- Specification as a Measurable Asset (II): The evidence graph transforms raw extracted elements into a structured, queryable asset that enables measurement, auditing, and analytics — reifying the spec-as-asset principle.
- Evidence First (V): Every graph node maintains its evidence reference. No element exists in the graph without traceable provenance. Evidence is stored as a first-class node type in the graph.
- Explainability by Design (VI): The graph supports provenance queries that explain any measurement by tracing it back through facts, entities, and evidence to the original specification text.
- Canonical Representation (VII): The evidence graph uses a canonical node and edge model. Downstream consumers (Canonical Functional Model) interact with this model — never with framework-specific extraction formats.
- Observability as a Native Capability (XI): Persisted graphs enable historical comparison, trend analysis, and audit trails — making functional measurement an observable engineering telemetry stream.
- Layer Independence (XIV): The Evidence Graph stage consumes ExtractionResult from the Semantic Extraction layer and produces an EvidenceGraph consumed by the Canonical Functional Model layer — no direct coupling between layers.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The evidence graph stage MUST accept an ExtractionResult (as produced by F04 — Semantic Extraction) and produce a directed graph where nodes represent extracted elements and edges represent relationships between them.
- **FR-002**: Each graph node MUST include: a unique identifier, a semantic type (fact, entity, relationship, operation), the originating document ID, and the evidence text fragment.
- **FR-003**: The graph MUST support nodes of type "evidence" that represent source text fragments, with edges from extracted elements to their supporting evidence nodes.
- **FR-004**: The graph MUST support querying by: document ID, semantic type, evidence text match, and relationship traversal (e.g., "all facts derived from entity X").
- **FR-005**: The graph MUST support provenance queries that trace any element back through its evidence chain to the original source document and text.
- **FR-006**: The evidence graph MUST be persistable to disk and reloadable — the storage format MUST preserve all nodes, edges, and metadata without loss.
- **FR-007**: Each persisted graph MUST be identified by a unique run identifier (run ID or timestamp) to support multiple historical graphs.
- **FR-008**: The graph MUST support incremental update by document — replacing all nodes originating from a given document without rebuilding the entire graph.
- **FR-009**: The graph MUST detect and de-duplicate elements with identical (document ID, section ID, text fragment, semantic type) fingerprints — only the first is stored.
- **FR-010**: Graph operations (build, query, persist, load) MUST NOT modify the input ExtractionResult — the extraction output is immutable per the pipeline invariant.
- **FR-011**: The graph stage MUST emit a structured event (EvidenceGraphBuilt) upon completion, containing the graph metadata (node count, edge count, documents covered, run ID) for downstream subscribers.

### Key Entities *(include if feature involves data)*

- **EvidenceGraph**: A directed graph data structure containing nodes and edges that represent extracted semantic elements and their provenance relationships. Identified by a unique run ID.
- **GraphNode**: A node in the evidence graph. Can be an ExtractedElement (fact, entity, relationship, operation) or an EvidenceReference (source text fragment). Contains type, identifier, and provenance metadata.
- **GraphEdge**: A directed relationship between two GraphNodes. Represents semantic connections (e.g., "derived from", "references", "composed of") with optional metadata.
- **ProvenanceChain**: A traversal path through the graph from a measurement result back through facts, entities, and evidence references to the original specification text.
- **GraphStore**: The persistence mechanism for EvidenceGraph. Supports save, load, list (available graphs), and delete operations. May be file-based or database-backed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An evidence graph built from 1,000 extracted elements with 500 relationship edges completes building in under 5 seconds on a standard development machine.
- **SC-002**: A query for all elements from a specific document containing 50 elements returns results in under 100 milliseconds.
- **SC-003**: A provenance chain query tracing a measurement result through 10 levels of derivation returns the complete chain in under 500 milliseconds.
- **SC-004**: A persisted evidence graph of 10,000 nodes is saved to disk and reloaded in under 10 seconds total (save + load).
- **SC-005**: Incremental update replacing 100 nodes from a single document completes in under 2 seconds, regardless of total graph size.
- **SC-006**: Rebuilding the graph from the same ExtractionResult twice produces identical graphs (node-for-node, edge-for-edge equality).

## Assumptions

- The ExtractionResult from F04 (Semantic Extraction) is the sole input to this stage — no additional text or document access is needed.
- The graph is primarily an in-memory structure with optional persistence — the default deployment uses file-based serialization (JSON/JSONL) for simplicity.
- Existing plugin discovery mechanism (F02) is not required for this stage — the graph engine is a core component of the measurement pipeline, not a plugin extension point.
- The Canonical Functional Model layer (F06) defines the final schema for downstream consumption; this spec defines an intermediate graph structure that F06 may transform further.
- NetworkX is the reference graph library for the in-memory representation — the interface is abstracted to allow alternative implementations.
- Incremental updates require the input ExtractionResult to include document-level granularity (which elements came from which document) — this is produced by F04.
