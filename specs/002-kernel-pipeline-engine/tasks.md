---

description: "Task list for Kernel & Pipeline Engine implementation"

---

# Tasks: Kernel & Pipeline Engine

**Input**: Design documents from `specs/002-kernel-pipeline-engine/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature is the core orchestration layer and
requires verification of determinism, ordering, and failure handling.

**Organization**: Tasks are grouped by user story to enable independent
implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/application/`,
  `specmetrics/sdk/`, `specmetrics/plugins/`, `specmetrics/cli/`,
  `specmetrics/mcp/`, `specmetrics/infrastructure/`, `specmetrics/tests/`
  at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create `specmetrics/kernel/` and `specmetrics/application/` package
  directories with `__init__.py`
- [X] T002 [P] Create `specmetrics/kernel/events.py` — EventType enum with all
  11 canonical event types
- [X] T003 [P] Create `specmetrics/kernel/exceptions.py` — StageError,
  PipelineError, HandlerNotFoundError exception classes
- [X] T004 [P] Create `tests/unit/` and `tests/integration/` package directories
  with `__init__.py`
- [X] T005 [P] Add `structlog` to project dependencies in `pyproject.toml`

**Checkpoint**: Basic project structure is in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that MUST be complete before ANY user story can
be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] [US1] Create `specmetrics/kernel/pipeline_context.py` —
  PipelineContext dataclass (frozen) with execution_id, all stage output fields
  as Optional, published_events tuple, diagnostics, and metadata
- [X] T007 [P] [US1] Create `specmetrics/kernel/events.py` — PipelineEvent base
  dataclass (frozen) with event_type, publisher, payload, context, timestamp
- [X] T008 [P] [US1] Create `specmetrics/kernel/handler_registry.py` —
  HandlerRegistry class with register() and resolve() methods, mapping
  EventType → EventHandler
- [X] T009 [P] [US1] Create `specmetrics/kernel/diagnostics.py` — Diagnostics,
  StageTiming, StageError, ExecutionMetadata dataclasses per data-model.md
- [X] T010 Create `specmetrics/kernel/__init__.py` — Re-export all public types
  (PipelineContext, PipelineEvent, EventType, EventHandler, StageError)

**Checkpoint**: Foundation ready — user story implementation can now begin in
parallel.

---

## Phase 3: User Story 1 — Execute a full measurement pipeline (Priority: P1) 🎯 MVP

**Goal**: A Functional Measurement Specialist runs `specmetrics measure` and
the system orchestrates all pipeline stages in the correct canonical order.

**Independent Test**: Provide mock handlers for 2–3 stages, execute the
pipeline, and verify events are published in canonical order with correct
payloads.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Test: PipelineEngine publishes RepositoryLoaded as first
  event in `tests/unit/test_pipeline_engine.py`
- [X] T012 [P] [US1] Test: PipelineEngine invokes handlers in canonical event
  order in `tests/unit/test_pipeline_engine.py`
- [X] T013 [P] [US1] Test: PipelineEngine returns PipelineCompleted event on
  success in `tests/unit/test_pipeline_engine.py`
- [X] T014 [P] [US1] Test: EventBus delivers events synchronously and in-order
  in `tests/unit/test_event_bus.py`
- [X] T015 [P] [US1] Test: EventBus raises error for unregistered event type in
  `tests/unit/test_event_bus.py`
- [X] T016 [P] [US1] Test: PipelineContext is immutable — with_stage_output
  returns new instance in `tests/unit/test_pipeline_context.py`
- [X] T017 [US1] Integration test: Pipeline with 2 mock stages executes in
  correct order in `tests/integration/test_pipeline_execution.py`

### Implementation for User Story 1

- [X] T018 [P] [US1] Create `specmetrics/kernel/event_bus.py` — EventBus class
  with publish(event) method, synchronous in-order delivery to registered
  handler
- [X] T019 [US1] Create `specmetrics/kernel/pipeline_engine.py` —
  PipelineEngine class with run(context) method, orchestrating the canonical
  event sequence: RepositoryLoaded → DocumentsDiscovered →
  SemanticExtractionCompleted → EvidenceGraphBuilt → CanonicalModelBuilt →
  RulePackApplied → MeasurementCompleted → ExportCompleted →
  TelemetryPublished → PipelineCompleted
- [X] T020 [US1] Add `with_stage_output()` builder method to PipelineContext
  in `specmetrics/kernel/pipeline_context.py`
- [X] T021 [US1] Add logging (structlog) for each stage transition in
  `specmetrics/kernel/pipeline_engine.py`
- [X] T022 [US1] Add PipelineEngine.run() to kernel `__init__.py` public API

**Checkpoint**: User Story 1 is complete — pipeline executes end-to-end with
mock handlers.

---

## Phase 4: User Story 2 — Handle pipeline failures gracefully (Priority: P1)

**Goal**: A Tech Lead runs an invalid measurement and the system stops before
producing incorrect results, reporting a clear failure cause.

**Independent Test**: Register a handler that raises StageError, execute the
pipeline, and verify PIPELINE_FAILED is published with the originating stage
name and error message. No downstream handlers execute.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T023 [P] [US2] Test: StageError in any handler halts pipeline immediately
  in `tests/unit/test_pipeline_engine.py`
