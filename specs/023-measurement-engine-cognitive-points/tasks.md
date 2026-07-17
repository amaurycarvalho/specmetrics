# Tasks: Measurement Engine Plugin — Cognitive Points

**Input**: Design documents from `specs/023-measurement-engine-cognitive-points/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/`, `specmetrics/tests/` at repository root
- Paths follow the project structure from `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package directories for the new plugin and tests

- [ ] T001 Create `specmetrics/plugins/measurement/cognitive_points/` package with `__init__.py`
- [ ] T002 Create test package directories: `tests/unit/`, `tests/contract/`, `tests/integration/` if not already present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, Bloom classifier, Fibonacci normalizer, calculator, calibration, and explainer — MUST complete before any user story

### Models & Classifier

- [ ] T003 [P] Create all measurement models (`CognitivePointsMeasurement`, `SpecificationReviewEffort`, `FunctionalValidationEffort`, `CognitiveContribution`, `FibonacciNormalizationResult`, `MeasurementMetadata`, `MeasurementWarning`) in `specmetrics/plugins/measurement/cognitive_points/models.py`
- [ ] T004 [P] Create Bloom classifier with default element-type-to-level mapping from FR-014a in `specmetrics/plugins/measurement/cognitive_points/bloom_classifier.py`
- [ ] T005 [P] Create Fibonacci normalizer with configurable threshold table and default scale (1, 3, 5, 8, 13, 20, 40, 100) in `specmetrics/plugins/measurement/cognitive_points/fibonacci_normalizer.py`

### Calibration

- [ ] T006 [P] Create `CognitiveCalibrationProfile`, `BloomClassification`, `FibonacciNormalizationProfile` models with built-in defaults in `specmetrics/plugins/measurement/cognitive_points/calibration.py`
- [ ] T007 Create calibration YAML loader in `specmetrics/plugins/measurement/cognitive_points/calibration.py` — parse with ruamel.yaml, merge overrides onto built-in defaults

### Calculator & Explainer

- [ ] T008 Create core three-stage calculator in `specmetrics/plugins/measurement/cognitive_points/calculator.py` — `calculate(cfm, csm, calibration) -> CognitivePointsMeasurement`: (1) classify each element via Bloom classifier, apply Bloom weight, sum per component, (2) add components for raw score, (3) normalize via Fibonacci normalizer
- [ ] T009 Create explainer in `specmetrics/plugins/measurement/cognitive_points/explainer.py` — build ranked contribution list, bloom_breakdown per component, identify top contributors per FR-023

### Package Wiring

- [ ] T010 Wire up `specmetrics/plugins/measurement/cognitive_points/__init__.py` to export `CognitivePointsMeasurement`, `CognitivePointsPlugin`, `create_cognitive_points_measurement_metadata`

**Parallel opportunities**: T003, T004, T005, T006 are independent. T008 depends on T003–T007. T009 depends on T003.

**Checkpoint**: Foundation ready — all models, classifiers, normalizer, calculator, and explainer exist and can be tested in isolation.

---

## Phase 3: User Story 1 — Estimate human cognitive effort (Priority: P1) 🎯 MVP

**Goal**: Technical leader executes the pipeline and receives a deterministic Cognitive Points measurement with Bloom classification, raw score, and Fibonacci-normalized result.

**Independent Test**: `pytest tests/unit/test_cognitive_points_calculator.py -v -k test_calculate_from_known_models`

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for measurement model construction, serialization, and validation rules in `tests/unit/test_cognitive_points_models.py`
- [ ] T012 [P] [US1] Unit test for Bloom classifier — each element type maps to correct level, unknown types use default, custom overrides in `tests/unit/test_cognitive_points_bloom.py`
- [ ] T013 [P] [US1] Unit test for Fibonacci normalizer — raw scores map to correct output values, boundary conditions, max clamping in `tests/unit/test_cognitive_points_normalizer.py`
- [ ] T014 [P] [US1] Unit test for calculator — known CFM + CSM produces expected Cognitive Points via three-stage formula in `tests/unit/test_cognitive_points_calculator.py`
- [ ] T015 [P] [US1] Unit test for determinism — identical inputs produce identical results in `tests/unit/test_cognitive_points_calculator.py`
- [ ] T016 [P] [US1] Unit test for graceful degradation — missing CSM produces 0 specification review effort + warning in `tests/unit/test_cognitive_points_calculator.py`
- [ ] T017 [P] [US1] Unit test for calibration loading — default weights loaded, YAML overrides specific keys in `tests/unit/test_cognitive_points_calibration.py`

### Implementation for User Story 1

- [ ] T018 [US1] Create Cognitive Points plugin (`CognitivePointsPlugin`, `CognitivePointsHandler`, `create_cognitive_points_measurement_metadata`) in `specmetrics/plugins/measurement/cognitive_points/plugin.py` — handler subscribes to `MEASUREMENT_COMPLETED`, reads CFM and CSM from context, invokes calculator, stores result payload
- [ ] T019 [US1] Register Cognitive Points entry point in `pyproject.toml` under `specmetrics.plugins.measurement`

**Checkpoint**: US1 is fully functional — the pipeline can produce deterministic Cognitive Points with Bloom classification and Fibonacci normalization.

---

## Phase 4: User Story 2 — Understand sources of cognitive complexity (Priority: P1)

**Goal**: Specification reviewer inspects the report and sees every contribution traceable to its canonical element, Bloom level, weight, and normalization.

**Independent Test**: `pytest tests/contract/test_cognitive_points_measurement.py -v`

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for explainer — ranked contribution list, bloom_breakdown per component, top contributors identified in `tests/unit/test_cognitive_points_calculator.py`
- [ ] T021 [P] [US2] Unit test for every contribution preserving evidence reference and Bloom level in `tests/unit/test_cognitive_points_models.py`
- [ ] T022 [US2] Contract test for measurement API — verify plugin metadata, handler event type, result schema, report structure per FR-023 in `tests/contract/test_cognitive_points_measurement.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `top_contributors` method in explainer and `bloom_breakdown` aggregation in `specmetrics/plugins/measurement/cognitive_points/explainer.py`

