# Tasks: Measurement Engine Plugin — Story Points (Modified Fibonacci)

**Input**: Design documents from `specs/024-measurement-engine-storypoints/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/`, `specmetrics/tests/` at repository root
- Paths follow the project structure from `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create package directories for the new plugin and tests

- [ ] T001 Create `specmetrics/plugins/measurement/storypoints/` package with `__init__.py`
- [ ] T002 Create test directories: `tests/unit/`, `tests/contract/`, `tests/integration/` if not already present

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, factor scorer, normalizer, calculator, explainer — MUST complete before any user story

### Models

- [ ] T003 [P] Create all measurement models (`StoryPointMeasurementResult`, `FunctionalWorkItem`, `RawEffortScore`, `StoryPointEstimate`, `MeasurementEvidence`, `ExecutionMetadata`, `MeasurementWarning`, `EvidenceRef`) in `specmetrics/plugins/measurement/storypoints/models.py`

### Scorers & Normalizer

- [ ] T004 [P] Create factor scorer with default scoring rules for all 6 factors (business_interactions, logical_information, external_integrations, business_rule_density, workflow_breadth, exception_handling) using CFM element relationships in `specmetrics/plugins/measurement/storypoints/factor_scorer.py`
- [ ] T005 [P] Create Fibonacci normalizer with configurable threshold table and default scale (1, 2, 3, 5, 8, 13, 20, 40, 100) in `specmetrics/plugins/measurement/storypoints/normalizer.py`

### Calculator & Explainer

- [ ] T006 Create core calculator in `specmetrics/plugins/measurement/storypoints/calculator.py` — `calculate(cfm) -> StoryPointMeasurementResult`: deduplicate Functional Processes by SHA-256 fingerprint, score each via factor_scorer, apply default coefficients, sum for raw_score, normalize via normalizer, aggregate distribution
- [ ] T007 Create explainer in `specmetrics/plugins/measurement/storypoints/explainer.py` — per-item factor_breakdown, evidence_refs assembly, top-contributor ranking

### Package Wiring

- [ ] T008 Wire up `specmetrics/plugins/measurement/storypoints/__init__.py` to export `StoryPointMeasurementResult`, `StoryPointsPlugin`, `create_storypoints_measurement_metadata`

**Parallel opportunities**: T003, T004, T005 are independent. T006 depends on T003–T005. T007 depends on T003.

**Checkpoint**: Foundation ready — all models, scoring, normalization, and calculation logic exist.

---

## Phase 3: User Story 1 — Automatic Story Point Estimation (Priority: P1) 🎯 MVP

**Goal**: Project manager runs `specmetrics measure --method storypoints` and receives deterministic Story Point estimates for every Functional Process in the CFM.

**Independent Test**: `pytest tests/unit/test_storypoints_calculator.py -v -k test_estimate_from_known_cfm`

### Tests for User Story 1

- [ ] T009 [P] [US1] Unit test for model construction, serialization, and validation rules in `tests/unit/test_storypoints_models.py`
- [ ] T010 [P] [US1] Unit test for factor scorer — each of 6 factors scores correctly from CFM relationships, zero when no related elements in `tests/unit/test_storypoints_factor_scorer.py`
- [ ] T011 [P] [US1] Unit test for normalizer — raw scores map to correct Fibonacci values (1,2,3,5,8,13,20,40,100), clamping at bounds in `tests/unit/test_storypoints_normalizer.py`
- [ ] T012 [P] [US1] Unit test for calculator — known CFM produces expected Story Points with correct distribution in `tests/unit/test_storypoints_calculator.py`
- [ ] T013 [P] [US1] Unit test for determinism — identical CFM produces identical results in `tests/unit/test_storypoints_calculator.py`
- [ ] T014 [P] [US1] Unit test for empty CFM — zero items, zero total, no errors in `tests/unit/test_storypoints_calculator.py`
- [ ] T015 [P] [US1] Unit test for duplicate merging — identical content fingerprints merged, count tracked in metadata in `tests/unit/test_storypoints_calculator.py`

### Implementation for User Story 1

- [ ] T016 [US1] Create Story Points plugin (`StoryPointsPlugin`, `StoryPointsHandler`, `create_storypoints_measurement_metadata`) in `specmetrics/plugins/measurement/storypoints/plugin.py` — handler subscribes to `MEASUREMENT_COMPLETED`, reads CFM from context, invokes calculator, stores result payload
- [ ] T017 [US1] Register Story Points entry point in `pyproject.toml` under `specmetrics.plugins.measurement`

**Checkpoint**: US1 is fully functional — the pipeline produces deterministic Story Point estimates from any CFM.

---

## Phase 4: User Story 2 — Explainable Estimation (Priority: P1)

**Goal**: Reviewer inspects why a backlog item received a specific Story Point value, with full traceability to CFM elements, factors, and applied rules.

**Independent Test**: `pytest tests/contract/test_storypoints_measurement.py -v`

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for explainer — per-item factor_breakdown, evidence_refs assembly, top-contributor identification in `tests/unit/test_storypoints_calculator.py`
- [ ] T019 [P] [US2] Unit test for every estimated item preserving evidence reference in `tests/unit/test_storypoints_models.py`
- [ ] T020 [US2] Contract test for measurement API — verify plugin metadata, handler event type, result schema, factor_breakdown per FR-027 in `tests/contract/test_storypoints_measurement.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement explainer detail per FR-027 — factor_breakdown, evidence_refs, applied_rules, top contributors sorting in `specmetrics/plugins/measurement/storypoints/explainer.py`

