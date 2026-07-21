# Tasks: Token Points Improvements

**Input**: Design documents from `specs/038-token-points-improvements/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Organization**: Tasks grouped by user story from spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Update data models and tokenizer infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No scoring formula or calibration changes can begin until models are updated

- [X] T001 [P] Add `content_token_count` (int) and `content_score` (float) fields to `TokenContribution` model in `specmetrics/plugins/measurement/token_points/models.py`
- [X] T002 [P] Update `TokenContribution` model validator: `partial_score` MUST equal `applied_weight + content_score` in `specmetrics/plugins/measurement/token_points/models.py`
- [X] T003 [P] Add `content_multiplier: float = 0.1` field to `CalibrationProfile` in `specmetrics/plugins/calibration/models.py`
- [X] T004 [P] Add `references: float = 1.0` field to `SpecificationCostWeights` in `specmetrics/plugins/calibration/models.py`
- [X] T005 [P] Update `SpecificationCostWeights.activities` default from empty dict to `{"exploration": 2.0, "clarification": 3.0, "refinement": 3.0, "review": 1.5, "validation": 2.0}` in `specmetrics/plugins/calibration/models.py`
- [X] T006 [P] Add `content_multiplier` validation (must be >= 0.0) to calibration validator in `specmetrics/plugins/calibration/validator.py`
- [X] T007 Create `count_tokens(text: str) -> int` function with tiktoken (`cl100k_base`) import and fallback to `max(1, len(text) // 4)` at top of `specmetrics/plugins/measurement/token_points/calculator.py`

**Checkpoint**: Models and tokenizer ready — scoring logic can now be updated

---

## Phase 2: User Story 1 - Content-Based Token Estimation (Priority: P1) 🎯 MVP

**Goal**: Each element's score includes content-based estimation: `score = type_weight + (content_tokens × content_multiplier)`. Elements with longer descriptions score proportionally higher.

**Independent Test**: Run Token Points on a project with two functional processes — one with 1000-word description, one with 10-word description. Verify the first scores significantly higher.

### Content Tokenization in Calculator

- [X] T008 [US1] Extract content text per element: `name + " " + description` for CSM elements (SpecificationActivity, Decision, Assumption, Constraint, Risk, OpenQuestion, AcceptanceCriterion, GlossaryTerm) in `specmetrics/plugins/measurement/token_points/calculator.py`
- [X] T009 [US1] Extract content text per element: `name + " " + description` for CFM elements (FunctionalProcess, BusinessRule, Operation, DataGroup, Actor); `name` only for Relationship (no description field) in `specmetrics/plugins/measurement/token_points/calculator.py`
- [X] T010 [US1] Extract content text for CSM References: `title + " " + url` (References have no description) in `specmetrics/plugins/measurement/token_points/calculator.py`

### Updated Scoring Formula

- [X] T011 [US1] Apply new scoring formula in CSM processing loop: for each element, compute `content_tokens = count_tokens(content_text)`, `content_score = content_tokens × content_multiplier`, set `partial_score = type_weight + content_score`, populate `content_token_count` and `content_score` in TokenContribution in `specmetrics/plugins/measurement/token_points/calculator.py`
- [X] T012 [US1] Apply new scoring formula in CFM processing loop: same computation as CSM using code generation weights in `specmetrics/plugins/measurement/token_points/calculator.py`
- [X] T013 [US1] Handle elements with zero-length content: use `content_tokens = 0`, `content_score = 0.0`, log a debug message for empty content in `specmetrics/plugins/measurement/token_points/calculator.py`
- [X] T014 [US1] Log per-element `content_token_count` in the TokenContribution metadata via structlog in `specmetrics/plugins/measurement/token_points/calculator.py`

**Checkpoint**: Content-based scoring active — element descriptions now affect scores

---

## Phase 3: User Story 2 - Cross-Specification Comparability (Priority: P1)

**Goal**: Token Points values are comparable across specifications — a spec with 2x content volume scores approximately 2x higher. Payload includes content token counts for auditing.

**Independent Test**: Generate Token Points for two specifications with known 2:1 content volume. Verify ratio between 1.5:1 and 2.5:1.

### Payload Extensions

- [X] T015 [US2] Extend handler payload with `token_content_multiplier` key (the content_multiplier value used) in `specmetrics/plugins/measurement/token_points/plugin.py`
- [X] T016 [US2] Extend handler payload with `token_content_tokens` key (dict of element_type → total content tokens) in `specmetrics/plugins/measurement/token_points/plugin.py`
- [X] T017 [US2] Extend each entry in `token_element_counts` dict with `content_tokens` field (sum of content_token_count for that element type) in `specmetrics/plugins/measurement/token_points/plugin.py`

### Comparability Verification

- [X] T018 [US2] Create test fixture with two specification files at known 2:1 content volume ratio in `tests/test_token_points_content.py`
- [X] T019 [US2] Create test: verify Token Points ratio between 2:1 content specs falls within 1.5:1 to 2.5:1 in `tests/test_token_points_content.py`

**Checkpoint**: Token Points values correlate with content volume — cross-spec comparison meaningful

---

## Phase 4: User Story 3 - Updated Calibration Profile with Activity Defaults (Priority: P2)

**Goal**: Default calibration produces Specification Cost > 0 without custom YAML. Activities have sensible non-zero weights. Old YAML files remain compatible.

**Independent Test**: Run Token Points with no calibration file on a spec with activities. Verify Specification Cost > 0.

### Default Behavior Tests

- [X] T020 [US3] Create test: run calculator with default calibration on CSM containing activities — verify Specification Cost > 0 in `tests/test_token_points_content.py`
- [X] T021 [US3] Create test: verify each activity type receives correct default weight (exploration=2.0, clarification=3.0, etc.) in `tests/test_token_points_content.py`
- [X] T022 [US3] Create test: verify CSM references contribute score (weight 1.0) instead of being excluded in `tests/test_token_points_content.py`

### Backward Compatibility

- [X] T023 [US3] Create test: load old calibration YAML without `content_multiplier` field — verify defaults to 0.1 in `tests/test_token_points_content.py`
- [X] T024 [US3] Create test: load old calibration YAML without `activities` in SpecificationCost — verify activities get non-zero defaults in `tests/test_token_points_content.py`
- [X] T025 [US3] Create test: load calibration YAML with `content_multiplier: 0.0` — verify content contribution is zero (all same-type elements have identical scores) in `tests/test_token_points_content.py`

**Checkpoint**: Calibration defaults sensible and backward-compatible

---

## Phase 5: User Story 4 - RFC-028 Documentation Update (Priority: P2)

**Goal**: RFC-028 includes a new section documenting the content-based estimation methodology, updated calibration defaults, and Kanban usage recommendations.

**Independent Test**: Open RFC-028, verify new section exists with ≥ 200 words.

- [X] T026 [US4] Add "Content-Based Estimation (v2)" section to RFC-028: describe the scoring formula `type_weight + (content_tokens × content_multiplier)`, token counting method, content sources per element type in `docs/rfcs/RFC-028 - Token Points Measurement Engine.md`
- [X] T027 [US4] Document updated calibration defaults (activity weights, references weight, content_multiplier) and backward-compatibility behavior in the new RFC section in `docs/rfcs/RFC-028 - Token Points Measurement Engine.md`
- [X] T028 [US4] Document usage recommendations: how Token Points enables cross-specification comparability and Kanban work item sizing (grouping specs into size buckets based on Token Points values) as a conceptual practice in `docs/rfcs/RFC-028 - Token Points Measurement Engine.md`

**Checkpoint**: RFC-028 accurately reflects the implemented behavior

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration tests, edge cases, final validation

- [X] T029 [P] Create integration test: end-to-end pipeline with Token Points using default calibration, verify `token_content_tokens` and `token_content_multiplier` appear in payload in `tests/test_token_points_content.py`
- [X] T030 [P] Create edge case test: element with empty name and description receives only type_weight (content contribution = 0) in `tests/test_token_points_content.py`
- [X] T031 [P] Create edge case test: specification with code blocks in descriptions — code is tokenized as text (not excluded) in `tests/test_token_points_content.py`
- [X] T032 [P] Create unit test: `count_tokens()` function with known text, verify correct token count (cross-check with tiktoken) in `tests/test_token_points_content.py`
- [X] T033 [P] Run existing `tests/unit/test_token_points_calculator.py` and `tests/unit/test_token_points_calibration.py` — verify no regressions
- [X] T034 Run quickstart.md validation scenarios 1-8 and confirm all pass
- [X] T035 Run `ruff check` and `ruff format` on all changed files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 (models + tokenizer) — BLOCKS MVP
- **US2 (Phase 3)**: Depends on Phase 2 (scoring must be active before payload extension)
- **US3 (Phase 4)**: Depends on Phase 1 (calibration models). Tests can run in parallel with Phase 2/3
- **US4 (Phase 5)**: Independent — can start anytime after plan is ready. Documents the implemented behavior
- **Polish (Phase 6)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only
- **US2 (P1)**: Depends on US1 (needs scoring formula running)
- **US3 (P2)**: Depends on Foundational models only — independent from US1/US2 implementation
- **US4 (P2)**: Independent — can be written in parallel with any phase

### Within Each Phase

- Phase 1: T001-T006 (6 model tasks) can run in parallel; T007 depends on nothing (tokenizer is standalone)
- Phase 2: T008-T010 (content extraction) can run in parallel; T011-T014 depend on T008-T010
- Phase 3: T015-T017 (payload) depend on Phase 2; T018-T019 (comparability tests) parallel within phase
- Phase 4: T020-T025 (6 test tasks) can all run in parallel
- Phase 5: T026-T028 can run in any order (same file, but sequential by section)
- Phase 6: T029-T033 can run in parallel; T034-T035 run sequentially

### Parallel Opportunities

- Phase 1: T001-T006 (6 model/calibration tasks in parallel)
- Phase 2: T008 + T009 + T010 (3 content extraction tasks in parallel)
- Phase 4: T020-T025 (6 tests in parallel)
- **US3 (Phase 4) and US4 (Phase 5) can run in parallel** with US1/US2
- **US4 (Phase 5) can be done anytime** — even before Phase 1

---

## Parallel Example: Foundational Models (Phase 1)

```bash
# All 6 model tasks touch different concerns — launch together:
Task: "Add content_token_count/content_score to TokenContribution in token_points/models.py"
Task: "Update TokenContribution validator in token_points/models.py"
Task: "Add content_multiplier to CalibrationProfile in calibration/models.py"
Task: "Add references to SpecificationCostWeights in calibration/models.py"
Task: "Update activities default in calibration/models.py"
Task: "Add content_multiplier validation in calibration/validator.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Foundational (models + tokenizer)
2. Complete Phase 2: US1 (content-based scoring)
3. **STOP and VALIDATE**: Run `specmetrics measure --metrics tp` on a project with varied descriptions, verify scores correlate with content volume

### Incremental Delivery

1. Foundational → Models ready, tokenizer working
2. Add US1 → Content-based scoring active (MVP!)
3. Add US2 → Cross-spec comparability verified, payload extended
4. Add US3 → Calibration defaults sensible, backward-compatible
5. Add US4 → RFC documentation updated
6. Polish → Tests and validation complete

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 together (models)
2. Once Foundational is done:
   - Developer A: US1 + US2 (calculator + payload, Phases 2-3)
   - Developer B: US3 (calibration tests, Phase 4)
   - Developer C: US4 (RFC update, Phase 5) — can start immediately
3. All converge on Polish (Phase 6)

---

## Notes

- [P] tasks = different files or independent test cases, no dependencies
- [Story] label maps task to specific user story for traceability
- The `count_tokens()` function at T007 should be a module-level function in calculator.py, not a method — it's called per-element in tight loops
- T018-T019 (comparability tests) use synthetic CSM/CFM fixtures with known content volumes — they do NOT require actual specification files
- Existing tests in `tests/unit/test_token_points_calculator.py` MUST pass without modification (T033) — any regression indicates a bug
- The RFC-028 update (Phase 5) is a documentation-only task and can be done by anyone familiar with the content-based estimation design from data-model.md
- When `content_multiplier = 0.0`, the new formula produces identical results to the old formula — this is the backward-compatibility escape hatch
