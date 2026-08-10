# Tasks: Refactor Pipeline Orchestrator for Maintainability

**Input**: Design documents from `/specs/045-refactor-orchestrator-mi/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Existing tests are the regression suite and MUST pass unmodified (FR-006). The feature spec does NOT request new tests; validation is driven by the quality gate, the existing test suite, and the run-artifact equivalence check (see quickstart.md). No new test tasks are generated (per the tests-are-optional rule). New unit coverage for extracted units is only added in the Polish phase IF a gate shows an uncovered gap.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/application/`, `specmetrics/cli/`, `specmetrics/mcp/`, `specmetrics/kernel/` at repository root
- This feature ONLY touches `specmetrics/application/` (per plan.md structure decision / spec Assumptions). No changes to `specmetrics/models.py` wait — models stay in `specmetrics/application/models.py` UNCHANGED.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Baseline capture and environment readiness for the refactor

- [X] T001 Verify development environment: `.venv` exists with `radon`, `pytest`, `ruff`, `flake8`, `xenon`, `lizard` installed (run `make install-quality-tools` if needed)
- [X] T002 [P] Capture baseline maintainability evidence: record current `radon mi -s specmetrics/application/orchestrator.py` (expected `C (0.00)`) and current `make test` status into `specs/045-refactor-orchestrator-mi/research.md` (baseline section)
- [X] T003 [P] Confirm feature branch/worktree `045-refactor-orchestrator-mi` is active (matches plan.md) before making changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared low-risk helper modules extracted first; all user-story units depend on these

**⚠️ CRITICAL**: No user story decomposition work may begin until these pure helpers exist

- [X] T004 [P] Create `specmetrics/application/truncation.py` with `_truncate_text(text, max_len=200)` and `_truncate_entities(entities, max_per_stage, per_category=False)` moved verbatim from `specmetrics/application/orchestrator.py` (keep `_TRUNCATE_TEXT_LENGTH = 200`)
- [X] T005 [P] Create `specmetrics/application/stage_mapping.py` with `_STAGE_NAME_TO_EVENT`, `_STAGE_NAME_TO_HANDLER_NAMES` constants and `_stage_name_from_event(event_type)`, `_resolve_event_order(stages, from_stage)`, `_detect_framework(ctx)` moved verbatim from `specmetrics/application/orchestrator.py`

**Checkpoint**: Pure helpers available; user story extraction can now begin in parallel

---

## Phase 3: User Story 1 - Quality gate passes for the orchestrator module (Priority: P1)

**Goal**: Decompose the 1,095-line orchestrator into single-responsibility units so the module scores **MI > 30** (blocking threshold) on the radon-based gate. This is the core deliverable.

**Independent Test**: `make complexity` is green — `scripts/complexity_metrics.py` exits 0 with no `[Blocking] Maintainability Index` for the orchestrator (worst score >= 30).

### Implementation for User Story 1

- [X] T006 [P] [US1] Create `specmetrics/application/artifact_persistence.py` with `save_run_artifacts(project_path, measure_id, result, max_entities_per_stage=5000) -> Path`, `read_run_artifacts(run_dir) -> dict`, and `_serialize_stage_data(result, max_entities_per_stage=5000)` moved verbatim from `specmetrics/application/orchestrator.py`
- [X] T007 [P] [US1] Create `specmetrics/application/entity_builders.py` with `_build_stage_entities` and `_entities_for_{discover,extract,graph,csm,cfm,rule,measure,export}` plus `_coerce_element_{dict,obj,evidence}` moved verbatim from `specmetrics/application/orchestrator.py`
- [X] T008 [P] [US1] Create `specmetrics/application/metric_builders.py` with `_build_metric_results`, `_build_metric_entry`, `_metric_breakdown`, `_metric_warnings`, `_extract_measurement` moved verbatim from `specmetrics/application/orchestrator.py`
- [X] T009 [P] [US1] Create `specmetrics/application/stage_builders.py` with `_build_stage_results`, `_build_stage_details`, `_detail_count`, `_count_{discover,extract,graph,model_elements,measure}`, `_entities_for_stage`, `_stage_timing`, `_status_for_kernel`, `_duration_seconds` moved verbatim from `specmetrics/application/orchestrator.py`
- [X] T010 [P] [US1] Create `specmetrics/application/export_writer.py` with `_handle_export`, `_handle_structured_export`, `_write_json_output`, `_build_output_errors`, `_get_llm_info` moved verbatim from `specmetrics/application/orchestrator.py`, reusing `truncation.py` and `stage_mapping.py`
- [X] T011 [US1] Refactor `specmetrics/application/orchestrator.py` into a thin coordinator: keep `PipelineOrchestrator` public methods (`__init__`, `set_config_system`, `discover_plugins`, `list_plugins`, `get_version_info`, `execute`) and module-level `save_run_artifacts`/`read_run_artifacts` imports, delegating entity/metric/stage/export building to the new units
- [X] T012 [US1] Keep thin delegating wrappers `_build_metric_results(ctx, metrics_filter)` and `_write_json_output(request, ctx, export_dir, metric_results, stage_details, output_errors)` on `PipelineOrchestrator` in `specmetrics/application/orchestrator.py` (tests call them directly — see contracts/orchestrator-public-api.md and research.md)
- [X] T013 [US1] Verify MI gate: run `radon mi -s specmetrics/application/orchestrator.py` and `scripts/complexity_metrics.py`; confirm worst MI >= 30 and exit 0 (re-run `make complexity` to confirm no `[Blocking]` violation)

