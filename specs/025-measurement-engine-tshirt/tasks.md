# Tasks: Measurement Engine Plugin — T-Shirt Sizing

**Input**: Design documents from `specs/025-measurement-engine-tshirt/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/`, `specmetrics/kernel/`, `specmetrics/tests/` at repository root
- Paths follow the project structure from `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package directories for the new plugin

- [X] T001 Create `specmetrics/plugins/measurement/tshirt/` package with `__init__.py`
- [X] T002 [P] Add `TSHIRT_CLASSIFICATION_COMPLETED` to `EventType` enum in `specmetrics/kernel/events.py`
- [X] T003 [P] Add `TSHIRT_CLASSIFICATION_COMPLETED` to `CANONICAL_EVENT_ORDER` after `MEASUREMENT_COMPLETED` in `specmetrics/kernel/pipeline_engine.py`

**Parallel opportunities**: T002 and T003 are independent.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, classifier, explainer — MUST complete before any user story

- [X] T004 [P] Create all measurement models (`TShirtMeasurementResult`, `FunctionalWorkItem`, `TShirtSize`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`) in `specmetrics/plugins/measurement/tshirt/models.py`
- [X] T005 Create classifier with default mapping table (FR-015) and validation rules (no gaps, no overlaps, non-empty ranges) in `specmetrics/plugins/measurement/tshirt/classifier.py`
- [X] T006 Create explainer in `specmetrics/plugins/measurement/tshirt/explainer.py` — per-item evidence_refs assembly, distribution aggregation, mapping_rule traceability
- [X] T007 Wire up `specmetrics/plugins/measurement/tshirt/__init__.py` to export `TShirtMeasurementResult`, `TShirtPlugin`, `create_tshirt_measurement_metadata`

**Parallel opportunities**: T004 and T005 are independent. T006 depends on T004.

**Checkpoint**: Foundation ready — all models, classifier, and explainer exist.

---

## Phase 3: User Story 1 — Automatic T-Shirt Classification (Priority: P1) 🎯 MVP

**Goal**: Product manager executes `specmetrics measure --method tshirt` and every work item receives a T-Shirt Size.

**Independent Test**: `pytest tests/unit/test_tshirt_classifier.py -v -k test_classify_from_known_sp`

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for model construction and serialization in `tests/unit/test_tshirt_models.py`
- [X] T009 [P] [US1] Unit test for classifier — default mapping produces correct sizes for all SP values (1→XS, 2→S, 3→S, 5→M, 8→M, 13→L, 20→XL, 40→XXL, 100→XXL) in `tests/unit/test_tshirt_classifier.py`
- [X] T010 [P] [US1] Unit test for classifier validation — overlapping ranges rejected, incomplete mapping rejected in `tests/unit/test_tshirt_classifier.py`
- [X] T011 [P] [US1] Unit test for determinism — identical SP input produces identical classifications in `tests/unit/test_tshirt_classifier.py`
- [X] T012 [P] [US1] Unit test for missing SP result — returns empty result with warnings in `tests/unit/test_tshirt_classifier.py`
- [X] T013 [P] [US1] Unit test for empty SP result — zero items, empty distribution, no errors in `tests/unit/test_tshirt_classifier.py`

### Implementation for User Story 1

- [X] T014 [US1] Create T-Shirt plugin (`TShirtPlugin`, `TShirtHandler`, `create_tshirt_measurement_metadata`) in `specmetrics/plugins/measurement/tshirt/plugin.py` — handler subscribes to `TSHIRT_CLASSIFICATION_COMPLETED`, reads `ctx.measurement_result`, invokes classifier, stores result payload
- [X] T015 [US1] Register T-Shirt entry point in `pyproject.toml` under `specmetrics.plugins.measurement`

**Checkpoint**: US1 is fully functional — the pipeline classifies every work item into a T-Shirt Size.

---

## Phase 4: User Story 2 — Explainable Classification (Priority: P1)

**Goal**: Reviewer understands why a work item received a specific T-Shirt Size via full SP and rule traceability.

