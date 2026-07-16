# Tasks: Explain Measurement

**Input**: Design documents from `/specs/016-explain-measurement/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in the feature specification. Test tasks are omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/cli/`, `specmetrics/mcp/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the explanation module structure and shared models

- [x] T001 Create `specmetrics/kernel/explanation/` package with `__init__.py`
- [x] T002 [P] Create `specmetrics/kernel/explanation/models.py` with data model entities
- [x] T003 [P] Create `specmetrics/kernel/explanation/formatters/` package with `__init__.py`
- [x] T004 [P] Create `specmetrics/tests/unit/explanation/` test directory with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `ExplainService` class in `specmetrics/kernel/explanation/service.py`
- [x] T006 Create `EvidenceTracer` class in `specmetrics/kernel/explanation/evidence_tracer.py`
- [x] T007 [P] Implement text formatter in `specmetrics/kernel/explanation/formatters/text.py`
- [x] T008 [P] Implement JSON formatter in `specmetrics/kernel/explanation/formatters/json.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Explain a Measurement Result (Priority: P1) MVP

**Goal**: Users can request and receive a structured explanation for any completed measurement result, showing which spec elements contributed to each metric.

**Independent Test**: Execute a measurement on a known spec, request explanation for a specific metric, and verify the explanation references the expected spec elements, evidence fragments, and applied rules.

### Implementation for User Story 1

- [x] T009 [P] [US1] Add `explain()` method to ExplainService in `specmetrics/kernel/explanation/service.py`
- [x] T010 [P] [US1] Add `load_explanation()` method to ExplainService in `specmetrics/kernel/explanation/service.py`
- [x] T011 [US1] Create CLI command in `specmetrics/cli/commands/explain.py`
- [x] T012 [US1] Register explain CLI subcommand in `specmetrics/cli/app.py`
- [x] T013 [US1] Implement `trace_element()` in EvidenceTracer in `specmetrics/kernel/explanation/evidence_tracer.py`
- [x] T014 [US1] Wire ExplainService to Evidence Graph and CFM interfaces in `specmetrics/kernel/explanation/service.py`

**Checkpoint**: At this point, User Story 1 should be fully functional. Running `specmetrics explain <run_id>` produces a complete explanation with elements and evidence.

---

## Phase 4: User Story 2 — Trace a Metric to Its Source Evidence (Priority: P2)

**Goal**: Users can drill into any metric to see the exact specification text fragments that caused each element to be counted.

**Independent Test**: Provide a spec with known content, run measurement, trace a single count to its source evidence, and verify the evidence text matches the original specification.

### Implementation for User Story 2

- [x] T015 [P] [US2] Add `trace_metric()` method to EvidenceTracer in `specmetrics/kernel/explanation/evidence_tracer.py`
- [x] T016 [P] [US2] Add `--metric` filter option to CLI command in `specmetrics/cli/commands/explain.py`
- [x] T017 [US2] Add drill-down evidence output in text formatter in `specmetrics/kernel/explanation/formatters/text.py`
- [x] T018 [US2] Handle orphan-count warning (element with no evidence) in evidence tracer

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. `specmetrics explain <run_id> --metric <name>` shows evidence traces.

---

## Phase 5: User Story 3 — Compare Explanations Across Measurement Runs (Priority: P3)

**Goal**: Users can compare two measurement runs side by side, highlighting which metrics changed and which elements caused the differences.

**Independent Test**: Provide two versions of the same spec with one known difference, run measurement on both, request a comparison, and verify the output highlights the expected difference.

### Implementation for User Story 3

- [x] T019 [P] [US3] Create comparison logic in `specmetrics/kernel/explanation/comparison.py`
- [x] T020 [P] [US3] Add `compare()` method to ExplainService in `specmetrics/kernel/explanation/service.py`
- [x] T021 [P] [US3] Add `--compare` option to CLI command in `specmetrics/cli/commands/explain.py`
- [x] T022 [US3] Implement comparison output in text formatter
- [x] T023 [US3] Implement comparison output in JSON formatter

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: MCP Tool & Polish

**Purpose**: Expose explanation capability through MCP and finalize cross-cutting concerns

- [x] T024 [P] Create MCP explain tool in `specmetrics/mcp/tools/explain.py`
- [x] T025 [P] Register explain tool in MCP server
- [x] T026 Add explanation config support (formatter selection, evidence depth) in `specmetrics/kernel/explanation/service.py`
- [x] T027 [P] Update documentation references in `specs/016-explain-measurement/`
- [x] T028 Run `quickstart.md` validation scenarios and fix any issues

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — standalone MVP increment
- **User Story 2 (P2)**: Builds on ExplainService from US1 — adds drilling/filtering capabilities
- **User Story 3 (P3)**: Builds on MeasurementExplanation model from US1 — comparison operates on serialized Explanation records

### Within Each User Story

- Models before services
- Services before CLI/endpoints
- Core implementation before formatting
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004 in Setup can run in parallel
- T007, T008 in Foundational can run in parallel
- T009, T010 in US1 can run in parallel
- T015, T016 in US2 can run in parallel
- T019, T020, T021 in US3 can run in parallel
- T024, T025 in Polish can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all parallel [P] tasks together:
Task: "Add explain() method to ExplainService in service.py"
Task: "Add load_explanation() method to ExplainService in service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Explain measurement result)
4. **STOP and VALIDATE**: `specmetrics explain <run_id>` returns structured explanation
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add MCP tool + Polish → Finalize

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2 (after US1 designs are stable)
   - Developer C: User Story 3 (after US1 models are stable)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- The Evidence Graph and CFM must already exist with data for explanation to work
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
