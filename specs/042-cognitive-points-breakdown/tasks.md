# Tasks: Cognitive Points Breakdown

**Input**: Design documents from `specs/042-cognitive-points-breakdown/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in feature specification. Test tasks are included where they validate existing test infrastructure.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/` at repository root for source, `tests/` for tests

---

## Phase 1: Setup

> This feature requires no project initialization — the project structure and dependencies already exist. Skip directly to implementation.

---

## Phase 2: Foundational (Blocking Prerequisites)

> No foundational work needed. The Cognitive Points plugin, orchestrator, and CLI formatter already exist and are functional. All changes are additive within these existing files.

---

## Phase 3: User Story 1 - Bloom-Level Score Breakdown in measure.json (Priority: P1) 🎯 MVP

**Goal**: The Cognitive Points entry in `measure.json` includes a `breakdown` field with per-Bloom-level score totals, computed from existing `CognitiveContribution` data.

**Independent Test**: Run `specmetrics measure` on any project and inspect `measure.json`. Verify the Cognitive Points entry contains a `breakdown` object with one key per Bloom level found, each containing a `total` field.

### Implementation for User Story 1

- [X] T001 [US1] Add `cognitive_bloom_breakdown` payload key computation in `specmetrics/plugins/measurement/cognitive_points/plugin.py` — aggregate `partial_score` by `bloom_level` from `all_cognitive_contributions`, wrap into `{level: {total: float}}` format, and add to payload dict (after line 108, before payload dict is used)
- [X] T002 [US1] Update `key_map` for `cognitive_points` in `specmetrics/application/orchestrator.py` line 602 from `("cognitive_raw_score", None)` to `("cognitive_raw_score", "cognitive_bloom_breakdown")`

### Tests for User Story 1

- [X] T003 [P] [US1] Add test for `cognitive_bloom_breakdown` presence and structure in `tests/integration/test_cognitive_points_pipeline.py` — verify breakdown key exists in payload, contains `{level: {total: float}}`, and totals sum to `cognitive_raw_score`
- [X] T004 [P] [US1] Add test for measure.json breakdown output in `tests/integration/test_cognitive_points_pipeline.py` — verify the measure stage entry for cognitive_points includes a `breakdown` field when elements are present

**Checkpoint**: Running `specmetrics measure` produces a `measure.json` with `breakdown` in the Cognitive Points entry. The breakdown values sum to the total.

---

## Phase 4: User Story 2 - Bloom-Level Score Breakdown in CLI Display (Priority: P1)

**Goal**: The CLI text output shows indented Bloom-level breakdown lines below the Cognitive Points total line.

**Independent Test**: Run `specmetrics measure` on any project and verify indented Bloom-level lines appear below "Cognitive Points" in the Results section.

### Implementation for User Story 2

- [X] T005 [US2] Add CLI display block for Cognitive Points breakdown in `specmetrics/cli/formatters.py` — after the Cognitive Points total line (around line 41), read `cognitive_bloom_breakdown` from `result.measurement_result_raw`, iterate levels, and append indented lines in format `    {Level.title()}: {total}`
- [X] T006 [US2] Handle edge cases in formatter — skip when `cognitive_bloom_breakdown` is missing, empty dict, or contains zero totals; handle both `{total: float}` nested format and bare float values

### Tests for User Story 2

- [X] T007 [P] [US2] Add test for CLI text output containing breakdown lines in `tests/unit/test_cognitive_points_calculator.py` — mock a `PipelineResult` with `cognitive_bloom_breakdown` in `measurement_result_raw` and verify `format_text_result()` includes indented per-level lines
- [X] T008 [P] [US2] Add test for CLI behavior with empty breakdown in `tests/unit/test_cognitive_points_calculator.py` — verify no indented lines appear when breakdown is missing or empty

**Checkpoint**: CLI text output shows indented Bloom-level breakdown lines below Cognitive Points. Empty specs produce no breakdown lines.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validate feature completeness against quickstart scenarios.

- [X] T009 Run quickstart.md validation scenarios — verify all 6 scenarios pass (measure.json breakdown, CLI display, sum verification, empty spec, backward compatibility, ordering)
- [X] T010 [P] Run existing Cognitive Points tests to verify no regressions — `pytest tests/unit/test_cognitive_points*.py tests/contract/test_cognitive_points*.py tests/integration/test_cognitive_points*.py -v`
- [X] T011 [P] Run linter on modified files — `ruff check specmetrics/plugins/measurement/cognitive_points/plugin.py specmetrics/application/orchestrator.py specmetrics/cli/formatters.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Skipped — project already initialized
- **Phase 2 (Foundational)**: Skipped — no blocking prerequisites
- **Phase 3 (US1)**: No dependencies — can start immediately
- **Phase 4 (US2)**: Depends on T001 (payload key must exist for formatter to read it); T002 is independent
- **Phase 5 (Polish)**: Depends on Phases 3 and 4 completion

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories. Self-contained in plugin + orchestrator.
- **User Story 2 (P1)**: Depends on T001 from US1 (needs `cognitive_bloom_breakdown` in payload). Does NOT depend on T002 (orchestrator change).

### Within Each User Story

- T001 → T002 (orchestrator mapping follows plugin output)
- T003, T004 can run after T001 (tests validate plugin behavior)
- T005 → T006 (edge cases build on main display logic)
- T007, T008 can run after T005 is written (tests validate formatter)

### Parallel Opportunities

- T003 and T004 can run in parallel (both tests, different focus areas)
- T007 and T008 can run in parallel (both unit tests, same file)
- T010 and T011 can run in parallel (test run + linter)
- US1 and US2 implementation tasks are sequential due to data dependency

---

## Parallel Example: User Story 1 Tests

```bash
# Launch both US1 tests together:
Task: "T003 [P] [US1] Add test for cognitive_bloom_breakdown in tests/integration/test_cognitive_points_pipeline.py"
Task: "T004 [P] [US1] Add test for measure.json breakdown in tests/integration/test_cognitive_points_pipeline.py"
```

## Parallel Example: Polish Phase

```bash
# Launch regression test and linter in parallel:
Task: "T010 [P] Run existing Cognitive Points tests"
Task: "T011 [P] Run linter on modified files"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001 → T002 (measure.json breakdown)
2. Complete T003, T004 (verify with tests)
3. **STOP and VALIDATE**: Run `specmetrics measure .` and inspect `measure.json` for breakdown field
4. The measure.json breakdown is the minimum deliverable — programmatic consumers can already use it

### Incremental Delivery

1. Complete Phase 3 (US1) → measure.json has breakdown → Validate
2. Complete Phase 4 (US2) → CLI shows breakdown → Validate
3. Complete Phase 5 (Polish) → quickstart scenarios pass → Ship

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Total modified files: 3 source files (`plugin.py`, `orchestrator.py`, `formatters.py`)
- Total test files: 2 (`test_cognitive_points_pipeline.py`, `test_cognitive_points_calculator.py`)
- No new files, models, or calibration changes
- All changes are additive — existing tests must continue to pass
- Order of Bloom levels in dict matters for display: `["remember", "understand", "apply", "analyze", "evaluate", "create"]`
