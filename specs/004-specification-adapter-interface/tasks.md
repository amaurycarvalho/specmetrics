---

description: "Task list for Specification Adapter Plugin Interface implementation"

---

# Tasks: Specification Adapter Plugin Interface

**Input**: Design documents from `specs/004-specification-adapter-interface/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature defines the contract for all SDD
framework adapters and requires verification of interface compliance, document
normalization, and F02 plugin integration.

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

**Purpose**: Project initialization for adapter interface infrastructure

- [X] T001 [P] Create `specmetrics/kernel/adapter_interface.py` —
  SpecificationAdapter Protocol, Document dataclass, DocumentSection dataclass
- [X] T002 [P] Create `specmetrics/kernel/adapter_registry.py` — AdapterRegistry
  class wrapping F02 PluginRegistry
- [X] T003 Update `specmetrics/kernel/__init__.py` — Export SpecificationAdapter,
  Document, DocumentSection, AdapterRegistry

**Checkpoint**: Adapter interface namespaces are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that MUST be complete before ANY user story can
be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] [US1] Create `Document` frozen dataclass in
  `specmetrics/kernel/adapter_interface.py` — id, path, document_type, content,
  metadata, sections per data-model.md
- [X] T005 [P] [US1] Create `DocumentSection` frozen dataclass in
  `specmetrics/kernel/adapter_interface.py` — id, title, level, content,
  subsections
- [X] T006 [US1] Create `SpecificationAdapter` Protocol in
  `specmetrics/kernel/adapter_interface.py` — scan() and supports() method
  signatures with pathlib.Path argument types

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Adapter discovers specification documents (Priority: P1) 🎯 MVP

**Goal**: A developer implements an adapter for a new SDD framework. They
implement the adapter interface, and the system discovers all specification
documents in a repository without needing to understand the framework's folder
conventions.

**Independent Test**: Can be tested by providing a mock repository with known
documents, running the adapter, and verifying that all documents are returned
with correct identifiers and metadata.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T007 [P] [US1] Test: A class implementing SpecificationAdapter Protocol
  passes isinstance check in `tests/unit/test_adapter_interface.py`
- [X] T008 [P] [US1] Test: A class missing scan() does NOT pass Protocol check
  in `tests/unit/test_adapter_interface.py`
- [X] T009 [P] [US1] Test: A class missing supports() does NOT pass Protocol
  check in `tests/unit/test_adapter_interface.py`
- [X] T010 [P] [US1] Test: Mock adapter scan() returns all discovered documents
  in `tests/unit/test_adapter_interface.py`
- [X] T011 [P] [US1] Test: Mock adapter returns empty list for empty repository
  in `tests/unit/test_adapter_interface.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement SpecificationAdapter Protocol in
  `specmetrics/kernel/adapter_interface.py` — structural typing with scan()
  and supports()
- [X] T013 [US1] Implement Document and DocumentSection frozen dataclasses in
  `specmetrics/kernel/adapter_interface.py`

**Checkpoint**: User Story 1 is complete — adapter interface is defined.

---

## Phase 4: User Story 2 — Adapter normalizes documents into canonical format (Priority: P1)

**Goal**: A specification document in any SDD framework format is transformed
into a framework-agnostic document representation that the pipeline can
consume.

**Independent Test**: Can be tested by providing a document in a specific
format and verifying the adapter returns a normalized Document with correct
id, path, type, and raw content fields.

### Tests for User Story 2

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T014 [P] [US2] Test: Document dataclass accepts valid field values
  in `tests/unit/test_adapter_interface.py`
- [X] T015 [P] [US2] Test: Document preserves metadata dict in
  `tests/unit/test_adapter_interface.py`
- [X] T016 [P] [US2] Test: DocumentSection stores hierarchy correctly
  (parent section with nested subsections) in
  `tests/unit/test_adapter_interface.py`
- [X] T017 [P] [US2] Test: Document with empty content is valid
  in `tests/unit/test_adapter_interface.py`