**Checkpoint**: At this point, User Story 1 is done — the module passes the maintainability gate while keeping tests wired to the same behavior.

---

## Phase 4: User Story 2 - Public behavior is preserved (Priority: P2)

**Goal**: Prove the refactor produces byte-for-byte identical results and identical failure semantics before/after.

**Independent Test**: `make test` passes 100% unmodified AND a before/after run-artifact diff on a sample project is empty (scenarios 2-4 in quickstart.md).

### Implementation for User Story 2

- [X] T014 [US2] Run the full existing suite unmodified: `make test` (or `pytest` with `--cov-fail-under=85`); all tests pass with zero test modifications (covers FR-006 and US-1/US-2 acceptance)
- [X] T015 [US2] Behavioral equivalence check: record a sample project's run artifacts (`<project>/.specmetrics/runs/<id>/`) before and after the refactor and `diff -r` them; confirm no differences in stages executed, metrics, stage entities, statuses, and error results (SC-003, SC-004)
- [X] T016 [US2] Verify error paths preserved: missing/invalid project path → `PipelineResult(FAILED, "Project path not found: ...")`; Kernel `PipelineError` → `FAILED` with error string; config load failure tolerated; optional plugin/adapter/exporter load failure warns-and-continues (FR-005, Edge Cases)

**Checkpoint**: At this point, User Stories 1 AND 2 both hold — refactor is safe and behaviorally equivalent.

---

## Phase 5: User Story 3 - The orchestrator remains easy to maintain (Priority: P3)

**Goal**: Confirm the orchestrator is a thin entry point with each responsibility locatable in its own cohesive unit and all externally consumed signatures unchanged.

**Independent Test**: Each FR-003 responsibility exists in its own module (data-model.md boundaries) and `specmetrics.application.orchestrator` still exposes `execute`/`list_plugins`/`discover_plugins`/`set_config_system`/`get_version_info`/`save_run_artifacts`/`read_run_artifacts` importably.

### Implementation for User Story 3

- [X] T017 [P] [US3] Import smoke test: confirm all CLI/MCP consumers (`specmetrics/cli/app.py`, `specmetrics/cli/measure.py`, `specmetrics/cli/plugins.py`, `specmetrics/cli/export_commands.py`, `specmetrics/mcp/tools/measure.py`, `specmetrics/mcp/tools/export.py`) still import `PipelineOrchestrator`/`save_run_artifacts`/`read_run_artifacts` without error (FR-004, US-3)
- [X] T018 [US3] Verify thin entry point: confirm `orchestrator.py` contains no large builder bodies — each responsibility delegates to its unit; update module docstring in `specmetrics/application/orchestrator.py` to reference the new unit layout
- [X] T019 [US3] Confirm each FR-003 responsibility is separately reviewable by checking the real files under `specmetrics/application/` match the unit boundaries in `data-model.md` (entity_builders, metric_builders, stage_builders, artifact_persistence, export_writer, stage_mapping, truncation)

**Checkpoint**: All user stories independently verified; the refactor is complete and maintainable.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Ensure the full quality gate and docs are green after the refactor

