# Tasks: Measurement Engine Plugin — Token Points

**Input**: Design documents from `specs/022-measurement-engine-token-points/`

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

**Purpose**: Create package directories for the new plugins

- [ ] T001 Create `specmetrics/plugins/measurement/token_points/` package with `__init__.py`
- [ ] T002 Create `specmetrics/plugins/calibration/` package with `__init__.py`

**Parallel opportunities**: T001 and T002 are independent.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, calibration framework, and calculation logic — MUST complete before any user story

### Models

- [ ] T003 [P] Create measurement models (`TokenPointsMeasurement`, `SpecificationCost`, `CodeGenerationCost`, `TokenContribution`, `MeasurementMetadata`, `MeasurementWarning`) in `specmetrics/plugins/measurement/token_points/models.py`
- [ ] T003a [P] Create Token Points calibration integration (built-in defaults, CalibrationProfile import/configuration) in `specmetrics/plugins/measurement/token_points/calibration.py`
- [ ] T004 [P] Create calibration models (`CalibrationProfile`, `SpecificationCostWeights`, `CodeGenerationCostWeights`) with all default weight values in `specmetrics/plugins/calibration/models.py`

### Calibration Plugin

- [ ] T005 [P] Create calibration YAML loader in `specmetrics/plugins/calibration/loader.py` — discover `.yml` files from `.specmetrics/calibration/`, parse with ruamel.yaml, merge overrides onto built-in defaults
- [ ] T006 [P] Create calibration profile validator in `specmetrics/plugins/calibration/validator.py` — validate required keys, value ranges (non-negative), version format
- [ ] T007 Create calibration plugin handler and metadata factory in `specmetrics/plugins/calibration/plugin.py` — subscribes to `RULE_PACK_APPLIED`, loads calibration, injects into context
- [ ] T008 Wire up `specmetrics/plugins/calibration/__init__.py` to export `CalibrationProfile`, `CalibrationPlugin`, `create_calibration_metadata`

### Calculator

- [ ] T009 Create core calculator in `specmetrics/plugins/measurement/token_points/calculator.py` — `calculate(cfm, csm, calibration) -> TokenPointsMeasurement` with O(n) single-pass iteration over CFM and CSM element collections, applying hierarchical weights, accumulating contributions into SpecificationCost and CodeGenerationCost
- [ ] T010 Create explainer in `specmetrics/plugins/measurement/token_points/explainer.py` — build ranked contribution list, identify top contributors, produce measurement breakdown per FR-018

**Parallel opportunities**: T003 and T004 are independent. T005, T006 are independent. T009, T010 depend on T003, T004.

**Checkpoint**: Foundation ready — all models, calibration loading, and calculation logic exist and can be tested in isolation.

---

## Phase 3: User Story 1 — Estimate AI computational cost (Priority: P1) 🎯 MVP

**Goal**: Technical leader executes the pipeline and receives a deterministic Token Points measurement with Specification Cost and Code Generation Cost.

**Independent Test**: `pytest tests/unit/test_token_points_calculator.py -v -k test_calculate_from_known_models`

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for measurement model construction, serialization, and validation rules in `tests/unit/test_token_points_models.py`
- [ ] T012 [P] [US1] Unit test for calculator — known CFM + CSM produces expected Token Points in `tests/unit/test_token_points_calculator.py`
- [ ] T013 [P] [US1] Unit test for determinism — identical inputs produce identical results in `tests/unit/test_token_points_calculator.py`
- [ ] T014 [P] [US1] Unit test for graceful degradation — missing CSM produces 0 specification cost + warning in `tests/unit/test_token_points_calculator.py`
- [ ] T015 [P] [US1] Unit test for empty CFM — Code Generation Cost is 0, Specification Cost calculated from CSM in `tests/unit/test_token_points_calculator.py`
- [ ] T016 [US1] Unit test for calibration loading — default weights loaded, YAML overrides specific keys in `tests/unit/test_token_points_calibration.py`

### Implementation for User Story 1

- [ ] T017 [US1] Create Token Points plugin (`TokenPointsPlugin`, `TokenPointsHandler`, `create_token_points_measurement_metadata`) in `specmetrics/plugins/measurement/token_points/plugin.py` — handler subscribes to `MEASUREMENT_COMPLETED`, reads CFM and CSM from context, invokes calculator, stores result payload
- [ ] T018 [US1] Wire up `specmetrics/plugins/measurement/token_points/__init__.py` to export `TokenPointsMeasurement`, `TokenPointsPlugin`, `create_token_points_measurement_metadata`
- [ ] T019 [US1] Register Token Points entry point in `pyproject.toml` under `specmetrics.plugins.measurement`

