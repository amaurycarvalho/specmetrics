# Tasks: Story Points Improvements

**Input**: Design documents from `/specs/040-story-points-improvements/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included for each user story to validate acceptance criteria and protect against regressions. The existing test suite covers the current engine; all modified files need corresponding test updates.

**Organization**: Tasks are grouped by user story to enable incremental implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm environment and establish base state before modifications begin

- [X] T001 Run existing Story Points test suite to establish baseline: `pytest tests/unit/test_storypoints_*.py tests/contract/test_storypoints_measurement.py tests/integration/test_storypoints_pipeline.py -v`
- [X] T002 Document current baseline results (test count, coverage, any existing failures) for regression comparison

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data model changes and new infrastructure modules that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Rename `FunctionalWorkItem` to `WorkItem` and add new fields (`element_type`, `source_model`, `structural_score`, `content_tokens`, `content_score`, `rank_position`, `base_weight`) in `specmetrics/plugins/measurement/storypoints/models.py`
- [X] T004 [P] Add `total_raw_score`, `specification_effort_total`, `implementation_effort_total`, `content_multiplier`, `content_tokens_by_type`, `calibration_version` to `StoryPointMeasurementResult` in `specmetrics/plugins/measurement/storypoints/models.py`
- [X] T005 [P] Extend `ExecutionMetadata` with `total_elements_processed`, `cfm_elements_processed`, `csm_elements_processed`, `elements_without_base_weight` in `specmetrics/plugins/measurement/storypoints/models.py`
- [X] T006 [P] Add model validators for new constraints (`raw_score == structural_score + content_score`, source consistency, effort totals) in `specmetrics/plugins/measurement/storypoints/models.py`
- [X] T007 [P] Create `StoryPointsCalibrationProfile` model with all fields (`content_multiplier`, `factor_coefficients`, `csm_base_weights`, `cfm_base_weights`, `default_fallback_weight`, `fibonacci_scale`, `ranking_strategy`) with Pydantic defaults in `specmetrics/plugins/measurement/storypoints/calibrator.py`
- [X] T008 [P] Implement `get_default_calibration()` returning a `StoryPointsCalibrationProfile` with all documented defaults in `specmetrics/plugins/measurement/storypoints/calibrator.py`
- [X] T009 [P] Implement `load_calibration(calibration_dir)` loading and merging YAML calibration files into `StoryPointsCalibrationProfile` with backward-compatible defaults in `specmetrics/plugins/measurement/storypoints/calibrator.py`
- [X] T010 [P] Implement `count_tokens_for_element(name: str, description: str) -> int` wrapper that delegates to `specmetrics.kernel.token_utils.count_tokens` in `specmetrics/plugins/measurement/storypoints/token_counter.py`
- [X] T011 [P] Write unit tests for `StoryPointsCalibrationProfile` defaults, validation, and backward-compatible loading in `tests/unit/test_storypoints_calibrator.py`
- [X] T012 [P] Write unit tests for `count_tokens_for_element` with various inputs (empty, short, long, code blocks) in `tests/unit/test_storypoints_token_counter.py`
- [X] T013 Update `__init__.py` exports to include new symbols (`WorkItem`, `StoryPointsCalibrationProfile`, `count_tokens_for_element`) in `specmetrics/plugins/measurement/storypoints/__init__.py`

**Checkpoint**: Foundation ready — data models, calibration profile, and token counter are in place. User story implementation can now begin.

---

## Phase 3: User Story 1 - Content-Aware Estimation Reflects Specification Depth (Priority: P1) 🎯 MVP

**Goal**: Add content token contribution to the raw score formula for all elements. A functional process with a detailed description scores higher than an identically-structured one.

**Independent Test**: Run Story Points on two FPs with identical structure but one having 500 tokens vs 100 tokens. Verify `raw_score` difference equals `(500 - 100) * content_multiplier`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T014 [P] [US1] Write test in `tests/unit/test_storypoints_calculator.py` verifying that two FPs with identical factor counts but different description lengths produce different `raw_score` values proportional to token count difference
- [X] T015 [P] [US1] Write test in `tests/unit/test_storypoints_calculator.py` verifying `content_multiplier: 0.0` produces raw scores identical to current factor-only output
- [X] T016 [P] [US1] Write test in `tests/unit/test_storypoints_calculator.py` verifying FP with empty name/description has `content_tokens == 0` and `content_score == 0.0` but structural score still applies

### Implementation for User Story 1

- [X] T017 [US1] Update `calculate()` to compute `content_tokens` via `count_tokens_for_element(name, description)` for each element in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T018 [US1] Update per-element score computation to `raw_score = structural_score + (content_tokens * content_multiplier)` using multiplier from calibration defaults in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T019 [US1] Populate new `WorkItem` fields (`content_tokens`, `content_score`, `structural_score`, `source_model`, `element_type`) during item creation in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T020 [US1] Update `explainer.py` to surface content-based contributions in `build_explanation()` and `factor_breakdown_summary()` in `specmetrics/plugins/measurement/storypoints/explainer.py`
- [X] T021 [US1] Ensure existing tests in `tests/unit/test_storypoints_models.py` pass with renamed/new model fields (update test assertions for `WorkItem` constructor and validators)

**Checkpoint**: Content-based estimation works for functional processes. Backward compatibility verified (content_multiplier=0.0 matches old scores).

---

## Phase 4: User Story 2 - Complete Specification Scope Estimation (Priority: P1)

**Goal**: Extend estimation to CSM elements (activities, decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms, references) and non-process CFM elements (business rules, operations, data groups, relationships, actors).

**Independent Test**: Run Story Points on a specification with CSM and non-FP CFM elements. Verify they contribute to `specification_effort_total` and `implementation_effort_total`.

### Tests for User Story 2

- [X] T022 [P] [US2] Write test in `tests/unit/test_storypoints_calculator.py` verifying CSM elements (decisions, constraints, acceptance criteria) contribute to raw scores using base weights + content tokens
- [X] T023 [P] [US2] Write test in `tests/unit/test_storypoints_calculator.py` verifying non-FP CFM elements (business rules, operations, data groups, relationships, actors) contribute using base weights
- [X] T024 [P] [US2] Write test in `tests/unit/test_storypoints_calculator.py` verifying FP-only specification (no CSM, no non-FP CFM) still works as before
- [X] T025 [P] [US2] Write test in `tests/unit/test_storypoints_calculator.py` verifying CSM-only specification (no FPs) produces result with `"NO_FPS_FOUND"` warning

### Implementation for User Story 2

- [X] T026 [US2] Implement CSM element iteration: consume `CanonicalSpecificationModel` and iterate over all element containers (activities, decisions, assumptions, constraints, risks, open questions, acceptance criteria, glossary terms, references) in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T027 [US2] Implement non-FP CFM element iteration: iterate over `actors`, `business_rules`, `operations`, `data_groups`, `relationships` that are not already counted via FP associations in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T028 [US2] Apply `base_weight + (content_tokens * content_multiplier)` formula for each non-FP element, using default base weights from calibration in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T029 [US2] Generate `MeasurementWarning(code="NO_FPS_FOUND")` when zero functional processes are present in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T030 [US2] Generate `MeasurementWarning(code="UNKNOWN_ELEMENT_TYPE")` and use `default_fallback_weight` for element types not in base weight mappings in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T031 [US2] Update `plugin.py` to accept CSM alongside CFM: modify `StoryPointsHandler.handle()` to extract `PipelineContext.canonical_spec_model` and pass to calculator in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T032 [US2] Update `plugin.py` `measure()` signature to accept optional `csm: CanonicalSpecificationModel` parameter in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T033 [US2] Update integration test in `tests/integration/test_storypoints_pipeline.py` to provide both CFM and CSM fixtures and verify combined output

**Checkpoint**: All specification element types contribute to Story Points. CSM-only and FP-only edge cases handled.

---

## Phase 5: User Story 3 - Cross-Specification Implementation Effort Comparison (Priority: P1)

**Goal**: Replace fixed-threshold Fibonacci normalization with relative ranking. Expose `specification_effort_total`, `implementation_effort_total`, `total_raw_score`, and per-type token breakdowns in the output.

**Independent Test**: Run Story Points on two specs with 2:1 content volume ratio. Verify `total_raw_score` ratio between 1.3:1 and 3.0:1.

### Tests for User Story 3

- [X] T034 [P] [US3] Write test in `tests/unit/test_storypoints_normalizer.py` verifying percentile-band ranking: 9 entities with ascending raw scores map to [1,2,3,5,8,13,20,40,100] in order
- [X] T035 [P] [US3] Write test in `tests/unit/test_storypoints_normalizer.py` verifying fewer than 9 entities (e.g., 3 entities) get direct rank-to-Fibonacci mapping (lowest→1, middle→8, highest→100)
- [X] T036 [P] [US3] Write test in `tests/unit/test_storypoints_normalizer.py` verifying custom `fibonacci_scale` produces valid distribution
- [X] T037 [P] [US3] Write test in `tests/unit/test_storypoints_calculator.py` verifying `specification_effort_total` and `implementation_effort_total` sum to `total_raw_score`
- [X] T038 [P] [US3] Write test in `tests/unit/test_storypoints_calculator.py` verifying `content_tokens_by_type` dict is populated for all element types present

### Implementation for User Story 3

- [X] T039 [US3] Rewrite `normalizer.py`: replace `FibonacciNormalizer` with `RelativeRankingNormalizer` implementing percentile-band algorithm in `specmetrics/plugins/measurement/storypoints/normalizer.py`
- [X] T040 [US3] Implement `normalize(raw_scores: list[tuple[str, float]]) -> dict[str, int]` method that sorts by raw score and maps to Fibonacci bands in `specmetrics/plugins/measurement/storypoints/normalizer.py`
- [X] T041 [US3] Integrate ranking normalization into `calculator.py`: collect all element raw scores, invoke normalizer, populate `normalized_value` and `rank_position` on each `WorkItem` in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T042 [US3] Compute and populate `specification_effort_total` (sum of CSM element raw scores) and `implementation_effort_total` (sum of CFM element raw scores) in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T043 [US3] Compute and populate `total_raw_score` (sum of all raw scores) and `content_tokens_by_type` (dict of element_type to total tokens) in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T044 [US3] Set `content_multiplier` field on result from calibration profile in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T045 [US3] Update `distribution` computation to aggregate normalized Fibonacci values from ranking output in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T046 [US3] Update `aggregate()` function to handle new payload fields (`total_raw_score`, effort totals, `content_tokens_by_type`) in `specmetrics/plugins/measurement/storypoints/models.py`
- [X] T047 [US3] Update `explainer.py` `top_contributors()` to include `source_model` and `element_type` in output for clarity in `specmetrics/plugins/measurement/storypoints/explainer.py`
- [X] T048 [US3] Update contract test in `tests/contract/test_storypoints_measurement.py` to verify new payload fields (`total_raw_score`, `specification_effort_total`, `implementation_effort_total`, `content_tokens_by_type`) are present and valid

**Checkpoint**: Relative ranking normalization works. Output payload fully supports cross-specification comparison.

---

## Phase 6: User Story 4 - Configurable Calibration for Team-Specific Tuning (Priority: P2)

**Goal**: Wire calibrator into the plugin so all weights, coefficients, and ranking strategy are loaded from external YAML profiles instead of hardcoded defaults.

**Independent Test**: Create a calibration profile with `content_multiplier: 0.5`, run measurement, verify content contribution is 5x the default.

### Tests for User Story 4

- [X] T049 [P] [US4] Write test in `tests/unit/test_storypoints_calibrator.py` verifying custom `content_multiplier: 0.5` produces 5x the default content score
- [X] T050 [P] [US4] Write test in `tests/unit/test_storypoints_calibrator.py` verifying custom `csm_base_weights` override (e.g., decision: 8.0) is used instead of default 5.0
- [X] T051 [P] [US4] Write test in `tests/unit/test_storypoints_calibrator.py` verifying calibration file with only `version: "1.0"` loads all defaults
- [X] T052 [P] [US4] Write test in `tests/unit/test_storypoints_calculator.py` verifying custom `factor_coefficients` override per-factor weights in FP scoring

### Implementation for User Story 4

- [X] T053 [US4] Integrate `load_calibration()` into `StoryPointsPlugin.measure()` — load profile at measurement start and pass to calculator in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T054 [US4] Update `calculate()` to accept `StoryPointsCalibrationProfile` parameter instead of individual `coefficients`/`thresholds`/`output_values` dicts in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T055 [US4] Replace hardcoded `DEFAULT_FACTOR_COEFFICIENTS` usage in `score_all_factors()` with values from calibration profile in `specmetrics/plugins/measurement/storypoints/factor_scorer.py`
- [X] T056 [US4] Pass `fibonacci_scale` and `ranking_strategy` from calibration to `RelativeRankingNormalizer` in `specmetrics/plugins/measurement/storypoints/calculator.py`
- [X] T057 [US4] Remove old `_resolve_rule_pack_overrides()` from `plugin.py` (CFM metadata overrides replaced by calibration profile) in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T058 [US4] Update `StoryPointsHandler.handle()` to load calibration via `StoryPointsPlugin.measure()` and pass through pipeline context in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T059 [US4] Ensure existing integration test `tests/integration/test_storypoints_pipeline.py` works with calibration profile fixture

**Checkpoint**: All estimation parameters are externally configurable via YAML calibration profiles.

---

## Phase 7: User Story 5 - Documentation of Story Points Methodology (Priority: P2)

**Goal**: Create RFC-041 documenting the complete Story Points measurement methodology.

**Independent Test**: Open the RFC document and verify it contains methodology, factor definitions, element coverage tables, normalization algorithm, and Kanban guidance.

### Implementation for User Story 5

- [X] T060 [P] [US5] Create `docs/rfcs/RFC-041 - Story Points Measurement Engine.md` with methodology overview: problem statement, measurement goals, and formula explanation
- [X] T061 [P] [US5] Add factor definitions section: all 6 structural factors with their default coefficients and rationale
- [X] T062 [P] [US5] Add element coverage section: CSM and CFM element types with default base weights table and rationale for each weight
- [X] T063 [P] [US5] Add normalization section: relative ranking algorithm, Modified Fibonacci scale, percentile-band distribution
- [X] T064 [P] [US5] Add calibration reference: YAML schema, all configurable parameters, backward compatibility notes
- [X] T065 [P] [US5] Add cross-specification comparison guidance: how to use `total_raw_score` for comparing specs, distinction from normalized values
- [X] T066 [P] [US5] Add Kanban usage appendix: how story points enable manual work item sizing for predictable flow (no automatic chunking)

**Checkpoint**: RFC-041 fully documents the Story Points measurement engine.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and integration checks

- [X] T067 Run full test suite: `pytest tests/unit/test_storypoints_*.py tests/contract/test_storypoints_measurement.py tests/integration/test_storypoints_pipeline.py -v`
- [X] T068 [P] Verify backward compatibility: run old test fixtures with `content_multiplier: 0.0` and confirm all existing tests pass
- [X] T069 Run quickstart.md validation scenarios 1-7 and confirm all pass
- [X] T070 [P] Run ruff linting: `ruff check specmetrics/plugins/measurement/storypoints/ tests/`
- [X] T071 [P] Update `pyproject.toml` entry points if calibration plugin registration changed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational — content formula for FPs
- **User Story 2 (Phase 4)**: Depends on Phase 3 — extends content formula to all elements
- **User Story 3 (Phase 5)**: Depends on Phase 4 — needs all elements for ranking normalization
- **User Story 4 (Phase 6)**: Depends on Phases 3-5 — calibrates the complete engine
- **User Story 5 (Phase 7)**: Depends on Phase 6 — documents the final methodology
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2/P1)**: Depends on User Story 1 (extends content formula)
- **User Story 3 (P1)**: Depends on User Story 2 (needs all element types for ranking)
- **User Story 4 (P2)**: Depends on User Stories 1-3 (calibrates the complete engine)
- **User Story 5 (P2)**: Depends on User Story 4 for final methodology; can draft sections in parallel with earlier phases

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before calculator changes
- Calculator changes before plugin integration
- Core implementation before explainer updates
- Story complete before moving to next phase

### Parallel Opportunities

- Phase 2: T003, T004, T005, T006, T007, T008, T009, T010, T011, T012 can all run in parallel (different files/functions)
- Within US1: T014, T015, T016 (tests) can run in parallel
- Within US2: T022, T023, T024, T025 (tests) can run in parallel; T026 and T027 can run in parallel
- Within US3: T034, T035, T036, T037, T038 (tests) can run in parallel; T039 and T046 can run in parallel
- Within US4: T049, T050, T051, T052 (tests) can run in parallel
- Within US5: All six documentation tasks (T060-T066) can run in parallel
- Phase 8: T068, T070, T071 can run in parallel

---

## Parallel Example: Foundational Phase (Phase 2)

```bash
# Launch all model tasks together:
Task: "Rename FunctionalWorkItem to WorkItem and add new fields in models.py"
Task: "Add new payload fields to StoryPointMeasurementResult in models.py"
Task: "Extend ExecutionMetadata in models.py"
Task: "Add model validators for new constraints in models.py"

