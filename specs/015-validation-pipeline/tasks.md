# Tasks: Validation Pipeline

**Input**: Design documents from `/specs/015-validation-pipeline/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in spec — test tasks excluded. Testing covered separately in quickstart.md.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/cli/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the validation module directory structure and package initialization

- [x] T001 Create `specmetrics/kernel/validation/` package with `__init__.py`
- [x] T002 Create `specmetrics/kernel/validation/rules/` package with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and shared infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Create SpecificationDocument model in `specmetrics/kernel/validation/models.py`
- [x] T004 [P] Create ValidationRule model in `specmetrics/kernel/validation/models.py`
- [x] T005 [P] Create ValidationResult model with EvidenceRef in `specmetrics/kernel/validation/models.py`
- [x] T006 [P] Create ValidationReport and ReportSummary models in `specmetrics/kernel/validation/models.py`
- [x] T007 Define RuleCategory and RuleSeverity enums in `specmetrics/kernel/validation/models.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Run validation on a specification (Priority: P1) 🎯 MVP

**Goal**: Users can validate a single specification document and receive pass/fail results with actionable details

**Independent Test**: Provide a valid spec document → pipeline reports PASS; provide invalid spec → pipeline reports FAIL with specific issues

### Implementation for User Story 1

- [x] T008 [P] [US1] Implement FORMAT rules (`file-readable`, `file-not-empty`, `parseable-markdown`) in `specmetrics/kernel/validation/rules/structural.py`
- [x] T009 [P] [US1] Implement STRUCTURAL rule `mandatory-sections-exist` in `specmetrics/kernel/validation/rules/structural.py`
- [x] T010 [P] [US1] Implement STRUCTURAL rule `no-unknown-sections` in `specmetrics/kernel/validation/rules/structural.py`
- [x] T011 [US1] Implement ValidationPipeline single-document `run()` method in `specmetrics/kernel/validation/pipeline.py`
- [x] T012 [US1] Implement rule loading from plugin discovery in `specmetrics/kernel/validation/pipeline.py`
- [x] T013 [US1] Add `specmetrics validate` CLI subcommand with single-spec mode in `specmetrics/cli/commands/validate.py`
- [x] T014 [US1] Wire CLI command with Typer app in `specmetrics/cli/app.py`
- [x] T015 [US1] Implement text output formatter for pass/fail results in `specmetrics/cli/commands/validate.py`
- [x] T016 [US1] Implement error handling for edge cases (empty file, unreadable file, bad encoding) in `specmetrics/kernel/validation/pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — `specmetrics validate <spec.md>` works and reports pass/fail

---

## Phase 4: User Story 2 — Validate constitutional compliance (Priority: P2)

**Goal**: Contributors can verify that a specification complies with the project's constitutional principles before submitting for review

**Independent Test**: Provide a spec that violates a constitutional principle → pipeline flags the violation; provide a compliant spec → reports PASS

### Implementation for User Story 2

- [x] T017 [P] [US2] Implement `constitution-engaged` rule in `specmetrics/kernel/validation/rules/constitutional.py`
- [x] T018 [P] [US2] Implement `constitution-compliance-notes` rule in `specmetrics/kernel/validation/rules/constitutional.py`
- [x] T019 [US2] Add `--constitution-only` and `--structural-only` CLI flags in `specmetrics/cli/commands/validate.py`
- [x] T020 [US2] Implement constitutional check routing in `specmetrics/kernel/validation/pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently — `specmetrics validate --constitution-only <spec.md>` checks constitutional compliance

---

## Phase 5: User Story 3 — Batch-validate multiple specifications (Priority: P3)

**Goal**: Project maintainers can validate all pending specifications in a batch and receive a summary report

**Independent Test**: Provide a directory with several spec files (some valid, some invalid) → batch report correctly summarizes each result

### Implementation for User Story 3

- [x] T021 [US3] Implement `run_batch()` method in ValidationPipeline in `specmetrics/kernel/validation/pipeline.py`
- [x] T022 [US3] Create BatchReport model in `specmetrics/kernel/validation/models.py`
- [x] T023 [US3] Implement directory scanning for spec files in `specmetrics/kernel/validation/pipeline.py`
- [x] T024 [US3] Add `--batch` CLI flag and batch output formatting in `specmetrics/cli/commands/validate.py`
- [x] T025 [US3] Implement JSON output format (`--format json`) for CI/CD integration in `specmetrics/cli/commands/validate.py`
- [x] T026 [US3] Implement non-zero exit code on validation failure (FR-010) in `specmetrics/cli/commands/validate.py`
- [x] T027 [US3] Add `--rules` flag for custom rule configuration file in `specmetrics/cli/commands/validate.py`

**Checkpoint**: All user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T028 [P] Create sample `.specify/validation-rules.yml` configuration file
- [x] T029 Integrate validation into pipeline engine as pre-measurement gate in `specmetrics/kernel/pipeline_engine.py`
- [x] T030 Add structured logging for all validation operations using structlog
- [x] T031 Run quickstart.md validation scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - US2 (P2) has NO dependency on US1 — can proceed in parallel
  - US3 (P3) has NO dependency on US1 or US2 — can proceed in parallel
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational — Independent of US1
- **User Story 3 (P3)**: Can start after Foundational — Independent of US1 and US2

### Within Each User Story

- Models before pipeline logic
- Pipeline logic before CLI wiring
- Core implementation before edge cases

### Parallel Opportunities

- T003-T007 (models): All marked [P], can run in parallel
- T008-T010 (rules): All marked [P], can run in parallel
- All user stories can run in parallel after Phase 2 completes
- T017-T018 (constitutional rules): Parallel within US2
- T028 (config) can run in parallel with any user story

---

## Parallel Example: User Story 1

```bash
# Launch all format+structural rules together:
Task: "T008 Create FORMAT rules in specmetrics/kernel/validation/rules/structural.py"
Task: "T009 Create mandatory-sections-exist rule in specmetrics/kernel/validation/rules/structural.py"
Task: "T010 Create no-unknown-sections rule in specmetrics/kernel/validation/rules/structural.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: `specmetrics validate specs/015-validation-pipeline/spec.md`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 — MVP)
   - Developer B: User Story 2 (P2 — constitutional checks)
   - Developer C: User Story 3 (P3 — batch validation)
3. Stories are independent, no integration conflicts

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No test task generation — tests not requested in spec (see quickstart.md for manual validation scenarios)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
