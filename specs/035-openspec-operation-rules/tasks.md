# Tasks: OpenSpec Operation Extraction Rules

**Input**: Design documents from `/specs/035-openspec-operation-rules/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Tests included per spec acceptance scenarios and quickstart validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/rules/openspec_rules.yaml` at repository root

---

## Phase 1: Setup

**Purpose**: Verify the existing codebase and understand the target file

- [X] T001 Verify existing test suite passes baseline: run `pytest specmetrics/tests/ -x --ignore=specmetrics/tests/integration/test_deterministic_pipeline.py::TestDeterministicPipeline::test_framework_detection_openspec -q`
- [X] T002 [P] Read `specmetrics/kernel/rules/openspec_rules.yaml` — identify the 9 rules to modify (lines 50, 59, 69, 104, 122, 170, 217, 226, 299)
- [X] T003 [P] Verify the 2 existing operation rules are unchanged: `openspec-scenario-heading` (line 77) and `openspec-when-trigger` (line 95) already have `type: "operation"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure. Single YAML file, zero code changes.

- No foundational tasks required — changes are isolated to existing YAML file, no new dependencies.

**Checkpoint**: Baseline tests pass. Ready to modify rules.

---

## Phase 3: User Story 1 - Repurpose Fact-Rules as Operation-Rules (Priority: P1) 🎯 MVP

**Goal**: Change 9 existing OpenSpec rules from `type: "fact"` to `type: "operation"` so behavioral content (THEN, AND, SHALL, DEVE, requirement headings, task items, decisions, What Changes) produces operations that feed functional processes and enable non-zero measurement metrics.

**Independent Test**: Run `specmetrics measure` on `tests/openspec/`. Verify Story Points > 0 and at least 1 functional process in the CFM.

### Implementation for User Story 1

- [X] T004 [P] [US1] Change `openspec-then-assertion` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 104)
- [X] T005 [P] [US1] Change `openspec-and-clause` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 299)
- [X] T006 [P] [US1] Change `openspec-shall-statement` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 69)
- [X] T007 [P] [US1] Change `openspec-deve-statement` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 59)
- [X] T008 [P] [US1] Change `openspec-req-heading` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 50)
- [X] T009 [P] [US1] Change `openspec-task-item` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 226)
- [X] T010 [P] [US1] Change `openspec-task-category` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 217)
- [X] T011 [P] [US1] Change `openspec-decision-colon` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 122)
- [X] T012 [P] [US1] Change `openspec-what-changes` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/openspec_rules.yaml` (line 170)
- [X] T013 [US1] Verify operation extraction from test documents: run quickstart scenario 1 — confirm Story Points > 0, Function Points > 0 on `tests/openspec/`
- [X] T014 [US1] Run quickstart scenario 2 — verify all 4 test patterns (THEN, SHALL, DEVE, Requirement) produce `type="operation"` elements

**Checkpoint**: All 9 rules changed, operations extracted, functional processes built, metrics non-zero.

---

## Phase 4: User Story 2 - Direction Inference Validation (Priority: P2)

**Goal**: Confirm operation direction is correctly inferred by the existing CFM builder for the repurposed rules. WHEN clauses → "input", THEN clauses → "output".

**Independent Test**: Run quickstart scenario 3 — verify `_infer_operation_direction` returns correct direction for each GWT keyword.

### Implementation for User Story 2

- [X] T015 [US2] Run quickstart scenario 3 — verify direction inference for WHEN (input), THEN (output), DEVE (input fallback), Scenario (query)
- [X] T016 [US2] Verify no builder code changes needed: the existing `_infer_operation_direction()` in `specmetrics/kernel/cfm/builder.py` already handles the GWT patterns in the repurposed rules' text

**Checkpoint**: Direction inference validated. No code changes needed.

---

## Phase 5: User Story 3 - Requirement Headings as Operations (Priority: P3)

**Goal**: Confirm requirement headings produce operation elements at the capability level, complementing scenario-level operations.

**Independent Test**: Run `specmetrics measure` on OpenSpec specs — verify both requirement-level and scenario-level operations appear in functional processes.

### Implementation for User Story 3

- [X] T017 [US3] Verify `openspec-req-heading` produces operation elements: run quickstart scenario 2 sub-test for requirement headings
- [X] T018 [US3] Run full `specmetrics measure` on `tests/openspec/` — verify requirement-heading operations coexist with scenario-level operations in the same functional process