**Checkpoint**: US2 is fully functional — the report includes per-element Bloom classification, cognitive weights, and ranked top contributors.

---

## Phase 5: User Story 3 — Support delivery planning and team capacity forecasting (Priority: P2)

**Goal**: Scrum Master or Product Manager aggregates Cognitive Points across a backlog for capacity planning.

**Independent Test**: `pytest tests/integration/test_cognitive_points_pipeline.py -v`

### Tests for User Story 3

- [ ] T024 [P] [US3] Unit test for aggregation — summing multiple CognitivePointsMeasurement produces correct totals in `tests/unit/test_cognitive_points_calculator.py`
- [ ] T025 [US3] Integration test for pipeline — CFM + CSM → Cognitive Points stored in `ctx.measurement_result` with correct payload format in `tests/integration/test_cognitive_points_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `aggregate(measurements: list[CognitivePointsMeasurement]) -> CognitivePointsMeasurement` helper in `specmetrics/plugins/measurement/cognitive_points/models.py`

**Checkpoint**: US3 is fully functional — Cognitive Points measurements can be aggregated across multiple specifications for backlog-level capacity forecasting.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Run full test suite — verify `pytest tests/unit/test_cognitive_points_*.py tests/contract/test_cognitive_points_measurement.py tests/integration/test_cognitive_points_pipeline.py` all pass
- [ ] T028 [P] Run performance benchmark — verify SC-006 (500 elements in under 2 seconds) with `pytest tests/unit/test_cognitive_points_calculator.py -k test_performance_500_elements --benchmark-only`
- [ ] T029 [P] Run quickstart validation scenarios from `specs/023-measurement-engine-cognitive-points/quickstart.md`
- [ ] T030 Code cleanup — remove unused imports, verify `ruff check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational (calculator + models) — can start in parallel with US1
- **US3 (Phase 5)**: Depends on US1 (full pipeline integration)
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Explainability built on top of calculator; independently testable via direct result construction
- **US3 (P2)**: Depends on US1 for pipeline — aggregation logic can be developed against raw models

### Parallel Opportunities

- T003, T004, T005, T006 in Phase 2 can run in parallel
- All tests marked [P] within a phase can run in parallel
- US1 and US2 can be developed in parallel once Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch tests for US1 together:
pytest tests/unit/test_cognitive_points_models.py tests/unit/test_cognitive_points_bloom.py tests/unit/test_cognitive_points_normalizer.py tests/unit/test_cognitive_points_calculator.py tests/unit/test_cognitive_points_calibration.py -v &

# While those run, start the plugin implementation:
# (tasks T018, T019)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Package directories
2. Complete Phase 2: Foundational — Models, Bloom classifier, normalizer, calculator, calibration, explainer
3. Complete Phase 3: User Story 1 — Plugin handler, entry point, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_cognitive_points_*.py -v`
5. Deploy/demo if ready — provides core Cognitive Points estimation

### Incremental Delivery

1. Setup + Foundational → Calculation infrastructure ready
2. Add US1 → Core Cognitive Points in pipeline → **MVP!**
3. Add US2 → Explainability and Bloom breakdown → Trust and transparency
4. Add US3 → Aggregation for backlog capacity planning → Enterprise readiness

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (plugin + pipeline + tests)
   - Developer B: User Story 2 (explainer + contract tests)
3. When US1 + US2 complete:
   - Developer A: User Story 3 (aggregation + integration tests)
   - Developer B: Polish (benchmark, quickstart validation)
