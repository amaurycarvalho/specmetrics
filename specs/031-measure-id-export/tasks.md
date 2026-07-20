# Tasks: Measure ID & Export Commands

**Input**: Design documents from `specs/031-measure-id-export/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tasks below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/cli/`, `specmetrics/application/`, `specmetrics/plugins/`, `specmetrics/kernel/`, `specmetrics/mcp/`, `specmetrics/infrastructure/` at repository root
- **Tests**: `tests/cli/`, `tests/contract/`, `tests/integration/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — no changes needed, project already exists.

*No setup tasks required for this feature. All changes are additive to existing files within the established project structure.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data model changes and utility functions that MUST be complete before ANY user story.

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 [P] Add `measure_id` field (timestamp-prefixed UUID) and `measure_id_path` field to `MeasureMetadata` in `specmetrics/cli/output_models.py`
- [x] T002 [P] Create `generate_measure_id()` utility that produces a timestamp-prefixed UUID (`YYYYMMDD-HHMMSS-<short-uuid>`) in `specmetrics/application/measure_id.py`
- [x] T003 Create `save_run_artifacts()` function that writes per-stage JSON files to `.specmetrics/runs/<measure-id>/` in `specmetrics/application/orchestrator.py` (consumes `PipelineResult` and writes `metadata.json` + per-stage `{stage_name}.json` files following the data model schema)
- [x] T004 [P] Create `read_run_artifacts()` function that loads per-stage JSON from `.specmetrics/runs/<measure-id>/` and returns structured data in `specmetrics/application/orchestrator.py`
- [x] T005 [P] Create `list_measure_runs()` function that scans `.specmetrics/runs/` and returns sorted list of run IDs with timestamps in `specmetrics/cli/export_commands.py`
- [x] T006 [P] Implement tabular normalization helpers for CSV/XML export: `normalize_discover_stage()`, `normalize_measure_stage()`, `normalize_items_stage()` in `specmetrics/plugins/exporter/orchestrator.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Run Measure and Capture Run ID (Priority: P1) 🎯 MVP

**Goal**: `specmetrics measure` generates a unique ID, persists per-stage JSON to `.specmetrics/runs/<id>/`, updates `specmetrics-output.json` with `measure.id` and `measure.id_path`, and prints the ID to stdout.

**Independent Test**: Run `specmetrics measure` on a known test project and verify (a) a non-empty measure ID is printed, (b) `.specmetrics/runs/<measure-id>/` contains JSON files, (c) `specmetrics-output.json` includes `measure.id` before `measure.sdd_framework` and `measure.id_path`.

### Implementation for User Story 1

