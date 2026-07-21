# Tasks: Improve Deterministic Extraction Engine

**Input**: Design documents from `/specs/034-improve-deterministic-extraction/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Tests**: Tests are included as specified in spec acceptance scenarios and quickstart validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Verify the existing codebase is ready for changes

- [X] T001 Verify existing test suite passes baseline: run `pytest specmetrics/tests/ -x --ignore=specmetrics/tests/integration/test_deterministic_pipeline.py::TestDeterministicPipeline::test_framework_detection_openspec -q`
- [X] T002 [P] Read and understand `specmetrics/kernel/rules/default_rule_pack.yaml` — note existing rule patterns, priorities, and types
- [X] T003 [P] Read and understand `specmetrics/kernel/rules/speckit_rules.yaml` — identify the 4 GWT rules to modify (lines 55-92)
- [X] T004 [P] Read and understand `specmetrics/kernel/cfm/builder.py` — locate `_infer_operation_direction()` (line 38) and element construction (lines 74-94) for marker insertion point
- [X] T005 [P] Read and understand `specmetrics/kernel/cfm/classifier.py` — locate `_classify_entity()` (line 37) and ACTOR_PATTERNS (line 14)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new infrastructure needed. Changes are isolated to existing YAML and Python files.

**⚠️ CRITICAL**: Phase 1 verification (test baseline passes) must complete before any modifications.

- No foundational tasks required — this feature extends existing components with no new dependencies or project structure.

**Checkpoint**: Baseline test suite passes. Ready to begin user story implementation.

---

## Phase 3: User Story 1 - Operation Extraction for GWT Scenarios (Priority: P1) 🎯 MVP

**Goal**: The deterministic engine identifies operations from Given/When/Then patterns, enabling functional process construction and non-zero Story Points, BCP, and transactional FPA metrics.

**Independent Test**: Run `specmetrics measure` — verify CFM contains at least 1 functional process and Story Points > 0.

### Implementation for User Story 1

- [X] T006 [P] [US1] Add `gwt-given-operation` rule with `type: "operation"`, keyword pattern for `**GIVEN**`/`**Given**`, priority 72 in `specmetrics/kernel/rules/default_rule_pack.yaml`
- [X] T007 [P] [US1] Add `gwt-when-operation` rule with `type: "operation"`, keyword pattern for `**WHEN**`/`**When**`, priority 72 in `specmetrics/kernel/rules/default_rule_pack.yaml`
- [X] T008 [P] [US1] Add `gwt-then-operation` rule with `type: "operation"`, keyword pattern for `**THEN**`/`**Then**`, priority 72 in `specmetrics/kernel/rules/default_rule_pack.yaml`
- [X] T009 [P] [US1] Change `speckit-gwt-numbered` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/speckit_rules.yaml` (line 59)
- [X] T010 [P] [US1] Change `speckit-gwt-multiline-given` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/speckit_rules.yaml` (line 69)
- [X] T011 [P] [US1] Change `speckit-gwt-multiline-when` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/speckit_rules.yaml` (line 79)
- [X] T012 [P] [US1] Change `speckit-gwt-multiline-then` type from `"fact"` to `"operation"` in `specmetrics/kernel/rules/speckit_rules.yaml` (line 89)
- [X] T013 [US1] Verify operation extraction: run quickstart edge case test — create test document with GWT patterns, confirm `extract()` returns elements with `type="operation"`
- [X] T014 [US1] Run full `specmetrics measure` and verify SC-001 (≥1 functional process), SC-002 (Story Points > 0), SC-004 (EI+EO+EQ count > 0)

**Checkpoint**: Operations extracted, functional processes built, Story Points and transactional FPA non-zero.

---

## Phase 4: User Story 2 - SNAP Semantic Marker Inference (Priority: P2)

**Goal**: CFM elements receive `semantic_marker` metadata so SNAP measurement classifies them into non-functional categories instead of producing zero items with 1005 warnings.

**Independent Test**: Run `specmetrics measure` — verify SNAP total > 0 and no `MISSING_SEMANTIC_MARKER` warnings for classifiable elements.

### Implementation for User Story 2

- [X] T015 [US2] Add `_infer_semantic_marker(element, section_id: str) -> str` function in `specmetrics/kernel/cfm/builder.py` with the marker-to-section mapping from research.md decision 2
- [X] T016 [US2] Integrate `_infer_semantic_marker()` call into CFM builder element construction in `specmetrics/kernel/cfm/builder.py` — set `metadata["semantic_marker"]` on each Actor, BusinessRule, DataGroup, and Operation during `build()`
- [X] T017 [US2] Verify semantic markers: run quickstart validation scenario 2 — check that SNAP `snap_total_items` > 0 and no MISSING_SEMANTIC_MARKER warnings remain for elements from mapped sections
- [X] T018 [US2] Run full `specmetrics measure` and verify SC-003 (SNAP non-zero classified items)

**Checkpoint**: SNAP measurement produces classified items. US1 + US2 both functional.

---

## Phase 5: User Story 3 - Actor Identification from Specification Entities (Priority: P3)

