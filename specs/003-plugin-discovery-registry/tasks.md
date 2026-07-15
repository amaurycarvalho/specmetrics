---

description: "Task list for Plugin Discovery & Registry implementation"

---

# Tasks: Plugin Discovery & Registry

**Input**: Design documents from `specs/003-plugin-discovery-registry/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature enables all plugin-based extension
points and requires verification of discovery, validation, registry operations,
and error isolation.

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

**Purpose**: Project initialization for plugin infrastructure

- [ ] T001 [P] Create `specmetrics/kernel/plugin_metadata.py` — PluginMetadata
  frozen dataclass, PluginType enum, PluginStatus enum per data-model.md
- [ ] T002 [P] Add `PluginError` exception to `specmetrics/kernel/exceptions.py`
  for plugin-related failures
- [ ] T003 Update `specmetrics/kernel/__init__.py` — Export PluginMetadata,
  PluginType, PluginStatus, PluginError, PluginRegistry, PluginDiscovery

**Checkpoint**: Plugin infrastructure namespaces are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models that MUST be complete before ANY user story can
be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] [US1] Create `specmetrics/kernel/plugin_metadata.py` —
  PluginMetadata frozen dataclass with id, api_version, plugin_type,
  handled_event_types, handler_factory, name, description, author, version
- [ ] T005 [P] [US1] Create `specmetrics/kernel/plugin_metadata.py` — PluginType
  enum (ADAPTER, SEMANTIC, MEASUREMENT, EXPORTER, PUBLISHER, UNSPECIFIED)
- [ ] T006 [P] [US1] Create `specmetrics/kernel/plugin_metadata.py` —
  PluginStatus enum (PENDING, REGISTERED, REJECTED, SKIPPED)
- [ ] T007 [P] [US1] Create `specmetrics/kernel/plugin_registry.py` —
  PluginDescriptor dataclass with metadata, entry_point_name, status,
  validation_errors

**Checkpoint**: Foundation ready — user story implementation can now begin in
parallel.

---

## Phase 3: User Story 1 — Automatic plugin discovery at startup (Priority: P1) 🎯 MVP

**Goal**: A developer installs a SpecMetrics plugin via pip and the system
automatically discovers it on next startup — no manual registration required.

**Independent Test**: Can be tested by installing a mock plugin package that
declares a SpecMetrics entry point, starting the system, and verifying the
plugin appears in the registry.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T008 [P] [US1] Test: PluginDiscovery scans `specmetrics.plugins` entry
  points and returns discovered metadata in `tests/unit/test_plugin_discovery.py`
- [ ] T009 [P] [US1] Test: PluginDiscovery handles empty discovery (no plugins
  installed) without errors in `tests/unit/test_plugin_discovery.py`
- [ ] T010 [P] [US1] Test: PluginDiscovery loads factory function and retrieves
  PluginMetadata in `tests/unit/test_plugin_discovery.py`
- [ ] T011 [P] [US1] Test: PluginDiscovery discovers multiple plugins and returns
  all of them in `tests/unit/test_plugin_discovery.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create `specmetrics/kernel/plugin_discovery.py` —
  PluginDiscovery class with scan() method using importlib.metadata.entry_points
  for the `specmetrics.plugins` group
- [ ] T013 [US1] Add factory function loading — PluginDiscovery.load() imports
  the entry point target and calls it to obtain PluginMetadata
- [ ] T014 [US1] Add `__init__.py` re-export for PluginDiscovery and its
  public methods

**Checkpoint**: User Story 1 is complete — plugins are discovered automatically.

---

## Phase 4: User Story 2 — Plugin compatibility validation (Priority: P1)

**Goal**: A developer installs a plugin built for an incompatible API version
and the system reports the incompatibility clearly, preventing runtime failures.

**Independent Test**: Can be tested by installing a plugin declaring an
incompatible API version and verifying the system reports the incompatibility.

### Tests for User Story 2

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T015 [P] [US2] Test: PluginValidator rejects plugin with incompatible
  major API version in `tests/unit/test_plugin_validation.py`
- [ ] T016 [P] [US2] Test: PluginValidator accepts plugin with compatible
  API version (same major, different minor/patch) in
  `tests/unit/test_plugin_validation.py`
- [ ] T017 [P] [US2] Test: PluginValidator rejects plugin with unparseable
  version string in `tests/unit/test_plugin_validation.py`
- [ ] T018 [P] [US2] Test: PluginValidator rejects plugin missing required
  metadata fields in `tests/unit/test_plugin_validation.py`