- [x] T007 [US1] Call `generate_measure_id()` at start of `run_measure()` in `specmetrics/cli/measure.py` and print `Measure ID: <id>` to stdout
- [x] T008 [US1] Call `save_run_artifacts()` after pipeline execution in `run_measure()` in `specmetrics/cli/measure.py`, passing the measure ID and `PipelineResult`
- [x] T009 [US1] Inject the measure ID and ID path into `MeasureOutput` before the `specmetrics-output.json` is written by updating the `_handle_export()` or `_write_json_output()` in `specmetrics/application/orchestrator.py` to populate `measure.id` before `measure.sdd_framework` and `measure.id_path`
- [x] T010 [US1] Write unit test for measure ID generation in `tests/cli/test_measure.py` — verify format matches `YYYYMMDD-HHMMSS-<8-char-hex>`
- [x] T011 [US1] Write integration test verifying `specmetrics measure` creates `.specmetrics/runs/<id>/` with expected JSON files in `tests/cli/test_measure.py`
- [x] T012 [US1] Write contract test verifying `specmetrics-output.json` contains `measure.id` before `measure.sdd_framework` and `measure.id_path` in `tests/contract/test_measure_output.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — every `measure` run creates a persisted, identifiable result

---

## Phase 4: User Story 3 — List Available Measure Runs (Priority: P1)

**Goal**: `specmetrics export list` displays all measure IDs ordered by recency.

**Independent Test**: Run `specmetrics measure` twice, then `specmetrics export list` — both IDs should appear, ordered by recency, with timestamps.

### Implementation for User Story 3

- [x] T013 [US3] Add `list` subcommand to `export_app` typer group in `specmetrics/cli/export_commands.py` that calls `list_measure_runs()` and renders a table
- [x] T014 [US3] Handle empty state: display "No measure runs found." when `.specmetrics/runs/` is empty or does not exist
- [x] T015 [US3] Write unit test for `list_measure_runs()` in `tests/cli/test_export_commands.py`
- [x] T016 [US3] Write integration test for `specmetrics export list` output format in `tests/cli/test_export_commands.py`

**Checkpoint**: Users can discover all available measure runs

---

## Phase 5: User Story 4 — Export a Specific Measure Run (Priority: P1)

**Goal**: `specmetrics export run <measure-id>` exports per-stage files to `.specmetrics/exports/` for a given measure ID, with JSON (copy) and CSV/XML (tabular normalization).

**Independent Test**: Run `specmetrics measure`, then `specmetrics export run <id>` — verify `.specmetrics/exports/` contains per-stage files with correct content in the requested format.

### Implementation for User Story 4

- [x] T017 [US4] Add `--format` option (default `json`) to `export run` command in `specmetrics/cli/export_commands.py`
- [x] T018 [US4] Accept optional `<measure-id>` positional argument; when provided, validate the directory exists in `.specmetrics/runs/<id>/` and read artifacts via `read_run_artifacts()`
- [x] T019 [US4] Implement JSON export path: copy all files from `.specmetrics/runs/<measure-id>/` to `.specmetrics/exports/` using `shutil.copy()` or `shutil.copytree()`
- [x] T020 [US4] Implement CSV export path: for each stage file in the run directory, load JSON, pass through the appropriate tabular normalization helper, and write to `.specmetrics/exports/<stage>.csv`
- [x] T021 [US4] Implement XML export path: for each stage file in the run directory, load JSON, pass through the appropriate tabular normalization helper, and write to `.specmetrics/exports/<stage>.xml`
- [x] T022 [US4] Ensure `.specmetrics/exports/` directory is created if it does not exist; overwrite existing files
- [x] T023 [US4] Handle export of empty stage data: write empty file (or empty array) to maintain predictable file set
- [x] T024 [US4] Write unit test for JSON export (file copy) in `tests/cli/test_export_commands.py`
- [x] T025 [US4] Write unit test for CSV tabular normalization in `tests/cli/test_export_commands.py`
- [x] T026 [US4] Write unit test for XML tabular normalization in `tests/cli/test_export_commands.py`
- [x] T027 [US4] Write integration test for `specmetrics export run <id>` output files in `tests/integration/test_export_commands.py`

**Checkpoint**: Users can export any specific run in JSON, CSV, or XML

---

## Phase 6: User Story 5 — Export Latest Measure Run (Default) (Priority: P1)

**Goal**: `specmetrics export run` (without arguments) automatically exports the most recent run.

**Independent Test**: Run `specmetrics measure` twice, then `specmetrics export run` — the most recent run should be used, producing correct export files.

### Implementation for User Story 5

- [x] T028 [US5] When `<measure-id>` is omitted in `export run`, call `list_measure_runs()` and select the first (most recent) entry
- [x] T029 [US5] Write integration test for `specmetrics export run` default-behavior in `tests/integration/test_export_commands.py`

**Checkpoint**: Users can export their last measurement without looking up the ID

---

## Phase 7: User Story 2 — Run Measure with Automatic Export (Priority: P1)

**Goal**: `specmetrics measure --export` automatically triggers `export run` after measurement completes. `--format` controls the export format.

**Independent Test**: Run `specmetrics measure --export` — measurement completes, export files appear in `.specmetrics/exports/`.

### Implementation for User Story 2

- [x] T030 [US2] Add `--export` flag to the `measure` command in `specmetrics/cli/app.py` and pass it through to `run_measure()`
- [x] T031 [US2] Add `--format` option to the `measure` command in `specmetrics/cli/app.py` and pass it through to `run_measure()`
- [x] T032 [US2] In `run_measure()` in `specmetrics/cli/measure.py`, after pipeline execution and run persistence, if `--export` is set, call the `export run` logic with the current measure ID and the specified format (default `json`)
- [x] T033 [US2] Validate `--format` values before execution — error on invalid format strings
- [x] T034 [US2] Write integration test for `specmetrics measure --export` in `tests/integration/test_export_commands.py`

**Checkpoint**: Users can measure and export in a single command

---

## Phase 8: User Story 6 — Error Handling and Fallback for Missing Export Runs (Priority: P2)

**Goal**: Clear error messages for nonexistent IDs; backward-compatible fallback when no runs exist.

**Independent Test**: Run `specmetrics export run nonexistent-id` on a project with no runs — error is shown. On a project with some runs but wrong ID — error with available IDs.

### Implementation for User Story 6

- [x] T035 [US6] When `<measure-id>` is provided and `.specmetrics/runs/<id>/` does not exist, display `Measure run "<id>" not found.` and exit with code 1; include available IDs in the error message when runs exist
- [x] T036 [US6] When `<measure-id>` is omitted and no runs exist, fall back to running the measurement pipeline directly (call the existing pipeline execution logic from `export run`)
- [x] T037 [US6] Write unit tests for error messages in `tests/cli/test_export_commands.py`
- [x] T038 [US6] Write integration test for missing ID error in `tests/integration/test_export_commands.py`

**Checkpoint**: Robust error handling — users always get clear, actionable feedback

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T039 [P] Update README.md at repository root with new command syntaxes: `specmetrics measure [--export] [--format]`, `specmetrics export list`, `specmetrics export run [<measure-id>] [--format]`
- [x] T040 Run full test suite (`pytest`) and fix any regressions
- [x] T041 Clean up: remove any dead code or debug logging introduced during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — project already exists
- **Foundational (Phase 2)**: No dependencies — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 3 (Phase 4)**: Depends on Foundational + US1 completion (runs must exist)
- **User Story 4 (Phase 5)**: Depends on Foundational + US1 completion (runs must exist to export)
- **User Story 5 (Phase 6)**: Depends on US4 (same export mechanism, just default ID resolution)
- **User Story 2 (Phase 7)**: Depends on US1 + US4 (measure + export combined)
- **User Story 6 (Phase 8)**: Depends on US4 + US5 (error handling wraps export run)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US3 (P1)**: Can start after Foundational + US1 — Independently testable with pre-existing runs
- **US4 (P1)**: Can start after Foundational + US1 — Independently testable with a specific run ID
- **US5 (P1)**: Depends on US4 — Same command with default ID resolution
- **US2 (P1)**: Depends on US1 + US4 — Combines measure ID with export functionality
- **US6 (P2)**: Depends on US4 + US5 — Polish on export run error handling

### Within Each User Story

- Models/utilities before CLI wiring
- Core implementation before tests
- Story complete before moving to next

### Parallel Opportunities

- T001, T002 (Phase 2): Can run in parallel (different files: output_models.py vs models.py)
- T004, T005, T006 (Phase 2): Can run in parallel with each other (different files)
- US3 (Phase 4) can start after US1 completes — US3 and US4 can proceed in parallel
- All test tasks marked [P] can run in parallel (different test files)
- All model/utility tasks can run in parallel (different files)

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all Phase 2 tasks together (different files):
Task: "Add measure_id fields to MeasureMetadata in specmetrics/cli/output_models.py"
Task: "Create generate_measure_id() in specmetrics/application/models.py"
Task: "Create save_run_artifacts() in specmetrics/application/orchestrator.py"
Task: "Create read_run_artifacts() in specmetrics/plugins/exporter/orchestrator.py"
Task: "Create list_measure_runs() in specmetrics/cli/export_commands.py"
Task: "Implement tabular normalization helpers in specmetrics/plugins/exporter/orchestrator.py"
```