# Launch calibration + token counter in parallel:
Task: "Create StoryPointsCalibrationProfile model in calibrator.py"
Task: "Implement get_default_calibration() in calibrator.py"
Task: "Implement load_calibration() in calibrator.py"
Task: "Implement count_tokens_for_element() in token_counter.py"

# Launch all new unit tests in parallel:
Task: "Write unit tests for calibrator"
Task: "Write unit tests for token_counter"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (content-based estimation for FPs)
4. **STOP and VALIDATE**: Test US1 independently — verify content formula, backward compatibility
5. This delivers the core value: content-aware estimation with backward compatibility

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Content formula works → **MVP!**
3. Add US2 → All element types estimated → Expanded scope
4. Add US3 → Ranking + cross-spec payload → **Full P1 delivery**
5. Add US4 → Configurable calibration → **P2 enhancement**
6. Add US5 → RFC-041 documentation → **Complete**

### P1-Only Strategy

If focusing only on P1 stories (US1, US2, US3):
1. Phases 1-2: Setup + Foundational
2. Phases 3-5: US1, US2, US3 sequentially
3. Phase 8: Polish + validation
4. Defer US4 (calibration) and US5 (documentation) to follow-up

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable via its acceptance scenarios
- Tests are written first (TDD) within each story phase to validate acceptance criteria
- Backward compatibility is verified at every checkpoint via `content_multiplier: 0.0` testing
- The existing test suite must continue passing throughout — any breaking changes must be intentional and documented
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently

---

## Phase 9: Convergence

**Purpose**: Close gaps identified between specified intent and current implementation

- [X] T072 Remove `_resolve_rule_pack_overrides()` method from `plugin.py` and its call site; remove unused `thresholds`/`output_values` params from `calculate()` signature per T057 (partial)
- [X] T073 Write test matching US1/AC1 acceptance scenario with exact 500 vs 100 token counts and verify `raw_score` difference equals `(500 - 100) * content_multiplier` per US1/AC1 (partial)
- [X] T074 Update `factor_breakdown_summary()` in `explainer.py` to aggregate `content_score` alongside factor scores per T020 (partial)
- [X] T075 Add cross-framework comparison test (SpecKit vs OpenSpec fixtures) verifying < 15% `total_raw_score` difference, or document as infeasible per SC-007 (missing)