- [X] T024 [P] [US2] Test: PIPELINE_FAILED event contains failed_stage and
  error_message in `tests/unit/test_pipeline_engine.py`
- [X] T025 [P] [US2] Test: Unregistered handler raises HandlerNotFoundError at
  resolution time in `tests/unit/test_handler_registry.py`
- [X] T026 [US2] Integration test: Pipeline with failing stage halts before
  downstream stages in `tests/integration/test_pipeline_execution.py`

### Implementation for User Story 2

- [X] T027 [US2] Add fail-fast error handling to PipelineEngine.run() — catch
  StageError, publish PIPELINE_FAILED, halt execution in
  `specmetrics/kernel/pipeline_engine.py`
- [X] T028 [US2] Add validation in HandlerRegistry.resolve() — raise
  HandlerNotFoundError if no handler registered for event_type in
  `specmetrics/kernel/handler_registry.py`
- [X] T029 [US2] Add edge case: no plugins installed → PipelineEngine.run()
  fails with descriptive error about missing handlers in
  `specmetrics/kernel/pipeline_engine.py`
- [X] T030 [US2] Add edge case: concurrent pipeline executions produce
  independent PipelineContext instances in
  `specmetrics/kernel/pipeline_engine.py`

**Checkpoint**: User Stories 1 AND 2 both work — pipeline handles failures
correctly.

---

## Phase 5: User Story 3 — Observe pipeline execution state (Priority: P2)

**Goal**: A Developer or AI Agent debugs a measurement execution by inspecting
the pipeline context — which events were published, which stages ran, and what
diagnostics were collected.

**Independent Test**: Execute a pipeline, then inspect the PipelineContext.
Verify published_events contains all events in order, diagnostics has per-stage
timing entries, and each execution has a unique execution_id.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T031 [P] [US3] Test: PipelineContext.published_events contains all events
  in publication order in `tests/unit/test_pipeline_context.py`
- [X] T032 [P] [US3] Test: Diagnostics records started_at, completed_at, and
  status for each stage in `tests/unit/test_pipeline_engine.py`
- [X] T033 [P] [US3] Test: Each execution produces unique execution_id (UUID v4)
  in `tests/unit/test_pipeline_engine.py`
- [X] T034 [US3] Integration test: Full pipeline context inspection after
  execution in `tests/integration/test_pipeline_execution.py`

### Implementation for User Story 3

- [X] T035 [P] [US3] Add execution_id generation (UUID v4) to PipelineEngine
  startup in `specmetrics/kernel/pipeline_engine.py`
- [X] T036 [US3] Add diagnostics collection — capture started_at, completed_at,
  duration_ms, status per stage in PipelineEngine in
  `specmetrics/kernel/pipeline_engine.py`
- [X] T037 [US3] Append each published event to PipelineContext.published_events
  tuple in `specmetrics/kernel/pipeline_engine.py`
- [X] T038 [US3] Add StageError capture to diagnostics.errors list on failure
  in `specmetrics/kernel/pipeline_engine.py`

**Checkpoint**: All user stories are now independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Add docstrings to all public kernel classes and methods
- [X] T040 Run quickstart.md validation scenarios end-to-end

---

## Phase 7: Convergence

**Purpose**: Close gaps between specification/plan intent and current implementation

- [X] T041 Fix `_STAGE_NAME_TO_EVENT` off-by-one mapping in `orchestrator.py` — each StageName currently maps to the wrong EventType (e.g. `CFM→EVIDENCE_GRAPH_BUILT` instead of `CANONICAL_MODEL_BUILT`, `MEASURE→RULE_PACK_APPLIED` instead of `MEASUREMENT_COMPLETED`) per plan: stage mapping (contradicts)
- [X] T042 Add `run_id` field to `PipelineResult` in `models.py` and populate it from `PipelineContext.execution_id` — `mcp/tools/measure.py` accesses `result.run_id` which would raise `AttributeError` at runtime per FR-009 (missing)
- [X] T043 Review/justify or remove `DOCUMENTS_VALIDATED` from `CANONICAL_EVENT_ORDER` and `EventType` enum — this event is not specified in the spec's canonical pipeline order or the plan's event sequence per spec: canonical order (unrequested)
- [X] T044 Add test verifying that a non-`StageError` exception (e.g. `ValueError`) raised by a handler is wrapped into `StageError` and the pipeline halts correctly per spec: edge cases — unexpected handler exceptions (partial)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user
  stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (different concerns: orchestration vs.
    error handling)
  - US3 depends on US1 (needs pipeline execution working to observe state)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on
  other stories
- **User Story 2 (P1)**: Can start after Foundational — Independent from US1
  (adds error handling to engine, can be implemented simultaneously)
- **User Story 3 (P2)**: Depends on US1 — US3 adds observability on top of
  working pipeline execution

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Once Foundational completes, US1 and US2 can start in parallel
- All tests within a story marked [P] can run in parallel
- Core data models (PipelineContext, PipelineEvent, HandlerRegistry,
  Diagnostics) can be built in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test pipeline execution independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo
4. Add User Story 3 → Test independently → Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 3 (sequential dependency)
   - Developer B: User Story 2
3. Stories complete and integrate independently at checkpoint phases

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break
  independence