## Parallel Example: US1 + US3 + US4 (After Foundation)

```bash
# US1 tasks
Task: "Wire up ID generation and run persistence in specmetrics/cli/measure.py"
Task: "Update _write_json_output() in specmetrics/application/orchestrator.py"

# US3 tasks (can start in parallel with US4)
Task: "Add list subcommand in specmetrics/cli/export_commands.py"

# US4 tasks (can start in parallel with US3)
Task: "Refactor export run to read from run directory in specmetrics/cli/export_commands.py"
```

---

## Implementation Strategy

### MVP First (Phase 2 + Phase 3 = User Story 1 Only)

1. Complete Phase 2: Foundational (data models, utility functions)
2. Complete Phase 3: User Story 1 (measure ID generation + run persistence)
3. **STOP and VALIDATE**: Run `specmetrics measure` — verify ID printed, runs directory created, specmetrics-output.json updated
4. Deploy/demo if ready — subsequent stories add value incrementally

### Incremental Delivery

1. Foundational → Foundation ready (measure ID utility, data types)
2. US1 → `specmetrics measure` with run tracking (MVP!)
3. US3 → `specmetrics export list` (run discovery)
4. US4 → `specmetrics export run <id>` (export from persisted run)
5. US5 → `specmetrics export run` defaults to latest (convenience)
6. US2 → `specmetrics measure --export` (combined workflow)
7. US6 → Error handling polish
8. Polish → README update, test suite pass

### Maximum Parallel Strategy

With multiple developers:

1. Developer A: Phase 2 (all foundational tasks) — blocks everything
2. Once Phase 2 is done:
   - Developer A: US1 + US2 (core measure flow)
   - Developer B: US3 + US4 + US5 (export commands, can proceed once US1 provides test data)
   - Developer C: US6 + Polish (error handling, README)
3. All stories integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