**Independent Test**: `pytest tests/contract/test_tshirt_measurement.py -v`

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for explainer — per-item mapping_rule, evidence_refs, distribution aggregation in `tests/unit/test_tshirt_classifier.py`
- [X] T017 [US2] Contract test for measurement API — verify plugin metadata, handler event type, result schema per FR-025 in `tests/contract/test_tshirt_measurement.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement explainer detail per FR-025 — mapping_rule, story_point_value, evidence_refs, distribution in `specmetrics/plugins/measurement/tshirt/explainer.py`

**Checkpoint**: US2 is fully functional — every classification includes originating SP value, applied mapping rule, and evidence references.

---

## Phase 5: User Story 3 — Organizational Calibration (Priority: P2)

**Goal**: Company customizes the scale and mapping via Rule Packs.

**Independent Test**: `pytest tests/unit/test_tshirt_classifier.py -v -k test_custom_mapping`

### Tests for User Story 3

- [X] T019 [P] [US3] Unit test for custom mapping override — 5-level scale (XS–XL) with custom SP ranges in `tests/unit/test_tshirt_classifier.py`
- [X] T020 [P] [US3] Unit test for invalid override — rejected overlapping ranges, rejected incomplete mapping in `tests/unit/test_tshirt_classifier.py`

### Implementation for User Story 3

- [X] T021 [US3] Implement Rule Pack override integration in classifier — accept optional mapping override from CFM annotations, validate before applying in `specmetrics/plugins/measurement/tshirt/classifier.py`

**Checkpoint**: US3 is fully functional — organizations can replace the mapping table via Rule Packs without code changes.

---

## Phase 6: User Story 4 — Pipeline Integration (Priority: P2)

**Goal**: Plugin auto-discovers and executes after Story Points in the pipeline.

**Independent Test**: `pytest tests/integration/test_tshirt_pipeline.py -v`

### Tests for User Story 4

- [X] T022 [US4] Integration test for pipeline — CFM → Story Points → T-Shirt Sizing, `ctx.measurement_result` contains T-Shirt output, plugin auto-discovered via entry point in `tests/integration/test_tshirt_pipeline.py`

### Implementation for User Story 4

- [X] T023 [US4] Implement OpenTelemetry metrics — classification duration histogram, classified items gauge, distribution histogram following SFP pattern in `specmetrics/plugins/measurement/tshirt/plugin.py`

**Checkpoint**: US4 is fully functional — plugin auto-discovers, executes after Story Points, and emits observability metrics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T024 [P] Run full test suite — verify `pytest tests/unit/test_tshirt_*.py tests/contract/test_tshirt_measurement.py tests/integration/test_tshirt_pipeline.py` all pass
- [X] T025 [P] Run performance benchmark — verify SC-003 (500 FPs in under 1 second) with `pytest tests/unit/test_tshirt_classifier.py -k test_performance_500_fps --benchmark-only`
- [X] T026 [P] Run quickstart validation scenarios from `specs/025-measurement-engine-tshirt/quickstart.md`
- [X] T027 Code cleanup — remove unused imports, verify `ruff check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational — can start in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational — classifier overrides built on classifier
- **US4 (Phase 6)**: Depends on US1 (entry point + event registration needed)
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Independently testable
- **US3 (P2)**: Can start after Phase 2 — Independently testable
- **US4 (P2)**: Depends on US1 (needs event + handler registered)

### Parallel Opportunities

- T002 and T003 in Phase 1 can run in parallel
- T004 and T005 in Phase 2 can run in parallel
- All test tasks in US1 (T008–T013) can run in parallel
- US1, US2, and US3 can be developed in parallel after Phase 2

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
pytest tests/unit/test_tshirt_models.py tests/unit/test_tshirt_classifier.py -v &

# While tests run, start plugin implementation:
# (tasks T014, T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Package + infrastructure changes
2. Complete Phase 2: Foundational — Models, classifier, explainer
3. Complete Phase 3: User Story 1 — Plugin handler, entry point, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_tshirt_*.py -v`
5. Deploy/demo if ready — provides core T-Shirt classification

### Incremental Delivery

1. Setup + Foundational → Infrastructure + classification ready
2. Add US1 → Core T-Shirt classification → **MVP!**
3. Add US2 → Explainability and mapping traceability → Transparency
4. Add US3 → Custom mapping via Rule Packs → Flexibility
5. Add US4 → Pipeline integration + observability → Production readiness
