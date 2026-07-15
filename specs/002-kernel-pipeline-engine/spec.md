# Feature Specification: Kernel & Pipeline Engine

**Feature Branch**: `002-kernel-pipeline-engine`

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F01 — Kernel & Pipeline Engine com base no 001-mvp-release-outline"

---

## User Scenarios & Testing

### User Story 1 — Execute a full measurement pipeline (Priority: P1)

A Functional Measurement Specialist runs `specmetrics measure` and the system
orchestrates all pipeline stages in the correct order — from loading the
specification repository to publishing the final result.

**Why this priority**: This is the core workflow the entire platform exists to
support. Without pipeline execution, no measurement is possible.

**Independent Test**: Can be tested by providing a known specification
repository, executing the pipeline, and verifying that each stage produces its
expected output in correct sequence.

**Acceptance Scenarios**:

1. **Given** a valid specification repository, **When** the pipeline starts,
   **Then** the RepositoryLoaded event is published first
2. **Given** the Specification Adapter finishes, **When** DocumentsDiscovered
   is published, **Then** Semantic Extraction begins processing
3. **Given** all configured plugins are available, **When** the pipeline
   executes, **Then** each pipeline stage is invoked exactly once in canonical
   order
4. **Given** a pipeline execution, **When** it completes successfully, **Then**
   the PipelineCompleted event is published and all output artifacts are
   available to the caller

---

### User Story 2 — Handle pipeline failures gracefully (Priority: P1)

A Tech Lead runs an invalid measurement and the system stops before producing
incorrect results, reporting a clear failure cause.

**Why this priority**: Users must never receive partial or incorrect
measurements. Fail-fast behavior is a pipeline invariant (SI-07).

**Independent Test**: Can be tested by injecting a failure in any stage and
verifying the pipeline halts before downstream stages execute.

**Acceptance Scenarios**:

1. **Given** a Specification Adapter that fails to discover documents,
   **When** the pipeline runs, **Then** an error is raised before Semantic
   Extraction starts
2. **Given** any stage raises an unrecoverable error, **When** the pipeline
   executes, **Then** the Pipeline Engine halts execution and reports the
   failure with the originating stage and error details
3. **Given** an interrupted pipeline, **When** the user inspects the result,
   **Then** no downstream stage has executed

---

### User Story 3 — Observe pipeline execution state (Priority: P2)

A Developer or AI Agent debugs a measurement execution by inspecting the
pipeline context — which events were published, which stages ran, and what
diagnostics were collected.

**Why this priority**: Traceability and debuggability are core principles (V,
VI). This enables audit and continuous improvement.

**Independent Test**: Can be tested by executing a pipeline and verifying the
pipeline context contains the correct sequence of published events and stage
completion markers.

**Acceptance Scenarios**:

1. **Given** a completed pipeline execution, **When** the user queries the
   pipeline context, **Then** it contains the complete sequence of published
   events
2. **Given** a pipeline execution, **When** diagnostics are collected, **Then**
   each stage's execution metadata (timing, status, outputs) is preserved in
   the pipeline context
3. **Given** multiple pipeline executions, **When** contexts are compared,
   **Then** each execution has a unique execution_id

---

### Edge Cases

- What happens when no plugins are installed? The pipeline should fail early
  at the stage where a required plugin is missing.
- What happens when an event handler throws an unexpected exception? The
  pipeline should capture the error, halt, and report which handler failed.
- What happens when the pipeline is triggered twice concurrently? The system
  should either queue or reject — no shared mutable state between executions.
- How does the system handle a stage that produces no output? The event for
  that stage should still be published, indicating completion with empty
  payload.

---

## Constitution Check

**Engaged Principles**:
- III (Semantic Before Structural) — Pipeline orchestrates semantic extraction
  before downstream processing
- IV (LLM-Assisted, Deterministic Results) — Pipeline ensures deterministic
  execution order; LLM involvement is isolated to the semantic extraction stage
- V (Evidence First) — Pipeline context preserves evidence throughout stages
- VII (Canonical Representation) — Pipeline enforces that downstream components
  receive only the CFM, never raw framework documents
- VIII (Plugin-Oriented) — Pipeline Engine is stage-agnostic; all stages are
  pluggable
- XIV (Layer Independence) — Pipeline Engine depends only on stable event
  contracts, never on implementation details of any stage

**Compliance Notes**: The Pipeline Engine owns execution lifecycle but does not
implement any stage logic. It communicates exclusively through immutable events.
Plugin isolation is ensured because stages never call each other directly.

---

## Requirements

### Functional Requirements

- **FR-001**: The Pipeline Engine MUST coordinate the execution of all pipeline
  stages in a predefined canonical order
- **FR-002**: The Pipeline Engine MUST publish an immutable domain event when
  each stage completes, containing the stage's output and execution metadata
- **FR-003**: Each pipeline execution MUST produce a unique Pipeline Context
  that accumulates execution state across all stages
- **FR-004**: The Pipeline Context MUST be immutable between stages — each event
  produces a new context version
- **FR-005**: The Pipeline Engine MUST resolve event handlers through a registry
  that maps each event type to its consuming component
- **FR-006**: The Pipeline Engine MUST halt execution and report an error if any
  stage fails or a required handler is not registered
- **FR-007**: The Event Bus MUST deliver events synchronously and in-order
  within a single pipeline execution
- **FR-008**: The Event Bus MUST NOT depend on external messaging
  infrastructure — it is an in-process component
- **FR-009**: The Pipeline Engine MUST accept pipeline start requests from both
  CLI and MCP interfaces through the Application Layer
- **FR-010**: The Pipeline Engine MUST support dynamic stage composition —
  adding or removing a stage does not require changes to the engine itself

### Key Entities

- **Pipeline Context**: Container for all execution state — includes
  execution_id, references to each stage's output (repository, adapter result,
  evidence graph, canonical model, measurement result, exported files),
  published events list, diagnostics, and execution metadata
- **Pipeline Event**: Immutable domain event with event type, publisher
  identity, payload, and timestamp. Each event type has a dedicated schema
- **Event Handler Registration**: Mapping from event type to the component
  responsible for processing that event and producing the next stage output
- **Execution ID**: Unique identifier for each pipeline run, enabling
  traceability and correlation across stages and output artifacts

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A specification repository with known content produces the same
  pipeline execution sequence across 10 consecutive runs (determinism)
- **SC-002**: A stage failure at any position in the pipeline halts execution
  within 1 second and reports the originating stage name to the caller
- **SC-003**: The pipeline context for any execution contains a complete,
  ordered event log with timestamps verifiable against actual execution order
- **SC-004**: A pipeline configured with only 2 stages runs successfully — the
  engine does not require all 9 stages to be present
- **SC-005**: Users receive pipeline completion or failure notification in
  under 5 seconds for typical specification repositories

---

## Assumptions

- The pipeline runs locally (no distributed execution)
- Pipeline stages are stateless — all state lives in the Pipeline Context
- The event registry is populated at startup by the Plugin Discovery mechanism
- Pipeline execution is single-threaded within one execution; concurrent
  executions produce independent contexts
- Error handling follows a fail-fast model — no retry logic at the pipeline
  level (retries are handled by individual stages if applicable)
- The canonical pipeline order matches Foundation §5: Repository → Adapter →
  Extraction → Evidence Graph → CFM → Rule Pack → Measurement → Export →
  Publish → Complete
