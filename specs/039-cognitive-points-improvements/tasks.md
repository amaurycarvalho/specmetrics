# Tasks: Cognitive Points Improvements

**Input**: Design documents from `specs/039-cognitive-points-improvements/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md. **Dependency**: spec 038 (Token Points) must be implemented first for the shared `count_tokens()` utility in `kernel/token_utils.py`.

**Organization**: Tasks grouped by user story from spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Update models and Bloom classifier infrastructure. All user stories depend on this phase.

**⚠️ CRITICAL**: No content scoring or sub-type classification can begin until models and classifier are updated.

- [X] T001 [P] Add `content_token_count` (int) and `content_score` (float) fields to `CognitiveContribution` model in `specmetrics/plugins/measurement/cognitive_points/models.py`
- [X] T002 [P] Update `CognitiveContribution` model validator: `partial_score` MUST equal `cognitive_weight + content_score` within 0.001 tolerance in `specmetrics/plugins/measurement/cognitive_points/models.py`
- [X] T003 [P] Add `content_multiplier: float = 0.1` field to `CognitiveCalibrationProfile` in `specmetrics/plugins/measurement/cognitive_points/calibration.py`
- [X] T004 [P] Update `BloomClassifier.classify()` signature to accept optional `element: Any = None` parameter and implement sub-type attribute lookup via `SUB_TYPE_ATTRS` dict in `specmetrics/plugins/measurement/cognitive_points/bloom_classifier.py`
- [X] T005 [P] Update `DefaultBloomClassifier` with sub-type Bloom mappings (4 BusinessRule sub-types, 4 Operation sub-types) and change `default_bloom_level` from "analyze" to "understand" in `specmetrics/plugins/measurement/cognitive_points/bloom_classifier.py`
- [X] T006 [P] Update `CognitiveCalibrationProfile.bloom_mappings` defaults to include sub-type entries in `specmetrics/plugins/measurement/cognitive_points/calibration.py`
- [X] T007 [P] Update `CognitiveCalibrationProfile.default_bloom_level` default from "analyze" to "understand" in `specmetrics/plugins/measurement/cognitive_points/calibration.py`
- [X] T008 Verify `count_tokens()` from `specmetrics/kernel/token_utils.py` exists (prerequisite from spec 038). If not yet implemented, add a note to implement spec 038 Phase 1 first.

**Checkpoint**: Models and classifier ready — content scoring and sub-type classification can now begin

---

## Phase 2: User Story 1 - Content-Based Cognitive Scoring (Priority: P1) 🎯 MVP

**Goal**: Each element's cognitive score includes content-based estimation: `score = bloom_weight + (content_tokens × content_multiplier)`. Elements with longer descriptions score proportionally higher.

**Independent Test**: Run Cognitive Points on two specs with identical element counts but one with 3x content volume — verify the richer spec scores at least 1.5x higher.

### Content Text Extraction

- [X] T009 [US1] Extract content text per CSM element: `name + " " + description` for SpecificationActivity, Decision, Assumption, Constraint, Risk, OpenQuestion, AcceptanceCriterion, GlossaryTerm in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T010 [US1] Extract content text per CFM element: `name + " " + description` for FunctionalProcess, BusinessRule, Operation, DataGroup, Actor; `name` only for Relationship in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T011 [US1] Extract content text for CSM References: `title + " " + url` (References are in CSM but not yet processed by cognitive engine — add them) in `specmetrics/plugins/measurement/cognitive_points/calculator.py`

### Updated Scoring Formula

- [X] T012 [US1] In `_process_csm()`: for each element, compute `content_tokens = count_tokens(content_text)`, `content_score = content_tokens × content_multiplier`, set `partial_score = bloom_weight + content_score`, populate `content_token_count` and `content_score` in CognitiveContribution in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T013 [US1] In `_process_cfm()`: same content-based scoring as CSM in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T014 [US1] Handle zero-length content: `content_tokens = 0`, `content_score = 0.0`, log debug in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T015 [US1] Import `count_tokens` from `specmetrics.kernel.token_utils` in `specmetrics/plugins/measurement/cognitive_points/calculator.py`

**Checkpoint**: Content-based cognitive scoring active — element descriptions affect scores

---

## Phase 3: User Story 2 - Cross-Specification Cognitive Comparability (Priority: P1)

**Goal**: Cognitive Points values correlate with content volume across specifications. Payload includes content token counts for auditing.

**Independent Test**: Two specifications with similar content volumes from different frameworks produce raw scores within 15% of each other.

### Payload Extensions

- [X] T016 [US2] Extend handler payload with `cognitive_content_multiplier` key in `specmetrics/plugins/measurement/cognitive_points/plugin.py`
- [X] T017 [US2] Extend handler payload with `cognitive_content_tokens` key (dict of element_type → total content tokens) in `specmetrics/plugins/measurement/cognitive_points/plugin.py`
- [X] T018 [US2] Extend each entry in `cognitive_element_counts` dict with `content_tokens` field (sum of content_token_count for that element type) in `specmetrics/plugins/measurement/cognitive_points/plugin.py`

### Comparability Tests

- [X] T019 [US2] Create test: two specifications with identical element counts but 3x content volume — verify raw score ratio meets SC-001 (≥ 1.5x) in `tests/test_cognitive_points_content.py`
- [X] T020 [US2] Create test: payloat includes `cognitive_content_tokens` and `cognitive_content_multiplier` keys in `tests/test_cognitive_points_content.py`

**Checkpoint**: Cross-spec comparability verified — scores correlate with content volume

---

## Phase 4: User Story 3 - Granular Bloom Classification with Sub-Types (Priority: P2)

**Goal**: Elements with sub-type metadata are classified into appropriate Bloom levels. BusinessRule `derivation` → evaluate, `constraint` → apply, etc.

**Independent Test**: Classify BusinessRules with different `rule_type` values — verify they map to different Bloom levels.

### Sub-Type Classification in Calculator

- [X] T021 [US3] Pass the element object (not just type string) to `classifier.classify()` in `_process_csm()` in `specmetrics/plugins/measurement/cognitive_points/calculator.py`
- [X] T022 [US3] Pass the element object to `classifier.classify()` in `_process_cfm()` in `specmetrics/plugins/measurement/cognitive_points/calculator.py`

### Sub-Type Classification Tests

- [X] T023 [US3] Create test: BusinessRule with `rule_type="derivation"` → Bloom level ≥ "analyze" (SC-003) in `tests/test_cognitive_points_content.py`
- [X] T024 [US3] Create test: BusinessRule with `rule_type="constraint"` → Bloom level "apply" in `tests/test_cognitive_points_content.py`
- [X] T025 [US3] Create test: unknown element type defaults to "understand" (SC-004) in `tests/test_cognitive_points_content.py`
- [X] T026 [US3] Create test: element with sub-type not in mappings falls back to base type mapping in `tests/test_cognitive_points_content.py`

**Checkpoint**: Sub-type classification active — same-type elements with different sub-types get different Bloom levels

---

## Phase 5: User Story 4 - RFC-029 Documentation Update (Priority: P2)

**Goal**: RFC-029 includes a new section documenting content-based estimation, sub-type classification, and Kanban usage recommendations.

**Independent Test**: Open RFC-029, verify new section exists with ≥ 200 words.

- [X] T027 [US4] Add "Content-Based Estimation (v2)" section to RFC-029: describe scoring formula `bloom_weight + (content_tokens × content_multiplier)`, token counting method, content sources per element type in `docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md`
- [X] T028 [US4] Document updated Bloom mappings with sub-type entries (BusinessRules and Operations) and default level change ("analyze" → "understand") in `docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md`
- [X] T029 [US4] Document usage recommendations: how Cognitive Points enables cross-specification cognitive comparability and Kanban work item sizing as a conceptual practice in `docs/rfcs/RFC-029 - Cognitive Points Measurement Engine.md`

**Checkpoint**: RFC-029 accurately reflects implemented behavior

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integration tests, edge cases, regression tests, final validation

- [X] T030 [P] Create integration test: end-to-end pipeline with content_multiplier=0.1, verify scores vary by content volume in `tests/test_cognitive_points_content.py`
- [X] T031 [P] Create integration test: content_multiplier=0.0 disables content estimation (all same-type elements have identical scores) in `tests/test_cognitive_points_content.py`
- [X] T032 [P] Create edge case test: element with empty name and description receives only bloom_weight (content contribution = 0) in `tests/test_cognitive_points_content.py`
- [X] T033 [P] Run existing tests: `tests/unit/test_cognitive_points_models.py`, `tests/unit/test_cognitive_points_bloom.py`, `tests/unit/test_cognitive_points_calculator.py`, `tests/unit/test_cognitive_points_calibration.py` — verify no regressions
- [X] T034 Run quickstart.md validation scenarios 1-8 and confirm all pass
- [X] T035 Run `ruff check` and `ruff format` on all changed files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies (beyond spec 038 token_utils) — can start immediately
- **US1 (Phase 2)**: Depends on Phase 1 (models + classifier) — BLOCKS MVP
- **US2 (Phase 3)**: Depends on Phase 2 (content scoring must be active before payload extension)
- **US3 (Phase 4)**: Depends on Phase 1 (classifier changes). Can run in parallel with Phase 2/3
- **US4 (Phase 5)**: Independent — can start anytime. Documents the implemented behavior
- **Polish (Phase 6)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only
- **US2 (P1)**: Depends on US1 (needs scoring formula running)
- **US3 (P2)**: Depends on Foundational only — independent from US1/US2
- **US4 (P2)**: Independent — can be written in parallel with any phase

### Within Each Phase

- Phase 1: T001-T007 (7 model/config tasks) can all run in parallel (different concerns, same files may need coordination)
- Phase 2: T009-T011 (content extraction) can run in parallel; T012-T015 depend on them
- Phase 3: T016-T018 (payload extension) depend on Phase 2; T019-T020 (tests) parallel within phase
- Phase 4: T021-T022 (calculator) depend on Phase 1; T023-T026 (tests) parallel within phase
- Phase 5: T027-T029 can run in any order (same file, sequential by section)
- Phase 6: T030-T033 can run in parallel; T034-T035 sequential

### Parallel Opportunities

- Phase 1: T001-T007 (7 tasks in parallel — different files/concerns)
- Phase 2: T009 + T010 + T011 (3 content extraction tasks in parallel)
- Phase 4: T023-T026 (4 test tasks in parallel)
- **US1 (Phase 2) and US3 (Phase 4) can run in parallel** by different developers
- **US4 (Phase 5) can be done anytime** — even before Phase 1

---

## Parallel Example: Foundational Phase (Phase 1)

```bash
# All 7 model/config tasks touch different concerns:
Task: "Add content fields to CognitiveContribution in cognitive_points/models.py"
Task: "Update CognitiveContribution validator in cognitive_points/models.py"
Task: "Add content_multiplier to CognitiveCalibrationProfile in cognitive_points/calibration.py"
Task: "Update BloomClassifier.classify() signature in cognitive_points/bloom_classifier.py"
Task: "Update DefaultBloomClassifier mappings and default in cognitive_points/bloom_classifier.py"
Task: "Update calibration defaults for bloom_mappings in cognitive_points/calibration.py"
Task: "Update calibration default_bloom_level in cognitive_points/calibration.py"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Foundational (models + classifier)
2. Complete Phase 2: US1 (content-based scoring)
3. **STOP and VALIDATE**: Run `specmetrics measure --metrics cp` on a project with varied descriptions, verify scores correlate with content volume