- [X] T020 [P] Run `ruff check .` and `flake8 --max-complexity=10 --select=B,A,D --extend-exclude=specmetrics/tests ./specmetrics/` and fix any lint issues in `specmetrics/application/`
- [X] T021 [P] Run `make complexity` (xenon, lizard, radon) and confirm no new blocking finding introduced by the extracted modules
- [X] T022 [P] Run duplication (`make duplication`) and mutation (`make mutation`) gates; fix any regression attributable to the refactor
- [X] T023 Run the full end-to-end gate: `make quality-gate` exits 0 (security/semgrep included)
- [X] T024 [P] Add minimal unit coverage in `tests/unit/application/` ONLY for extracted units that the existing suite does not reach (pragmatic gap-fill; see research.md on `_build_metric_results`/`_write_json_output` test coupling)
- [X] T025 Execute the quickstart.md validation scenarios end-to-end and confirm each expected outcome

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories (truncation + stage_mapping are imported by every extracted unit)
- **User Story 1 (Phase 3)**: Depends on Foundational completion; is the core refactor
- **User Story 2 (Phase 4)**: Depends on US1 completion (equivalence can only be verified once decomposed)
- **User Story 3 (Phase 5)**: Depends on US1 completion (separability of units)
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Core decomposition; gates US2 and US3
- **User Story 2 (P2)**: Requires US1 complete (verifies equivalence of the refactor)
- **User Story 3 (P3)**: Requires US1 complete (verifies separability/thin entry)

> Note: Unlike a greenfield feature where stories are independent, this refactor's stories are verification perspectives on the SAME decomposition. US1 produces the change; US2 and US3 verify it. They must run after US1, though US2 and US3 can be checked in parallel with each other.

### Within Each User Story

- Extracted units marked [P] are moved verbatim in parallel (each touches a distinct new file)
- US1: helpers (Foundational) → extracted units [P] → thin orchestrator → wrappers → MI verification
- US2: full-suite run → artifact diff → error-path checks
- US3: import smoke → thin-entry review → boundary confirmation
- Story complete before moving to next

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Foundational T004, T005 marked [P] can run in parallel
- US1 extraction T006-T010 marked [P] can run in parallel (each a distinct new file; no interdependencies)
- US2 and US3 verification tasks can run in parallel after US1
- Polish T020, T021, T022, T024, T025 marked [P] can run in parallel

---

## Parallel Example: User Story 1 (extraction units)

```bash
# Launch all extracted units together (each a distinct new file, no interdependencies):
Task: "Create specmetrics/application/artifact_persistence.py (T006)"
Task: "Create specmetrics/application/entity_builders.py (T007)"
Task: "Create specmetrics/application/metric_builders.py (T008)"
Task: "Create specmetrics/application/stage_builders.py (T009)"
Task: "Create specmetrics/application/export_writer.py (T010)"
```

Then single task (blocks): thin orchestrator (T011) + delegating wrappers (T012), then MI verification (T013).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline capture)
2. Complete Phase 2: Foundational (truncation + stage_mapping — CRITICAL, blocks all extraction)
3. Complete Phase 3: User Story 1 (extract units → thin orchestrator → verify MI > 30)
4. **STOP and VALIDATE**: confirm `make complexity`/`complexity_metrics.py` passes and `make test` still passes
5. This alone delivers the primary requirement (blocking gate resolved) and satisfies FR-001..FR-004 where testable by the gate

### Incremental Delivery

1. Setup + Foundational → helpers ready
2. Add User Story 1 (decomposition) → MI gate green → **MVP**
3. Add User Story 2 (equivalence evidence) → confirms behavior preservation (FR-002/FR-005)
4. Add User Story 3 (separability + thin entry) → confirms maintainability intent (FR-003/FR-004)
5. Polish → full `make quality-gate` + quickstart validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T005)
2. Once Foundational is done, extraction units T006-T010 can be split across developers (distinct new files)
3. A single developer sequences T011-T013 (thin orchestrator + wrappers + MI gate)
4. US2 (T014-T016) and US3 (T017-T019) verification can be split across two reviewers
5. Polish (T020-T025) consolidated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- All extraction tasks MUST move code **verbatim** (no behavior change) — FR-002
- Public signatures in contracts/orchestrator-public-api.md are frozen; do not alter
- Existing tests are never modified (FR-006); keep `_build_metric_results`/`_write_json_output` delegating wrappers on the class
- Commit after each task or logical group; stop at checkpoints to validate
- Avoid: behavior changes, edits to `specmetrics/application/models.py`/`enums.py`/`metrics_json.py`, new third-party deps, and changes to any test file