- [ ] T019 [P] [US2] Test: PluginValidator checks handler_factory presence
  when handled_event_types is non-empty in
  `tests/unit/test_plugin_validation.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Create `specmetrics/kernel/plugin_validation.py` —
  PluginValidator class with validate(metadata) method performing:
  API version SemVer check, required field presence, handler_factory check
- [ ] T021 [US2] Add platform API version resolution via
  `importlib.metadata.version("specmetrics")` in PluginValidator
- [ ] T022 [US2] Add SemVer comparison logic — major must match; minor/patch
  within same major accepted; pre-release tags ignored; unparseable rejected
- [ ] T023 [US2] Add validation result reporting — return structured
  ValidationResult with is_valid, errors list

**Checkpoint**: User Story 2 is complete — incompatible plugins are rejected.

---

## Phase 5: User Story 3 — Registry lookup for pipeline orchestration (Priority: P1)

**Goal**: The Pipeline Engine queries the registry to find handlers for each
event type and the registry returns all matching plugins.

**Independent Test**: Can be tested by registering mock plugins, then querying
the registry by event type and verifying the correct handlers are returned.

### Tests for User Story 3

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T024 [P] [US3] Test: PluginRegistry.register() stores a validated
  PluginDescriptor in `tests/unit/test_plugin_registry.py`
- [ ] T025 [P] [US3] Test: PluginRegistry.get_handler() returns handler for
  registered event type in `tests/unit/test_plugin_registry.py`
- [ ] T026 [P] [US3] Test: PluginRegistry.get_handler() returns None for
  unregistered event type in `tests/unit/test_plugin_registry.py`
- [ ] T027 [P] [US3] Test: PluginRegistry.get_handlers() returns all handlers
  for an event type in registration order in
  `tests/unit/test_plugin_registry.py`
- [ ] T028 [P] [US3] Test: PluginRegistry.install_handlers() populates F01
  HandlerRegistry correctly in `tests/unit/test_plugin_registry.py`
- [ ] T029 [P] [US3] Test: PluginRegistry handles duplicate plugin IDs by
  logging warning and using last registration in
  `tests/unit/test_plugin_registry.py`
- [ ] T030 [US3] Integration test: End-to-end plugin lifecycle — discover →
  validate → register → install handlers → pipeline uses handlers in
  `tests/integration/test_plugin_lifecycle.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Create `specmetrics/kernel/plugin_registry.py` —
  PluginRegistry class with: register(), get_handler(), get_handlers(),
  list_plugins(), get_by_type()
- [ ] T032 [US3] Add `install_handlers(handler_registry)` method to
  PluginRegistry — iterates all REGISTERED plugins and calls
  handler_registry.register() for each handler_factory-produced handler
- [ ] T033 [US3] Add duplicate plugin ID detection — log warning, overwrite
  with last registration
- [ ] T034 [US3] Wire discovery → validation → registry into a unified
  load_plugins() entry point that performs the full lifecycle
- [ ] T035 [US3] Update `specmetrics/kernel/__init__.py` — export PluginRegistry
  and load_plugins

**Checkpoint**: User Story 3 is complete — registry integrates with F01.

---

## Phase 6: User Story 4 — Graceful plugin loading errors (Priority: P2)

**Goal**: A developer installs a corrupted or malformed plugin and the system
continues to operate with the remaining plugins, reporting the specific error
for the faulty one.

**Independent Test**: Can be tested by placing a malformed plugin in the
discovery path and verifying the system starts with remaining plugins intact.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T036 [P] [US4] Test: PluginDiscovery skips a plugin when its factory
  function raises an exception in `tests/unit/test_plugin_discovery.py`
- [ ] T037 [P] [US4] Test: PluginDiscovery skips a plugin when its module
  cannot be imported in `tests/unit/test_plugin_discovery.py`
- [ ] T038 [P] [US4] Test: load_plugins() isolates errors — one faulty plugin
  does not prevent healthy plugins from registering in
  `tests/unit/test_plugin_registry.py`
- [ ] T039 [US4] Integration test: Healthy plugin registers despite presence
  of faulty plugin in `tests/integration/test_plugin_lifecycle.py`

### Implementation for User Story 4

- [ ] T040 [P] [US4] Add per-plugin try/except in PluginDiscovery.scan() —
  catch import errors and factory errors, log warning with plugin ID, continue
  to next plugin
- [ ] T041 [US4] Add per-plugin try/except in PluginRegistry.register() —
  catch validation errors, set descriptor status to REJECTED, log error
- [ ] T042 [US4] Ensure load_plugins() atomicity — each plugin discovery +
  validation + registration is isolated; one failure never blocks another

**Checkpoint**: User Story 4 is complete — faulty plugins never block the system.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Add docstrings to all public plugin classes and methods
- [ ] T044 Run quickstart.md validation scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (discovery vs validation are independent)
  - US3 depends on US1 + US2 (registry needs discovered and validated plugins)
  - US4 depends on US1 + US2 (error isolation wraps discovery and validation)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on
  other stories
- **User Story 2 (P1)**: Can start after Foundational — Independent from US1
  (validation logic has no dependency on discovery mechanism)
- **User Story 3 (P1)**: Depends on US1 + US2 — Registry integrates discovered
  and validated plugins with F01 HandlerRegistry
- **User Story 4 (P2)**: Depends on US1 + US2 — Error isolation wraps both
  discovery and validation phases

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel
- US1 and US2 can proceed in parallel once Foundational is complete
- All tests within a story marked [P] can run in parallel
- PluginMetadata, PluginType, PluginStatus models can be built in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T008 [P] [US1] Test: PluginDiscovery scans entry points"
Task: "T009 [P] [US1] Test: PluginDiscovery handles empty discovery"
Task: "T010 [P] [US1] Test: PluginDiscovery loads factory function"
Task: "T011 [P] [US1] Test: PluginDiscovery discovers multiple plugins"

# Launch implementation tasks in parallel:
Task: "T012 [P] [US1] Create PluginDiscovery"
Task: "T013 [US1] Add factory function loading"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test plugin discovery independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo
4. Add User Story 3 → Test independently → Demo (full F01 integration)
5. Add User Story 4 → Test independently → Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 + User Story 2 (can be parallel)
   - Developer B: User Story 3 (waits for US1 + US2)
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
