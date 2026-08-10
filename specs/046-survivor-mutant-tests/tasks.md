# Tasks: Eliminate Surviving Mutants with Targeted Tests

**Input**: Design documents from `specs/046-survivor-mutant-tests/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: This feature IS about writing tests. Test generation tasks are the core implementation (US3). No separate test layer is created — the generated tests ARE the deliverable.

**Organization**: Tasks are grouped by user story, following the single-pass automated workflow defined in the spec (FR-002a).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Mutation log**: `mutants/mutmut-cicd-results.log` (input)
- **Report**: `mutants/survivor-analysis.md` (output)
- **Test files**: `tests/<mirror-path>/test_<module>.py` (modified or created)
- **Source files**: `specmetrics/<package>/<module>.py` (read-only)
- This feature does NOT modify any source code under `specmetrics/`

---

## Phase 1: Setup (Verify Prerequisites)

**Purpose**: Confirm the mutation log exists and the development environment is ready

- [X] T001 Verify `mutants/mutmut-cicd-results.log` exists and contains 8,822 survivor entries (grep count `^# `)
- [X] T002 [P] Verify `pytest` and `ruff` are available in the environment by running `pytest --version && ruff --version`

**Checkpoint**: Environment ready — mutation log accessible, tools available

---

## Phase 2: Foundational (Parse & Group)

**Purpose**: Parse the mutation log and organize survivors by module. This is the single data structure all subsequent phases depend on.

**⚠️ CRITICAL**: No user story work can begin until parsing and grouping is complete

- [X] T003 Parse `mutants/mutmut-cicd-results.log` and extract all 8,822 survivor entries into a structured in-memory representation: mutation_id, module_path, class_name, function_name, source_file, line_number, diff_hunk, original_line, mutated_line (per data-model.md Survivor entity)
- [X] T004 [P] Validate parsed survivor count equals 8,822 and count unique source files (expected: 157) using `grep "^--- " mutants/mutmut-cicd-results.log | sort -u | wc -l`
- [X] T005 Group survivors by source module prefix (e.g., `specmetrics.plugins.rule_pack`) into a module-to-survivors map. Create the initial skeleton of `mutants/survivor-analysis.md` with module headings and empty survivor tables

**Checkpoint**: All 8,822 survivors parsed, validated, and grouped — ready for analysis

---

## Phase 3: User Story 1 - Analyze Survivors Grouped by Module (Priority: P1)

**Goal**: Present all survivors organized by module with full metadata, enabling the engineer to understand which functions have unguarded behavior

**Independent Test**: Read the mutation report and verify every survivor is listed under its correct module heading with file, function, and mutation description

### Implementation for User Story 1

- [X] T006 [US1] For each module group in the survivors map, populate the survivor metadata: extract source file path from the diff header, resolve the function name from the module path, classify the mutation type (operator change, default value change, string literal change, control flow change, constant change per research.md Section 2)
- [X] T007 [US1] Populate the module sections in `mutants/survivor-analysis.md` with per-survivor table rows: mutation_id, source_file, function_name, mutation_type, original_token, mutated_token, line_number

**Checkpoint**: US1 complete — all 8,822 survivors are listed under their module groups in the report with full identifiers

---

## Phase 4: User Story 2 - Skip Survivors Already Killed by Existing Tests (Priority: P2)

**Goal**: Classify each survivor as ALREADY_GUARDED (existing test covers it), EQUIVALENT (semantically equivalent mutation), or NEEDS_NEW_TEST (truly uncovered). Skip the first two categories.

**Independent Test**: For a random sample of survivors classified as ALREADY_GUARDED, manually verify the referenced test exercises the mutated behavior

### Implementation for User Story 2

- [X] T008 [US2] For each survivor, locate the corresponding test file: map `specmetrics/<package>/<module>.py` to `tests/<mirror-path>/test_<module>.py`. If the test file does not exist, record the planned creation path `tests/<package>/test_<module>.py` per the edge case resolution
- [X] T009 [US2] Apply static diff-based guard detection for each survivor (per research.md Section 2): inspect the mutation's affected source lines from the diff, read the corresponding test file, and check whether existing test functions call the mutated function with inputs that exercise the mutated code path and assert on the altered behavior. Classify as ALREADY_GUARDED if a matching test is found
- [X] T010 [US2] Apply equivalent mutant heuristics for remaining survivors (per research.md Section 3): flag survivors matching LOG_STRING (logger/structlog call with only string literal change), TYPE_ANNOTATION (type hint mutation), DEFAULT_STRUCTURAL (`.get(key, {})` → `None` where used as dict), UNUSED_RESULT (mutation on line whose result is discarded), DEBUG_ONLY (behind log-level guard). Classify matches as EQUIVALENT with confidence level
- [X] T011 [US2] Classify all remaining survivors as NEEDS_NEW_TEST. Update the classification column in `mutants/survivor-analysis.md` for every survivor with the GuardAnalysis classification and rationale. Record summary counts (already_guarded, equivalent, needs_new_test, skipped) for the report header