### Incremental Delivery

1. Foundational → Models ready, classifier updated
2. Add US1 → Content-based scoring active (MVP!)
3. Add US2 → Cross-spec comparability verified, payload extended
4. Add US3 → Sub-type classification active
5. Add US4 → RFC documentation updated
6. Polish → Tests and validation complete

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 together
2. Once Foundational is done:
   - Developer A: US1 + US2 (content scoring + payload, Phases 2-3)
   - Developer B: US3 (sub-type classification, Phase 4)
   - Developer C: US4 (RFC update, Phase 5) — can start immediately
3. All converge on Polish (Phase 6)

---

## Notes

---

## Phase 7: Convergence

**Purpose**: Close remaining gaps between the spec/plan/tasks and the current codebase. All tasks identified during convergence assessment.

- [X] T036 Extract `count_tokens()` from `token_points/calculator.py` into `specmetrics/kernel/token_utils.py` as a shared utility per plan: shared tokenizer (missing)
- [X] T037 Add `content_token_count` (int) and `content_score` (float) fields to `CognitiveContribution` model, with `partial_score = cognitive_weight + content_score` validator (0.001 tolerance) per FR-004 (missing)
- [X] T038 Import `count_tokens` from `kernel/token_utils`, add content text extraction helpers, and apply `score = bloom_weight + (content_tokens × content_multiplier)` formula in CSM and CFM processing loops per FR-001, FR-002, FR-003 (missing)
- [X] T039 Add CSM References (`csm.references`) processing to `_process_csm()` in `calculator.py` with content text `title + " " + url` per T011 (missing)
- [X] T040 Update `BloomClassifier` protocol signature to `classify(self, element_type: str, element: Any = None) -> str`, add `SUB_TYPE_ATTRS` dict with sub-type attribute mapping, and implement three-tier lookup (sub-type → base type → default) per FR-005 (missing)
- [X] T041 Add sub-type Bloom mappings (4 BusinessRule, 4 Operation sub-types) to `DefaultBloomClassifier` and change `default_bloom_level` from "analyze" to "understand" per FR-006, FR-007 (missing)
- [X] T042 Add `content_multiplier: float = 0.1` to `CognitiveCalibrationProfile`, change `default_bloom_level` default to `"understand"`, update `bloom_mappings` defaults with sub-type entries, and update `_merge_calibration_data` to handle `content_multiplier` per FR-009 (missing)
- [X] T043 Extend handler payload with `cognitive_content_multiplier`, `cognitive_content_tokens` (dict of element_type → total content tokens), and `content_tokens` field in each `cognitive_element_counts` entry per FR-008 (missing)
- [X] T044 Pass element object to `classifier.classify()` in both `_process_csm()` and `_process_cfm()` loops per T021, T022 (missing)
- [X] T045 Create `tests/test_cognitive_points_content.py` with content-based scoring tests, comparability tests (SC-001), sub-type classification tests (SC-003, SC-004), payload extension tests (SC-005), edge case tests, and backward-compatibility tests per plan: test file (missing)
- [X] T046 Add "Content-Based Estimation (v2)" section to RFC-029 with formula, token counting method, content sources, sub-type classification, and Kanban usage recommendations per FR-010 (missing)
- [X] T047 Update existing test expectations in `test_cognitive_points_calibration.py` (default_bloom_level) and `test_cognitive_points_bloom.py` (unknown type default) to match new "understand" default — run T033 after these changes per T033 (partial)
- [X] T048 Handle zero-length content in calculator: content_tokens = 0, content_score = 0.0, log debug message per T014 (missing)
- [X] T049 Log per-element content_token_count via structlog in calculator per T014 (missing)

- [P] tasks = different files or independent test cases, no dependencies
- [Story] label maps task to specific user story for traceability
- **Prerequisite**: spec 038 (Token Points) must have `kernel/token_utils.py` with `count_tokens()` implemented before T015. If not available, create the shared utility placeholader in this feature.
- T001-T003 (model changes) and T004-T005 (classifier changes) are in different files — true parallel
- T006-T007 modify the same file (`calibration.py`) but different fields — can still be done in parallel or combined
- Existing tests (T033) MUST pass without modification — any regression indicates a bug
- The `content_multiplier` = 0.0 escape hatch (T031) ensures backward compatibility for users who want pure Bloom taxonomy scoring
- Sub-type classification (Phase 4) is additive to content-based scoring (Phase 2) — they can be implemented independently and combined
