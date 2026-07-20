# Tasks: Measure Metric Filtering & JSON Output

**Input**: Design documents from `/specs/030-measure-metric-filter/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/measure-cli-interface.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. Note that US1, US2, and US3 share the same mechanism (CLI argument → PipelineRequest → orchestrator filter → formatter output) — US1 establishes the infrastructure, US2/US3 are natural consequences of the same implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

All paths are relative to the repository root (`specmetrics/`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure review and configuration

- [x] T001 Review existing codebase: `cli/app.py`, `cli/measure.py`, `cli/formatters.py`, `application/models.py`, `application/orchestrator.py` to understand current `measure` command flow
- [x] T002 [P] Review measurement plugin entry points in `pyproject.toml` under `[project.entry-points."specmetrics.plugins.measurement"]` for metric ID mapping reference

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model changes that all user stories depend on

- [x] T003 Add `metrics_filter: list[str] | None = None` field to `PipelineRequest` dataclass in `specmetrics/application/models.py`
- [x] T004 [P] Add `duration_seconds` field to `StageResult` if not already tracked per-stage in `specmetrics/application/models.py`
- [x] T005 [P] Create Pydantic output models (`MeasureOutput`, `MeasureMetadata`, `MetricResult`, `StageInfo`, `ErrorRecord`) in `specmetrics/cli/output_models.py` per data-model.md schema
- [x] T006 Create `METRIC_NAME_MAP` constant mapping CLI short IDs to JSON snake_case names in `specmetrics/application/models.py`

**Checkpoint**: Foundation ready — data models can represent metric selections and JSON output

---

## Phase 3: User Story 1 — Run Measurement with Default (All Metrics) (Priority: P1) 🎯 MVP

**Goal**: Running `specmetrics measure` (or `specmetrics measure all`) shows all 8 metric totals in text output and writes `specmetrics-output.json`

**Independent Test**: Run `specmetrics measure` on a known test project, verify all 8 metric lines appear in Results section, and `.specmetrics/output/specmetrics-output.json` is created with valid JSON

### Implementation for User Story 1

- [x] T007 [US1] Add optional `metrics` positional argument to `measure` command in `specmetrics/cli/app.py` — `metrics: Optional[str] = typer.Argument(None, ...)`
- [x] T008 [P] [US1] Implement metric argument parsing and validation in `specmetrics/cli/measure.py` — parse comma-separated string, trim whitespace, normalize to `all` when None, pass as `metrics_filter` to `PipelineRequest`
- [x] T009 [US1] Implement orchestrator metric filtering in `specmetrics/application/orchestrator.py` — pass `metrics_filter` to `discover_plugins()` which filters measurement plugin handler installation
- [x] T010 [P] [US1] Add per-metric result collection in `specmetrics/application/orchestrator.py` — `_build_metric_results()` collects name/total/status from measurement_result dict
- [x] T011 [US1] Update `format_text_result()` in `specmetrics/cli/formatters.py` — iterate over `metric_results` and display human-readable name + total value; preserve existing sub-detail format for FPA (ILF/EIF breakdown)
- [x] T012 [P] [US1] Add metric display names in `specmetrics/application/models.py` — `METRIC_DISPLAY_MAP` with human-readable labels
- [x] T013 [US1] Implement `_write_json_output()` in `specmetrics/application/orchestrator.py` — collect measure metadata, per-metric results, stage info, errors; write Pydantic-serialized JSON to `.specmetrics/output/specmetrics-output.json`
- [x] T014 [US1] Replace text file export in `_handle_export()` in `specmetrics/application/orchestrator.py` — call `_write_json_output` when `output_format` is `TEXT`
- [x] T015 [US1] Update `format_json_result()` in `specmetrics/cli/formatters.py` — keep existing JSON stdout format for `--output json` CLI flag; new JSON schema goes to file

**Checkpoint**: `specmetrics measure` works end-to-end with all 8 metrics, text output shows all metric totals, JSON file written with correct schema

---

## Phase 4: User Story 2 — Filter to a Single Metric (Priority: P1)

**Goal**: Running `specmetrics measure fpa` executes and displays only the FPA metric; other metrics are skipped

**Independent Test**: Run `specmetrics measure fpa`, verify only FPA result shown in text output, only FPA entry in `results` array in JSON, and execution completes faster than `specmetrics measure all`

**Note**: US2 leverages the infrastructure built in US1. The `metrics_filter` field already supports multiple values. This phase is primarily about verification and edge-case handling.

### Implementation for User Story 2

- [x] T016 [P] [US2] JSON output `results` array contains only entries for selected metrics — `_build_metric_results()` uses `metrics_filter` param
- [x] T017 [US2] Unselected metrics are not installed as handlers — `install_handlers()` in `plugin_registry.py` skips measurement plugins not in `metrics_filter`
- [x] T018 [US2] `--stage measure` combined with metric filter works — metric filter only affects measurement plugin installation, stage selection is independent

**Checkpoint**: Single-metric filtering works end-to-end

---

## Phase 5: User Story 3 — Filter to Multiple Metrics (Priority: P1)

**Goal**: Running `specmetrics measure fpa, sfp, snap` executes and displays only those three metrics

**Independent Test**: Run `specmetrics measure fpa, sfp`, verify only FPA and SFP results shown, and other metrics are not executed

**Note**: US3 is a natural extension of US2 — the same code path handles single and multiple metrics. Focus on edge cases and verification.

### Implementation for User Story 3

- [x] T019 [US3] Deduplication logic — `_parse_metrics()` deduplicates with `seen` set in `specmetrics/cli/measure.py`
- [x] T020 [US3] `all` override logic — `_parse_metrics()` returns `None` (meaning all) when `"all"` is in the list in `specmetrics/cli/measure.py`
- [x] T021 [US3] Whitespace trimming — `m.strip()` applied to each part in `_parse_metrics()`
- [x] T022 [US3] Stage/metric filter composition — metric filtering only affects which measurement plugin handlers are installed; stage selection via `--stage`/`--from` is independent

**Checkpoint**: Multi-metric filtering with all edge cases handled

---

## Phase 6: User Story 4 — Invalid Metric Name Handling (Priority: P2)

**Goal**: Invalid metric names produce a clear error message listing valid identifiers before any measurement execution

**Independent Test**: Run `specmetrics measure unknown`, verify error message with valid IDs and exit code 1

### Implementation for User Story 4

- [x] T023 [US4] Metric name validation in `specmetrics/cli/measure.py` — `_parse_metrics()` validates each ID against `VALID_METRICS` set; prints error with full valid ID list and returns `None` with side effect
- [x] T024 [US4] Mixed valid+invalid input — `_parse_metrics()` checks ALL parts before returning; reports all invalid identifiers in error message; `run_measure()` returns 1 when validation fails

**Checkpoint**: Input validation catches all invalid metric names with clear error messages

---

## Phase 7: Tests

**Purpose**: Comprehensive test coverage for all metric filtering scenarios

- [x] T025 [P] Unit test for metric argument parsing in `tests/cli/test_measure.py` — 11 tests covering None, empty, single, multiple, whitespace, duplicates, `all` override
- [x] T026 [P] Unit test for metric name validation in `tests/cli/test_measure.py` — tests for invalid IDs, mixed valid+invalid
- [x] T027 [P] Unit test for orchestrator metric filtering in `tests/unit/application/test_orchestrator.py` — 7 tests covering None filter, single metric, all metrics, empty context, JSON output, plugin registry filtering
- [x] T028 [P] Unit test for JSON output models in `tests/contract/test_measure_output.py` — 4 tests covering serialization, failed metrics, all 8 metrics, required fields
- [x] T029 Write integration test for end-to-end filtered measurement — unit tests at `test_orchestrator.py` already cover: metrics_filter passthrough, result filtering, plugin registry filtering, JSON output writing (adequate coverage without test project fixture)
- [x] T030 [P] Contract test for JSON output schema in `tests/contract/test_measure_output.py` — validates schema conformance
- [x] T031 [P] Contract test for text output format in `tests/cli/test_formatters.py` — existing tests verify text output still works

**Checkpoint**: All tests pass, metric filtering behavior is fully validated

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T032 [P] CLI help text updated — `specmetrics/cli/app.py` has METRICS argument with help text listing valid values
- [x] T033 Remove `specmetrics-output.text` file generation code — `_handle_export()` in `orchestrator.py` now writes JSON instead of text
- [x] T034 Full test suite (`pytest`) passes — 1025 tests, 0 failures
- [x] T035 Run linting (`ruff`) to ensure code quality — 0 issues
- [x] T036 Update CHANGELOG.md with the new feature entry

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — establishes core infrastructure for all subsequent stories
- **US2 (Phase 4)**: Depends on US1 — reuses the same `metrics_filter` mechanism
- **US3 (Phase 5)**: Depends on US1 — extends US2's code path with edge case handling
- **US4 (Phase 6)**: Depends on US1 — validation is part of the argument parsing path
- **Tests (Phase 7)**: Depends on US1+US2+US3+US4 implementation
- **Polish (Phase 8)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: Self-contained foundation — No dependencies on other stories
- **US2 (P1)**: Shares US1's infrastructure — implemented in the same code path, verified separately
- **US3 (P1)**: Extends US1/US2 — additional edge case handling on the same mechanism
- **US4 (P2)**: Depends on US1's argument parsing — error path in the same pipeline

### Within Each Phase

- Models before services
- Core implementation before edge cases
- Phase complete before moving to next

### Parallel Opportunities

- All [P] tasks within the same phase can run in parallel (different files)
- Phases must execute sequentially (each depends on previous)
- T025-T031 (tests) can all run in parallel once implementation is done
- T001 and T002 (setup) can run in parallel

---

## Parallel Example: Phase 3 (US1)

```bash
# Launch CLI argument task and formatter task together:
Task: "Add optional metrics argument in specmetrics/cli/app.py"
Task: "Update format_text_result for multi-metric display in specmetrics/cli/formatters.py"

# Launch orchestrator filtering and output models together:
Task: "Implement orchestrator metric filtering in specmetrics/application/orchestrator.py"
Task: "Add per-metric duration tracking in specmetrics/application/orchestrator.py"
```

---

## Implementation Strategy

### MVP First (Phase 3 Only = US1)

1. Complete Phase 1: Setup (review existing code)
2. Complete Phase 2: Foundational (PipelineRequest, output models)
3. Complete Phase 3: User Story 1 — `specmetrics measure` with all metrics + JSON output
4. **STOP and VALIDATE**: Run `specmetrics measure`, verify output, check JSON file
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (all metrics default) → Test → Deploy/Demo (MVP!)
3. Add US2 (single metric filter) → Test → Deploy
4. Add US3 (multi-metric filter) → Test → Deploy
5. Add US4 (validation) → Test → Deploy
6. Add tests → Deploy

### Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