**Checkpoint**: US1 is fully functional — the pipeline can produce deterministic Token Points from CFM + CSM with graceful degradation when CSM is absent.

---

## Phase 4: User Story 2 — Understand where token consumption originates (Priority: P1)

**Goal**: Software architect inspects a Token Points report and sees every contribution traceable to specific canonical elements.

**Independent Test**: `pytest tests/contract/test_token_points_measurement.py -v`

### Tests for User Story 2

- [ ] T020 [P] [US2] Unit test for explainer — ranked contribution list, top contributors identified in `tests/unit/test_token_points_calculator.py`
- [ ] T021 [P] [US2] Unit test for every contribution preserving evidence reference in `tests/unit/test_token_points_models.py`
- [ ] T022 [US2] Contract test for measurement API — verify plugin metadata, handler event type, result schema conformance in `tests/contract/test_token_points_measurement.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement `top_contributors` method in explainer to return ranked list sorted by partial_score in `specmetrics/plugins/measurement/token_points/explainer.py`

**Checkpoint**: US2 is fully functional — the Token Points report includes per-element traceability, applied weights, and ranked top contributors.

---

## Phase 5: User Story 3 — Support planning and AI budget forecasting (Priority: P2)

**Goal**: Product Manager aggregates Token Points across multiple specifications for backlog-level AI budget estimation.

**Independent Test**: `pytest tests/integration/test_token_points_pipeline.py -v`

### Tests for User Story 3

- [ ] T024 [P] [US3] Unit test for aggregation — summing multiple TokenPointsMeasurement produces correct totals in `tests/unit/test_token_points_calculator.py`
- [ ] T025 [US3] Integration test for pipeline — CFM + CSM → Token Points stored in `ctx.measurement_result` with correct payload format in `tests/integration/test_token_points_pipeline.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `aggregate(measurements: list[TokenPointsMeasurement]) -> TokenPointsMeasurement` helper in `specmetrics/plugins/measurement/token_points/models.py`

**Checkpoint**: US3 is fully functional — Token Points measurements can be aggregated across multiple specifications, enabling backlog-level budget forecasting.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Run full test suite — verify `pytest tests/unit/test_token_points_*.py tests/contract/test_token_points_measurement.py tests/integration/test_token_points_pipeline.py` all pass
- [ ] T028 [P] Run performance benchmark — verify SC-006 (500 elements in under 2 seconds) with `pytest tests/unit/test_token_points_calculator.py -k test_performance_500_elements --benchmark-only`
- [ ] T029 [P] Run quickstart validation scenarios from `specs/022-measurement-engine-token-points/quickstart.md`
- [ ] T030 Code cleanup — remove unused imports, verify `ruff check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational (calculator + models) — can start in parallel with US1
- **US3 (Phase 5)**: Depends on US1 (full pipeline integration) — needs pipeline running
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Explainability built on top of calculator output; independently testable via direct result construction
- **US3 (P2)**: Depends on US1 for pipeline integration — aggregation logic can be developed against raw models independently

### Parallel Opportunities

- T001 and T002 in Phase 1 can run in parallel
- T003 and T004 in Phase 2 can run in parallel
- T005 and T006 in Phase 2 can run in parallel
- T009 and T010 depend on T003/T004 but are independent of each other
- All tests marked [P] within a phase can run in parallel
- US1 and US2 can be developed in parallel once Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch tests for US1 together:
pytest tests/unit/test_token_points_models.py tests/unit/test_token_points_calculator.py tests/unit/test_token_points_calibration.py -v &

# While those run, start the plugin implementation:
# (tasks T017, T018)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Package directories
2. Complete Phase 2: Foundational — All models, calibration, calculator, explainer
3. Complete Phase 3: User Story 1 — Plugin handler, entry point registration, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_token_points_*.py -v`
5. Deploy/demo if ready — provides core Token Points estimation

### Incremental Delivery

1. Setup + Foundational → Calculation infrastructure ready
2. Add US1 → Core Token Points measurement in pipeline → **MVP!**
3. Add US2 → Explainability and ranked breakdown → Trust and transparency
4. Add US3 → Aggregation for backlog planning → Enterprise readiness
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (plugin + pipeline integration + tests)
   - Developer B: User Story 2 (explainer + contract tests)
3. When US1 + US2 complete:
   - Developer A: User Story 3 (aggregation + integration tests)
   - Developer B: Polish (benchmark, quickstart validation)
