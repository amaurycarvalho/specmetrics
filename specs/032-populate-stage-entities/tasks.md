# Tasks: Populate Stage Entities on Run Artifacts

**Input**: Design documents from `specs/032-populate-stage-entities/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec — test tasks are excluded per template guidelines. Quickstart scenarios serve as validation criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/application/`, `specmetrics/infrastructure/config/`, `specmetrics/cli/` at repository root
- **Tests**: `tests/unit/`, `tests/integration/` at repository root
- Paths shown below reflect the existing project structure from plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Add `RunArtifactsSettings` to config schema in `specmetrics/infrastructure/config/schema.py` with `max_entities_per_stage: int = 5000`
- [x] T002 [P] Add `stage_entities: dict[str, list[dict]]` field to `PipelineResult` in `specmetrics/application/models.py`
- [x] T003 [P] Create `_build_stage_entities()` method in `PipelineOrchestrator` in `specmetrics/application/orchestrator.py` — maps `PipelineContext` data to per-stage entity dicts
- [x] T004 [P] Modify `_serialize_stage_data()` in `specmetrics/application/orchestrator.py` to read from `result.stage_entities` instead of only `result.metric_results`
- [x] T005 Wire config `max_entities_per_stage` through `PipelineOrchestrator.execute()` → `save_run_artifacts()` in `specmetrics/application/orchestrator.py`
- [x] T006 Handle skipped/failed stages: `stage_entities` entries MUST be `[]` when stage not executed, in `specmetrics/application/orchestrator.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Implement truncation logic in `_build_stage_entities()` — per-category for CSM/CFM (Option A), first-N for others; add `_truncated` and `_total_count` fields in `specmetrics/application/orchestrator.py`
- [x] T008 [P] Add 200-char truncation helper for `description`/`text`/`content` fields in entity serialization in `specmetrics/application/orchestrator.py`
- [x] T009 [P] Write unit tests for truncation logic in `tests/unit/test_truncation.py`

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Discover Stage Entities (Priority: P1) 🎯 MVP

**Goal**: `discover.json` entities contain each discovered document's `id`, `document_type`, and relative `path`

**Independent Test**: Run `specmetrics measure` on a project with `.sdd` files; verify `discover.json` has non-empty `entities` with correct fields

### Implementation for User Story 1

- [x] T010 [P] [US1] Implement discover entities serialization: iterate `adapter_result["documents"]`, produce `{id, document_type, path}` dicts in `_build_stage_entities()` in `specmetrics/application/orchestrator.py`
- [x] T011 [P] [US1] Handle empty discover result: when `adapter_result` has no documents, produce `[]` entities in `specmetrics/application/orchestrator.py`
- [x] T012 [US1] Wire discover entity data into `stage_entities["discover"]` in `PipelineOrchestrator.execute()` in `specmetrics/application/orchestrator.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — `discover.json` has populated entities

---

## Phase 4: User Story 2 — Extract Stage Entities (Priority: P1)

**Goal**: `extract.json` entities contain each extracted element's `id`, `type`, `content` (200 chars), `confidence`, and `evidence` reference

**Independent Test**: Run on a spec file with known statements; verify `extract.json` entities contain element types matching expected semantic categories

### Implementation for User Story 2