**Checkpoint**: Multi-level operations validated. All 3 user stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and regression checks.

- [X] T019 [P] Run quickstart scenario 4 — verify no regressions: entity and fact types from unchanged rules are still present
- [X] T020 [P] Run quickstart scenario 5 — full pipeline spot-check on `tests/openspec/` verifying all metrics
- [X] T021 Run full existing test suite: `pytest specmetrics/tests/ -x --ignore=specmetrics/tests/integration/test_deterministic_pipeline.py::TestDeterministicPipeline::test_framework_detection_openspec -q` — confirm no regressions
- [X] T022 Verify YAML syntax: run `python3 -c "from ruamel.yaml import YAML; YAML(typ='safe').load(open('specmetrics/kernel/rules/openspec_rules.yaml'))"` — confirm YAML is valid

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: N/A — no infrastructure needed
- **User Story 1 (Phase 3)**: Depends on Setup (verify baseline)
- **User Story 2 (Phase 4)**: Depends on US1 (rules must be changed first)
- **User Story 3 (Phase 5)**: Depends on US1 (rules must be changed first)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories. All YAML changes are in the same file but can be committed together.
- **User Story 2 (P2)**: Depends on US1 — rules must be changed before direction can be validated.
- **User Story 3 (P3)**: Depends on US1 — rules must be changed before heading operations can be validated.

### Within Each User Story

- US1: All 9 rule changes (T004-T012) are [P] — can be done in any order since they're independent lines in the same file
- US2: T015 (validation) → T016 (confirmation)
- US3: T017 (validation) → T018 (integration test)

### Parallel Opportunities

- All 9 US1 rule changes (T004-T012) can run in parallel (independent YAML lines)
- US2 and US3 can run in parallel after US1 completes (both are validation-only)
- Polish tasks T019-T020 can run in parallel

---

## Parallel Example: User Story 1 — All 9 Rules

```bash
# All 9 YAML type changes can be applied in parallel (different lines, same file):
Task: "Change openspec-then-assertion type in specmetrics/kernel/rules/openspec_rules.yaml line 104"
Task: "Change openspec-and-clause type in specmetrics/kernel/rules/openspec_rules.yaml line 299"
Task: "Change openspec-shall-statement type in specmetrics/kernel/rules/openspec_rules.yaml line 69"
Task: "Change openspec-deve-statement type in specmetrics/kernel/rules/openspec_rules.yaml line 59"
Task: "Change openspec-req-heading type in specmetrics/kernel/rules/openspec_rules.yaml line 50"
Task: "Change openspec-task-item type in specmetrics/kernel/rules/openspec_rules.yaml line 226"
Task: "Change openspec-task-category type in specmetrics/kernel/rules/openspec_rules.yaml line 217"
Task: "Change openspec-decision-colon type in specmetrics/kernel/rules/openspec_rules.yaml line 122"
Task: "Change openspec-what-changes type in specmetrics/kernel/rules/openspec_rules.yaml line 170"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 3: User Story 1 (T004-T014)
3. **STOP and VALIDATE**: Run `specmetrics measure` on `tests/openspec/` — confirm Story Points > 0
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → Baseline verified
2. Add US1 → 9 rules changed → Operations extracted → Metrics non-zero → MVP!
3. Add US2 → Direction validated → Correct FPA classification
4. Add US3 → Headings as operations → Richer process model
5. Polish → No regressions → Complete

### Parallel Team Strategy

This feature is sufficiently small that parallel development is unnecessary. One developer can complete all tasks in ~30 minutes.

---

## Phase 7: Convergence

**Purpose**: Fix regex patterns in 7 non-matching OpenSpec rules so they align with observation-based extraction format.

- [X] T023 Fix regex patterns in `openspec_rules.yaml` for 7 rules (`openspec-then-assertion`, `openspec-and-clause`, `openspec-req-heading`, `openspec-decision-colon`, `openspec-what-changes`, `openspec-task-category`, `openspec-task-item`) to match observation content without markdown list/heading prefixes per SC-004 (partial)

## Notes

- [P] tasks = independent YAML lines, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Zero code changes required — only YAML `type` field value changes
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