**Checkpoint**: US2 complete — every survivor is classified; only NEEDS_NEW_TEST survivors proceed to test generation

---

## Phase 5: User Story 3 - Write Targeted Tests for Genuinely Uncovered Survivors (Priority: P1)

**Goal**: For every NEEDS_NEW_TEST survivor, write a pytest function that asserts on the specific behavior the mutation would alter. Each test must pass against the current (unmutated) source.

**Independent Test**: Run each new test individually (`pytest <file>::<test_function>`) and confirm it passes

### Implementation for User Story 3

- [X] T012 [US3] For each NEEDS_NEW_TEST survivor, determine the test placement location: if a test file at `tests/<mirror-path>/test_<module>.py` exists, use it; otherwise create the new test file at that path (creating parent directories if needed), writing the file header with `from __future__ import annotations` and adding an empty test class or module-level test placeholder
- [X] T013 [US3] Write a targeted pytest function for each NEEDS_NEW_TEST survivor. Each test function MUST: (a) import the function/class under test from the source module, (b) set up inputs that trigger the specific code path where the mutation occurs, (c) assert on the exact behavior the mutation would alter (e.g., boundary value, return type, raised exception, log output), (d) include a docstring referencing the mutation ID. Follow existing project test conventions: `test_<descriptive_name>` naming, `from __future__ import annotations`, no classes unless the target test file uses them. Append tests to the end of the target test file
- [X] T014 [US3] Run each newly written test individually with `pytest <test_file>::<test_function_name>` to confirm it passes against the current source (FR-007). Record pass/fail status
- [X] T015 [US3] For any test that fails during T014: analyze the failure, fix the test (correct assertions, fix imports, adjust inputs), and re-run until it passes. Do NOT modify source code under `specmetrics/`

**Checkpoint**: US3 complete — all NEEDS_NEW_TEST survivors have a passing test function. Test files are modified/created under `tests/`

---

## Phase 6: User Story 4 - Verify Lint and Full Test Suite (Priority: P2)

**Goal**: Ensure no regressions: lint passes clean and the complete test suite is green

**Independent Test**: Run `ruff check .` and `pytest tests/` — both must pass

### Implementation for User Story 4

- [X] T016 [US4] Run `ruff check .` from repository root. Fix any new lint findings introduced by test file modifications (unused imports, line length, formatting). Re-run lint until zero new findings (FR-008)
- [X] T017 [US4] Run `pytest tests/` (full test suite) from repository root. For any test failure: determine root cause, fix in the test code (do NOT modify source under `specmetrics/`), re-run the failing test individually, then re-run the full suite. Repeat until all tests pass (FR-009)

**Checkpoint**: US4 complete — lint clean, full test suite green. No regressions introduced

---

## Phase 7: Polish & Final Validation

**Purpose**: Finalize the report and validate the complete deliverable against all success criteria

- [X] T018 Finalize `mutants/survivor-analysis.md` with the complete ReportSummary (total_survivors, already_guarded, needs_new_test, equivalent, skipped, tests_added, files_modified), per-module sections with classification rationale for every survivor, equivalent mutants section grouped by confidence level for human review, and files-modified list per data-model.md AnalysisReport entity
- [X] T019 Validate report completeness: (a) verify survivor count in report summary matches 8,822, (b) verify every NEEDS_NEW_TEST survivor has at least one test function in a test file, (c) verify `mutmut` was never executed (no mutmut in shell history or process logs per FR-006)
- [X] T020 Run the quickstart.md verification checklist: confirm `mutants/survivor-analysis.md` exists with all sections, `ruff check .` passes, `pytest tests/` passes, no source files outside `tests/` were modified, all new tests follow project conventions

**Checkpoint**: Feature complete — all success criteria SC-001 through SC-006 satisfied

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (Phase 2) — needs parsed and grouped survivors
- **US2 (Phase 4)**: Depends on US1 (Phase 3) — needs module-organized survivors with metadata
- **US3 (Phase 5)**: Depends on US2 (Phase 4) — needs classification to identify NEEDS_NEW_TEST survivors
- **US4 (Phase 6)**: Depends on US3 (Phase 5) — needs all test files written before lint/suite run
- **Polish (Phase 7)**: Depends on US4 (Phase 6) — needs green suite before final validation

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependencies on other stories
- **US2 (P2)**: Depends on US1 — requires module-organized survivor metadata
- **US3 (P1)**: Depends on US2 — requires classification to filter NEEDS_NEW_TEST survivors
- **US4 (P2)**: Depends on US3 — requires all tests to be written

**Note**: US2 and US3 are sequential by necessity (classification before test writing). The single-pass automated workflow (FR-002a) processes survivors in order: group → classify → write. No parallelization across stories is possible.

### Within Each User Story

- T008 → T009 → T010 → T011 (sequential within US2: locate test files before guard detection, detect guard before equivalent check, classify last)
- T012 → T013 → T014 → T015 (sequential within US3: determine placement before writing, write before running, run before fixing)

### Parallel Opportunities