- [x] T013 [P] [US2] Implement extract entities serialization: iterate `extraction_result["results"]`, produce `{id, type, content, confidence, evidence}` dicts with 200-char truncation in `specmetrics/application/orchestrator.py`
- [x] T014 [P] [US2] Include `documents_processed` and `documents_skipped` summary entries alongside extracted elements in `specmetrics/application/orchestrator.py`
- [x] T015 [US2] Wire extract entity data into `stage_entities["extract"]` in `PipelineOrchestrator.execute()` in `specmetrics/application/orchestrator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — Graph, CSM, and CFM Stage Entities (Priority: P2)

**Goal**: `graph.json`, `csm.json`, and `cfm.json` entities contain categorized model entities with evidence references

**Independent Test**: Cross-reference entity IDs in `cfm.json` with node IDs in `graph.json` — they should trace back

### Implementation for User Story 3

- [x] T016 [P] [US3] Implement graph entities serialization: iterate `ctx.evidence_graph` nodes, produce `{id, node_type, semantic_type, document_id, section_id, text}` dicts; append summary entity with `edge_count` and `run_id` in `specmetrics/application/orchestrator.py`
- [x] T017 [P] [US3] Implement CSM entities serialization: for each of the 9 CSM categories, iterate dict and call `model_dump(mode="json")` with 200-char truncation on `description`; prepend `type` field identifying category in `specmetrics/application/orchestrator.py`
- [x] T018 [P] [US3] Implement CSM per-category truncation: keep first N entities per CSM category in `specmetrics/application/orchestrator.py`
- [x] T019 [P] [US3] Implement CFM entities serialization: for each of the 7 CFM categories, iterate dict and call `model_dump(mode="json")` with 200-char truncation on `description`; prepend `type` field identifying category in `specmetrics/application/orchestrator.py`
- [x] T020 [P] [US3] Implement CFM per-category truncation: keep first N entities per CFM category in `specmetrics/application/orchestrator.py`
- [x] T021 [US3] Wire graph entity data into `stage_entities["graph"]` in `specmetrics/application/orchestrator.py`
- [x] T022 [US3] Wire CSM entity data into `stage_entities["csm"]` in `specmetrics/application/orchestrator.py`
- [x] T023 [US3] Wire CFM entity data into `stage_entities["cfm"]` in `specmetrics/application/orchestrator.py`

**Checkpoint**: At this point, User Stories 1 through 3 should all work independently

---

## Phase 6: User Story 4 — Rule and Measure Stage Entities (Priority: P2)

**Goal**: `rule.json` entities contain applied Rule Pack info and modification summary; `measure.json` entities include breakdown data

**Independent Test**: Apply a known Rule Pack and verify `rule.json` contains the pack name and modification count

### Implementation for User Story 4

- [x] T024 [P] [US4] Implement rule entities serialization: read `ctx.canonical_model.metadata.applied_rules` and `vaf`; produce `{type, rule_pack_name, description, version}` and `{type, entities_modified, vaf_applied}` dicts in `specmetrics/application/orchestrator.py`
- [x] T025 [P] [US4] Implement measure entities breakdown enrichment: extract breakdown dicts from `ctx.measurement_result` for each metric that supports it; append `breakdown` field to existing metric entity in `specmetrics/application/orchestrator.py`
- [x] T026 [US4] Wire rule entity data into `stage_entities["rule"]` in `specmetrics/application/orchestrator.py`
- [x] T027 [US4] Wire measure entity data (with breakdown) into `stage_entities["measure"]` in `specmetrics/application/orchestrator.py`

**Checkpoint**: At this point, User Stories 1 through 4 should all work independently

---

## Phase 7: User Story 5 — Export Stage Entities (Priority: P3)

**Goal**: `export.json` entities contain exported file paths with format

**Independent Test**: Run with `--export --format csv` and verify `export.json` entities contain the exported CSV file path

### Implementation for User Story 5

- [x] T028 [P] [US5] Implement export entities serialization: iterate `ctx.exported_files`, produce `{format, path}` dicts in `specmetrics/application/orchestrator.py`
- [x] T029 [US5] Wire export entity data into `stage_entities["export"]` in `specmetrics/application/orchestrator.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Write integration test: run `specmetrics measure`, verify all 8 stage files have populated `entities` in `tests/integration/test_run_artifacts.py` (requires full environment)
- [x] T031 [P] Write unit test for `_serialize_stage_data()`: verify backward compatibility with empty entities in `tests/unit/test_serialize_stage_data.py`
- [x] T032 Add logging for truncation events when entities exceed `max_entities_per_stage` in `specmetrics/application/orchestrator.py`
- [ ] T033 Run quickstart.md validation scenarios and fix any issues (requires full environment)
- [ ] T034 Run `ruff check` and fix linting issues (requires project dependencies installed)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories 1-5 can proceed in parallel (they touch the same file `orchestrator.py` but different sections)
  - Or sequentially in priority order (US1 → US2 → US3 → US4 → US5)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (P1)**: Can start after Foundational — No dependencies on US1
- **US3 (P2)**: Can start after Foundational — No dependencies on US1/US2
- **US4 (P2)**: Can start after Foundational — Shares `ctx.canonical_model` data access but independently serialized
- **US5 (P3)**: Can start after Foundational — No dependencies on US1-US4

### Within Each User Story

- Entity dict construction before wiring into `stage_entities`
- Wire task depends on both entity construction tasks completing
- Implementation before integration

### Parallel Opportunities

- T001, T002, T003, T004, T006 (Setup) marked [P] — different files or independent sections
- T007 vs T008/T009 (Foundational) — T007 is sequential, T008/T009 are parallel
- All user stories marked [P] within each phase — parallel model construction
- All stories can be implemented in parallel (different `elif` branches in `_build_stage_entities()`)

---

## Parallel Example: User Story 1 (US1)

```bash
# Launch all entity construction tasks for US1 together:
Task: "T010 [P] [US1] Implement discover entities serialization in orchestrator.py"
Task: "T011 [P] [US1] Handle empty discover result in orchestrator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T009) — CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T010-T012)
4. **STOP and VALIDATE**: Run `specmetrics measure`, inspect `discover.json`
5. Deploy/demo if ready — discover entities provide immediate value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Discover) → Test independently → Deploy/Demo (MVP!)
3. Add US2 (Extract) → Test independently → Deploy/Demo
4. Add US3 (Graph + CSM + CFM) → Test independently → Deploy/Demo
5. Add US4 (Rule + Measure) → Test independently → Deploy/Demo
6. Add US5 (Export) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Discover) + US5 (Export)
   - Developer B: US2 (Extract) + US3 (Graph/CSM/CFM)
   - Developer C: US4 (Rule/Measure) + Polish tasks
3. Stories complete and integrate independently
4. All work converges in `_build_stage_entities()` — no file conflicts since each stage is a separate `elif` branch

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