**Checkpoint**: US2 is fully functional — every estimate includes originating CFM node, factor breakdown, evidence traceability, and applied rules.

---

## Phase 5: User Story 3 — Organizational Calibration (Priority: P2)

**Goal**: Company customizes estimation via Rule Packs — adjusts factor coefficients and normalization thresholds.

**Independent Test**: `pytest tests/unit/test_storypoints_calculator.py -v -k test_rule_pack_overrides`

### Tests for User Story 3

- [ ] T022 [P] [US3] Unit test for factor coefficient overrides via Rule Pack — custom coefficients produce different raw scores in `tests/unit/test_storypoints_calculator.py`
- [ ] T023 [P] [US3] Unit test for normalization threshold overrides via Rule Pack — custom thresholds produce different Fibonacci mappings in `tests/unit/test_storypoints_normalizer.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement Rule Pack override integration in calculator — read coefficient overrides and threshold overrides from CFM element metadata annotations in `specmetrics/plugins/measurement/storypoints/calculator.py`

**Checkpoint**: US3 is fully functional — organizations can customize factor coefficients and normalization thresholds through Rule Packs without code changes.

---

## Phase 6: User Story 4 — Pipeline Integration (Priority: P2)

**Goal**: Plugin is automatically discovered and executes after Rule Pack processing within the standard SpecMetrics pipeline.

**Independent Test**: `pytest tests/integration/test_storypoints_pipeline.py -v`

### Tests for User Story 4

- [ ] T025 [US4] Integration test for pipeline — CFM → Story Points stored in `ctx.measurement_result` with correct payload, plugin auto-discovered via entry point in `tests/integration/test_storypoints_pipeline.py`

### Implementation for User Story 4

- [ ] T026 [US4] Implement OpenTelemetry metrics — duration histogram, estimated items gauge, distribution histogram following SFP pattern in `specmetrics/plugins/measurement/storypoints/plugin.py`

**Checkpoint**: US4 is fully functional — plugin auto-discovers, executes in pipeline, and emits observability metrics.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Run full test suite — verify `pytest tests/unit/test_storypoints_*.py tests/contract/test_storypoints_measurement.py tests/integration/test_storypoints_pipeline.py` all pass
- [ ] T028 [P] Run performance benchmark — verify SC-003 (500 FPs in under 5 seconds) with `pytest tests/unit/test_storypoints_calculator.py -k test_performance_500_fps --benchmark-only`
- [ ] T029 [P] Run quickstart validation scenarios from `specs/024-measurement-engine-storypoints/quickstart.md`
- [ ] T030 Code cleanup — remove unused imports, verify `ruff check` passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational — can start in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational — coefficient overrides built on calculator
- **US4 (Phase 6)**: Depends on US1 (entry point registration) — needs plugin registered for discovery test
- **Polish (Phase 7)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — Independently testable via direct result construction
- **US3 (P2)**: Can start after Phase 2 — Independently testable by injecting overrides into calculator
- **US4 (P2)**: Depends on US1 (needs plugin registered to test discovery)

### Parallel Opportunities

- T003, T004, T005 in Phase 2 can run in parallel
- All 7 test tasks in US1 can run in parallel (T009–T015)
- US1, US2, and US3 can be developed in parallel after Phase 2 completes

---

## Parallel Example: User Story 1

```bash
# Launch all US1 tests together:
pytest tests/unit/test_storypoints_models.py tests/unit/test_storypoints_factor_scorer.py tests/unit/test_storypoints_normalizer.py tests/unit/test_storypoints_calculator.py -v &

# While tests run, start plugin implementation:
# (tasks T016, T017)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Package directories
2. Complete Phase 2: Foundational — Models, factor scorer, normalizer, calculator, explainer
3. Complete Phase 3: User Story 1 — Plugin handler, entry point, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_storypoints_*.py -v`
5. Deploy/demo if ready — provides core Story Point estimation

### Incremental Delivery

1. Setup + Foundational → Calculation infrastructure ready
2. Add US1 → Core Story Points estimation → **MVP!**
3. Add US2 → Explainability and factor breakdown → Transparency
4. Add US3 → Organizational calibration via Rule Packs → Customization
5. Add US4 → Pipeline integration + observability → Production readiness

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (plugin + pipeline + tests)
   - Developer B: User Story 2 (explainer + contract tests)
   - Developer C: User Story 3 (Rule Pack override tests)
3. When US1–US3 complete:
   - Developer A: User Story 4 (integration test + metrics)
   - Developer B: Polish (benchmark, quickstart validation)