- T001 and T002 can run in parallel (Setup phase — independent checks)
- T003 and T004 can run in parallel (T003 does parsing while T004 independently verifies count with grep)
- Within a module group, multiple survivors can be analyzed in parallel for T009 (different source files)
- Within a module group, multiple test functions can be written in parallel for T013 (different test files)
- Within US4, T016 (lint) and T017 (test suite) must be sequential: fix lint first to avoid test noise

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3)

The MVP is the core pipeline: group survivors, classify them, and write tests for uncovered ones.

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — parses the log)
3. Complete Phase 3: US1 (module grouping with metadata)
4. Complete Phase 4: US2 (guard detection + equivalent heuristics + classification)
5. Complete Phase 5: US3 (test generation + individual validation)
6. **STOP and VALIDATE**: All NEEDS_NEW_TEST survivors have tests; all new tests pass individually
7. Complete Phase 6: US4 (lint + full suite)
8. Complete Phase 7: Polish (final report + validation)

### Incremental Delivery

This workflow is inherently sequential. Incremental value is delivered at each checkpoint:
1. After Phase 2: Parsed data available for inspection
2. After Phase 3: Module-grouped survivor list (US1 complete) — engineer can see the scope
3. After Phase 4: Classification complete (US2 complete) — engineer knows what needs work
4. After Phase 5: Tests written and passing (US3 complete) — core value delivered
5. After Phase 6: Green lint + suite (US4 complete) — ready for user's manual mutmut run
6. After Phase 7: Final report delivered — complete audit trail

### Single-Pass Execution

Per FR-002a, the entire workflow executes as a single pass over all modules without per-module human confirmation. The AI agent processes module groups sequentially but without interactive prompting between modules.

---

## Notes

- [P] tasks = different files/concerns, no data dependencies
- [Story] label maps task to specific user story for traceability
- `mutmut` MUST NOT be executed at any point (FR-006) — verify with shell history check in T019
- No source code under `specmetrics/` may be modified — only `tests/` and `mutants/`
- All new tests follow existing project conventions: `from __future__ import annotations`, `test_` prefix, docstrings
- Commit after each phase completion to preserve progress
- The user will run `mutmut` manually after this workflow completes to verify mutation score improvement

---

## Phase 8: Convergence

**Origin**: `/speckit.converge` — assessed the implemented codebase against spec.md, plan.md, and tasks.md. Mutation-kill verification (applying each survivor's diff and re-running the test suite) found survivors classified as `NEEDS_NEW_TEST` with no test that kills them, and the report summary counts (T018) were based on estimates that did not account for these.

**Scope**: Add the missing tests below and reconcile `mutants/survivor-analysis.md` counts. Only `tests/` and `mutants/` may be modified; do NOT modify source under `specmetrics/`.

- [X] T021 Add targeted pytest tests in `tests/application/test_entity_builders.py` for the 74 `_entities_for_rule` NEEDS_NEW_TEST survivors in `specmetrics/application/entity_builders.py` (builds `applied_rule_pack` and `modification_summary` entity payloads from `cfm.metadata.applied_rules`). Each test MUST assert on the exact behavior the mutation alters (rule-pack dict fields, defaults, `modification_summary` entity/`vaf_applied` computation) and reference the mutation IDs in docstrings. Verify with `pytest tests/application/test_entity_builders.py` and confirm the mutations are killed (per FR-005, SC-002)
- [X] T022 Add targeted pytest tests for the 26 `_entities_for_cfm` NEEDS_NEW_TEST survivors (entity payloads from CFM category maps and relationships) in `specmetrics/application/entity_builders.py`, appending to `tests/application/test_entity_builders.py`, asserting on the mutated behavior with mutation IDs in docstrings; verify they pass and kill the mutations
- [X] T023 Add targeted pytest tests for the 25 `_entities_for_csm` NEEDS_NEW_TEST survivors (entity payloads from CSM category maps) in `specmetrics/application/entity_builders.py`, appending to `tests/application/test_entity_builders.py`, asserting on the mutated behavior with mutation IDs in docstrings; verify they pass and kill the mutations
- [X] T024 Add targeted pytest tests for the 20 `_entities_for_measure` NEEDS_NEW_TEST survivors (measurement-result entity payloads via `_build_metric_entry`) in `specmetrics/application/entity_builders.py`, appending to `tests/application/test_entity_builders.py`, asserting on the mutated behavior with mutation IDs in docstrings; verify they pass and kill the mutations
- [X] T025 Add targeted pytest tests for the 5 `_print_result` NEEDS_NEW_TEST survivors in `specmetrics/cli/measure.py` (prints JSON vs text output via `format_json_result`/`format_text_result`), appending to `tests/cli/test_measure.py`, asserting on the exact printed output with mutation IDs in docstrings; verify they pass and kill the mutations
- [X] T026 Reconcile the `ReportSummary` in `mutants/survivor-analysis.md`: recompute `tests_added` (count of test functions actually added for NEEDS_NEW_TEST survivors) and `files_modified` (count of test files actually modified/created) after T021–T025, so every survivor classified NEEDS_NEW_TEST has a corresponding test and the report counts match the test tree (per FR-010, SC-001, Constitution V Evidence First)