**Goal**: Entities with role-like names or appearing in actor-context sections are classified as actors instead of data groups, enriching functional processes with actor associations.

**Independent Test**: Run `specmetrics measure` — verify CFM contains at least 1 Actor entity.

### Implementation for User Story 3

- [X] T019 [P] [US3] Expand ACTOR_PATTERNS set in `specmetrics/kernel/cfm/classifier.py` — add keywords: stakeholder, moderator, subscriber, visitor, guest, consumer, provider, vendor, partner
- [X] T020 [P] [US3] Add section-context actor detection in `_classify_entity()` in `specmetrics/kernel/cfm/classifier.py` — if entity's section_id contains "Actor", "Role", "User", or "Persona", classify as actor before data_group checks
- [X] T021 [P] [US3] Add key-phrase actor detection in `_classify_entity()` in `specmetrics/kernel/cfm/classifier.py` — if entity text contains "acts as", "is a user", "represents a person", or "external system", classify as actor
- [X] T022 [US3] Verify actor classification: run quickstart validation scenario 3 — check that CFM contains at least 1 actor element (previously 0)
- [X] T023 [US3] Run full `specmetrics measure` and verify SC-005 (≥1 Actor entity), SC-006 (no broken evidence references)

**Checkpoint**: Actors identified, functional processes linked to actors. All 3 user stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and regression checks.

- [X] T024 [P] Run quickstart.md full pipeline spot-check (scenario 4) — verify all metric values against expected ranges
- [X] T025 [P] Run quickstart.md evidence traceability check (scenario 5) — verify zero broken evidence references
- [X] T026 Run full existing test suite: `pytest specmetrics/tests/ -x --ignore=specmetrics/tests/integration/test_deterministic_pipeline.py::TestDeterministicPipeline::test_framework_detection_openspec -q` — confirm no regressions
- [X] T027 Verify no performance degradation: run `specmetrics measure` and confirm extraction stage ≤ 12s (baseline ~8s, 50% margin for new rules)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (verify baseline tests pass)
- **User Story 1 (Phase 3)**: Depends on Setup — no foundational blockers
- **User Story 2 (Phase 4)**: Depends on Setup — independent of US1, can run in parallel
- **User Story 3 (Phase 5)**: Depends on Setup — independent of US1/US2, can run in parallel
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories. YAML-only changes.
- **User Story 2 (P2)**: No dependencies on other stories. Python builder changes only.
- **User Story 3 (P3)**: No dependencies on other stories. Python classifier changes only.

### Within Each User Story

- US1: All YAML rule changes are [P] (different files/lines) → can run in parallel. T013 verification depends on all rule changes.
- US2: T015 (function definition) → T016 (integration) → T017 (verification)
- US3: T019, T020, T021 are [P] (different code sections) → T022 verification depends on all classifier changes

### Parallel Opportunities

- All 4 Setup tasks (T002-T005) can run in parallel
- All 7 US1 rule tasks (T006-T012) can run in parallel
- US1 (Phase 3), US2 (Phase 4), US3 (Phase 5) can run in parallel by different developers
- US3 classifier tasks T019, T020, T021 can run in parallel
- All Polish tasks T024-T025 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all YAML rule additions together:
Task: "Add gwt-given-operation rule in specmetrics/kernel/rules/default_rule_pack.yaml"
Task: "Add gwt-when-operation rule in specmetrics/kernel/rules/default_rule_pack.yaml"
Task: "Add gwt-then-operation rule in specmetrics/kernel/rules/default_rule_pack.yaml"
Task: "Change speckit-gwt-numbered type to operation in specmetrics/kernel/rules/speckit_rules.yaml"
Task: "Change speckit-gwt-multiline-given type to operation in specmetrics/kernel/rules/speckit_rules.yaml"
Task: "Change speckit-gwt-multiline-when type to operation in specmetrics/kernel/rules/speckit_rules.yaml"
Task: "Change speckit-gwt-multiline-then type to operation in specmetrics/kernel/rules/speckit_rules.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 3: User Story 1 (T006-T014)
3. **STOP and VALIDATE**: Run `specmetrics measure` — confirm Story Points > 0, functional processes ≥ 1
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → Baseline verified
2. Add US1 → Operations extracted → Test independently → MVP!
3. Add US2 → SNAP markers → Test independently → SNAP non-zero
4. Add US3 → Actors identified → Test independently → Richer measurements
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup verified:
   - Developer A: User Story 1 (YAML rules)
   - Developer B: User Story 2 (builder changes)
   - Developer C: User Story 3 (classifier changes)
3. Stories complete and integrate independently — no merge conflicts (different files)

---

## Phase 7: Convergence

**Purpose**: Close remaining gaps identified by convergence assessment — marker-to-section mapping overrideability and automated test coverage for new features.

- [X] T028 Make section-to-semantic-marker mappings overridable via rule packs or configuration in `specmetrics/kernel/cfm/builder.py` per FR-007 (partial)
- [X] T029 Add pytest tests for operation extraction (`test_deterministic_pipeline.py`), semantic marker inference, and actor classification (`test_cfm_classifier.py`) per plan.md project structure and spec.md acceptance criteria (missing)

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
