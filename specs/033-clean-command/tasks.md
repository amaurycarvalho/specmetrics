---

description: "Task list for clean command feature implementation"

---

# Tasks: Clean Command for Runs Housekeeping

**Input**: Design documents from `/specs/033-clean-command/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/clean-cli.md, quickstart.md

**Tests**: Included — the spec defines acceptance scenarios with Given/When/Then. Each user story must be independently testable.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project paths**: `specmetrics/cli/`, `specmetrics/infrastructure/`, `specmetrics/tests/`
- All paths are relative to the repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure for new code

- [x] T001 Create `specmetrics/infrastructure/runs/` package directory with `__init__.py`
- [x] T002 [P] Create test directories `tests/unit/infrastructure/runs/` and `tests/cli/test_clean.py` with `__init__.py` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core cleaner module that MUST be complete before any user story can be tested

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Implement `RunFolder` dataclass and `RetentionPolicy` dataclass in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T004 Implement `discover_run_folders()` — lists `.specmetrics/runs/`, filters by naming pattern `^\d{8}-\d{6}-[a-f0-9-]+$`, parses timestamps, returns sorted list of `RunFolder` — in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T005 Implement `compute_retention()` — applies `keep_runs` + `keep_days` intersection logic per data-model.md — in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T006 Implement `delete_run_folders()` — calls `shutil.rmtree` on each folder with per-folder error handling (log warning, continue), returns count of successfully deleted and count of failures — in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T007 Implement `dry_run()` — returns `DryRunResult` with lists of folders to delete/keep and summary text — in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T008 Implement `clean_runs()` orchestration function — ties discovery → retention computation → deletion/dry-run into a single callable — in `specmetrics/infrastructure/runs/cleaner.py`

**Checkpoint**: Foundation ready — `cleaner.py` module is complete and can be unit tested

---

## Phase 3: User Story 1 - Developer cleans old runs with defaults (Priority: P1) 🎯 MVP

**Goal**: User runs `specmetrics clean` and the default retention policy (keep last 90 runs, keep 30 days) removes only runs outside both thresholds.

**Independent Test**: Create 100+ run folders with varied timestamps, run `specmetrics clean` with defaults, verify only runs outside both thresholds are deleted.

### Tests for User Story 1

- [x] T009 [P] [US1] Write unit tests for cleaner default behavior — 3 scenarios from spec (100 runs with 10 old, 200 runs all old, 5 runs all recent) — in `tests/unit/infrastructure/runs/test_cleaner.py`

### Implementation for User Story 1

- [x] T010 [US1] Implement CLI command function `clean()` in `specmetrics/cli/commands/clean.py` with `--keep-runs`, `--keep-days`, `--dry-run`, `--verbose`, `--quiet`, `--project-path` options matching contract in `contracts/clean-cli.md`
- [x] T011 [US1] Register `clean` command in `specmetrics/cli/app.py` (import and `app.command()`)
- [x] T012 [US1] Handle missing `.specmetrics/runs/` and empty directory cases — print message, exit 0 (FR-008, FR-009) in `specmetrics/cli/commands/clean.py`
- [x] T013 [US1] [P] Write CLI integration tests for `specmetrics clean` with defaults — use `CliRunner` + `tmp_path`, verify output and exit codes — in `tests/cli/test_clean.py`

**Checkpoint**: User can run `specmetrics clean` and see runs cleaned with defaults

---

## Phase 4: User Story 2 - Developer customizes retention policy (Priority: P1)

**Goal**: User can customize retention via `--keep-runs` and `--keep-days` options, including `0` to disable each axis.

**Independent Test**: Create 20 run folders spanning 7 days, run with `--keep-runs 7 --keep-days 1`, verify only the intersection of last-7-runs and last-1-day is kept. Test `--keep-runs 0` and `--keep-days 0` independently.

### Tests for User Story 2

- [x] T014 [P] [US2] Write unit tests for custom retention values — `--keep-runs 0`, `--keep-days 0`, `--keep-runs 7 --keep-days 1`, both 0 (delete all) — in `tests/unit/infrastructure/runs/test_cleaner.py`

### Implementation for User Story 2

- [x] T015 [US2] Add `--keep-runs 0` and `--keep-days 0` passthrough to `clean_runs()` in `specmetrics/cli/commands/clean.py` (the core logic in cleaner.py already supports 0-disables; ensure CLI correctly passes 0 instead of defaulting to 90/30)
- [x] T016 [US2] Handle edge cases — non-run files/dirs silently skipped (FR-012), invalid folder names silently skipped — in `specmetrics/infrastructure/runs/cleaner.py`
- [x] T017 [US2] [P] Write CLI integration tests for custom retention — `CliRunner` with `--keep-runs`, `--keep-days` variations — in `tests/cli/test_clean.py`

**Checkpoint**: User can customize retention via CLI options

---

## Phase 5: User Story 3 - Developer previews what would be deleted (Priority: P2)

**Goal**: User runs `specmetrics clean --dry-run` and sees which runs would be deleted without actually removing any files.

**Independent Test**: Create runs, run `--dry-run`, verify output lists the same runs that a real `specmetrics clean` would delete. Verify no files are actually deleted.

### Tests for User Story 3

- [x] T018 [P] [US3] Write unit tests for dry-run — verify `DryRunResult` accuracy, verify no files are deleted — in `tests/unit/infrastructure/runs/test_cleaner.py`

### Implementation for User Story 3

- [x] T019 [US3] Format dry-run output — list each run folder with timestamp and reason, show summary counts — in `specmetrics/cli/commands/clean.py`
- [x] T020 [US3] [P] Write CLI integration tests for dry-run — `CliRunner` with `--dry-run`, verify output contains expected run IDs, verify no filesystem changes — in `tests/cli/test_clean.py`

**Checkpoint**: User can preview deletions safely with `--dry-run`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final validation

- [x] T021 [P] Update `README.md` — add `specmetrics clean` to the CLI usage section and CLI Parameters table per the user's request
- [x] T022 Run `make lint test` to verify code quality and all tests pass
- [x] T023 Run quickstart validation scenarios from `quickstart.md` to confirm end-to-end correctness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (P1)**: Depends on Foundational — CLI command wrapping the cleaner module
- **User Story 2 (P1)**: Depends on Foundational — extends CLI with custom option passthrough and edge cases
- **User Story 3 (P2)**: Depends on Foundational — dry-run output formatting on top of `clean_runs()`
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — primary CLI implementation
- **User Story 2 (P1)**: Can start after Foundational — independently testable using the same cleaner module
- **User Story 3 (P2)**: Can start after Foundational — independently testable using the same cleaner module

### Within Each User Story

- Tests are written and FAIL before implementation
- Unit tests before CLI integration tests
- Implementation before formatting/output polish

### Parallel Opportunities

- All Phase 1 Setup tasks marked [P] can run in parallel
- All test tasks marked [P] can run in parallel (within and across phases)
- US1, US2, and US3 are independent once Foundational is complete — all could run in parallel
- T011 (register in app.py) is sequential on T010 (implement command)

---

## Parallel Example: User Story 1

```bash
# Launch both test files at the same time:
cd /home/amaury/Documentos/Sources/Python/specmetrics

# Task T009: Unit tests for cleaner default behavior
Task: "Write unit tests for cleaner default behavior in tests/unit/infrastructure/runs/test_cleaner.py"

# Task T013: CLI integration tests for clean with defaults
Task: "Write CLI integration tests in tests/cli/test_clean.py"

# These can run in parallel after T010 (implement clean command) is done
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (core cleaner module)
3. Complete Phase 3: User Story 1 (CLI command with defaults)
4. **STOP and VALIDATE**: `specmetrics clean` works with defaults
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (custom retention) → Test independently → Deploy/Demo
4. Add User Story 3 (dry-run) → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (CLI command + tests)
   - Developer B: User Story 2 (custom retention edge cases + tests)
   - Developer C: User Story 3 (dry-run formatting + tests)
3. All three stories can integrate independently since they all call into the same `clean_runs()` function

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