- [X] T018 [US2] Test: Mock adapter scan() returns Documents with correct
  path and type fields in `tests/unit/test_adapter_interface.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement file discovery logic — recursive glob for
  text files (*.md, *.yml, *.yaml) in scan() base implementation in
  `specmetrics/kernel/adapter_interface.py`
- [X] T020 [US2] Implement per-document error isolation — try/except for each
  file read, skip failures, log warning in
  `specmetrics/kernel/adapter_interface.py`
- [X] T021 [US2] Add document type inference helper — map parent directory
  names to canonical types in
  `specmetrics/kernel/adapter_interface.py`

**Checkpoint**: User Story 2 is complete — documents are normalized.

---

## Phase 5: User Story 3 — Adapter integrates with Plugin Registry (Priority: P1)

**Goal**: An adapter is packaged as a SpecMetrics plugin, discovered at
startup via F02, and made available to the pipeline through the registry.

**Independent Test**: Can be tested by packaging a mock adapter as a plugin,
starting the system, and verifying the adapter is registered and can be
retrieved by type.

### Tests for User Story 3

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T022 [P] [US3] Test: AdapterRegistry.list_adapters() returns all
  registered adapters in `tests/unit/test_adapter_registry.py`
- [X] T023 [P] [US3] Test: AdapterRegistry.find_adapter() returns correct
  adapter for a matching path in
  `tests/unit/test_adapter_registry.py`
- [X] T024 [P] [US3] Test: AdapterRegistry.find_adapter() returns None when
  no adapter supports the path in
  `tests/unit/test_adapter_registry.py`
- [X] T025 [P] [US3] Test: AdapterRegistry.scan_all() returns results from
  multiple adapters in `tests/unit/test_adapter_registry.py`
- [X] T026 [US3] Integration test: Mock adapter registered via F02 plugin
  mechanism is available through AdapterRegistry in
  `tests/integration/test_adapter_pipeline.py`
- [X] T027 [US3] Integration test: Adapter scan() output is consumable by
  PipelineEngine in `tests/integration/test_adapter_pipeline.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Create `AdapterRegistry` class in
  `specmetrics/kernel/adapter_registry.py` — wraps F02 PluginRegistry,
  provides find_adapter(), list_adapters(), scan_all()
- [X] T029 [US3] Implement find_adapter() — iterates registered adapters
  calling supports() on each, returns first match
- [X] T030 [US3] Implement scan_all() — runs scan() on all adapters that
  support the given path
- [X] T031 [US3] Update `specmetrics/kernel/__init__.py` — export
  AdapterRegistry

**Checkpoint**: User Story 3 is complete — adapters integrate with F02.

---

## Phase 6: User Story 4 — Multiple adapters coexist (Priority: P2)

**Goal**: An organization uses documents from multiple SDD frameworks. Each
framework has its own adapter, and the system selects the correct one for each
document.

**Independent Test**: Can be tested by installing two adapters for different
frameworks and verifying that each correctly handles its own document format.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T032 [P] [US4] Test: Two adapters registered, find_adapter() returns
  correct one for each path in `tests/unit/test_adapter_registry.py`
- [X] T033 [P] [US4] Test: scan_all() with two adapters returns combined
  results in `tests/unit/test_adapter_registry.py`
- [X] T034 [US4] Integration test: Two adapters coexist and each processes
  its own documents in `tests/integration/test_adapter_pipeline.py`

### Implementation for User Story 4

- [X] T035 [P] [US4] Ensure AdapterRegistry supports multiple adapters of
  same type — no deduplication by adapter id in
  `specmetrics/kernel/adapter_registry.py`
- [X] T036 [US4] Add adapter routing — find_adapter() tries adapters in
  registration order, returns first match

**Checkpoint**: User Story 4 is complete — multiple adapters coexist.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Add docstrings to all public adapter classes and methods
- [X] T038 Run quickstart.md validation scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (interface vs normalization)
  - US3 depends on US1 + F02 (registry needs adapter interface)
  - US4 depends on US3 (coexistence builds on registry)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational
- **User Story 2 (P1)**: Can start after Foundational — independent from US1
- **User Story 3 (P1)**: Depends on US1 + F02 (needs both to integrate)
- **User Story 4 (P2)**: Depends on US3 (needs registry for multiple adapters)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel
- US1 and US2 can proceed in parallel once Foundational is complete
- All tests within a story marked [P] can run in parallel
- Document and DocumentSection models can be built in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T007 [P] [US1] Test: Protocol check - valid adapter"
Task: "T008 [P] [US1] Test: Protocol check - missing scan()"
Task: "T009 [P] [US1] Test: Protocol check - missing supports()"
Task: "T010 [P] [US1] Test: Mock adapter scan() returns documents"
Task: "T011 [P] [US1] Test: Mock adapter empty repository"

# Launch implementation tasks in parallel:
Task: "T012 [P] [US1] Implement SpecificationAdapter Protocol"
Task: "T013 [US1] Implement Document and DocumentSection"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test adapter interface independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo
4. Add User Story 3 → Test independently → Demo (F02 integration)
5. Add User Story 4 → Test independently → Demo
6. Each story adds value without breaking previous stories

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

---

## Phase 8: Convergence

**Purpose**: Close gaps identified during convergence assessment between implemented code and specified intent.

- [X] T039 Create `tests/unit/test_adapter_interface.py`, `tests/unit/test_adapter_registry.py`, and `tests/integration/test_adapter_pipeline.py` with tests for Protocol compliance, document normalization, registry lookup, F02 integration, and multi-adapter coexistence per US1/US2/US3/US4 acceptance scenarios (missing)
- [X] T040 Add `supported_document_types` property to `SpecificationAdapter` Protocol in `specmetrics/kernel/adapter_interface.py` to expose supported document types as metadata accessible before scanning per FR-008 (missing)
