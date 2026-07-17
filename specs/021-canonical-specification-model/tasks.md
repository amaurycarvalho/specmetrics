# Tasks: Canonical Specification Model Builder

**Input**: Design documents from `specs/021-canonical-specification-model/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/tests/` at repository root
- Paths follow the project structure from `plan.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend existing pipeline infrastructure to support the new CSM stage

- [X] T001 Create `specmetrics/kernel/csm/` package directory with `__init__.py`
- [X] T002 [P] Add `CANONICAL_SPECIFICATION_MODEL_BUILT` to `EventType` enum in `specmetrics/kernel/events.py`
- [X] T003 [P] Add `canonical_spec_model` field to `PipelineContext` in `specmetrics/kernel/pipeline_context.py`
- [X] T004 Update `CANONICAL_EVENT_ORDER` in `specmetrics/kernel/pipeline_engine.py` — insert `CANONICAL_SPECIFICATION_MODEL_BUILT` after `EVIDENCE_GRAPH_BUILT`

**Parallel opportunities**: T002 and T003 are independent files and can run in parallel.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, classifier, and builder function — MUST complete before any user story

- [X] T005 [P] Create `EvidenceRef` model in `specmetrics/kernel/csm/model.py` (shared reference type)
- [X] T006 [P] Create `CsmElement` base model with id (UUID v4), description, evidence_references, status fields in `specmetrics/kernel/csm/model.py`
- [X] T007 [P] Create `BuildMetadata` and `ClassificationConflict` models in `specmetrics/kernel/csm/metadata.py`
- [X] T008 Create all CSM entity models (Decision, Assumption, Constraint, Risk, OpenQuestion, AcceptanceCriterion, GlossaryTerm, Reference, SpecificationActivity) inheriting from CsmElement in `specmetrics/kernel/csm/model.py`
- [X] T009 Create `CanonicalSpecificationModel` root model (frozen) with all category dictionaries + query interface methods (`get_element`, `get_elements`, `get_elements_by_evidence`, `trace_evidence`) in `specmetrics/kernel/csm/model.py`
- [X] T010 Create deterministic classifier with regex patterns for all 8 canonical categories in `specmetrics/kernel/csm/classifier.py`
- [X] T011 Create SpecificationActivity type detector (exploration, clarification, refinement, review, validation) in `specmetrics/kernel/csm/activity_classifier.py`
- [X] T012 Create evidence graph traversal helpers for linking entities to evidence nodes in `specmetrics/kernel/csm/evidence_processing.py`
- [X] T013 Implement `build()` function that transforms EvidenceGraph → CanonicalSpecificationModel in `specmetrics/kernel/csm/builder.py`
- [X] T014 [P] Wire up `specmetrics/kernel/csm/__init__.py` to export all public symbols

**Parallel opportunities**: T005–T007 are independent. T010–T012 are independent of each other. T014 depends on all preceding tasks.

**Checkpoint**: Foundation ready — all models, classifier, and build() function exist and can be tested in isolation.

---

## Phase 3: User Story 1 — Transform evidence graph into CSM (Priority: P1) 🎯 MVP

**Goal**: Pipeline operator runs the measurement pipeline; after Evidence Graph stage completes, CSM Builder automatically transforms the evidence graph into a framework-independent Canonical Specification Model.

**Independent Test**: Provide an evidence graph extracted from both OpenSpec and SpecKit repositories containing specification artifacts (Explore, Clarify, Decisions, Questions, Assumptions). Verify that the resulting CSM contains only canonical elements with no framework-specific terminology.

### Tests for User Story 1

- [X] T015 [P] [US1] Unit test for CsmElement base and entity model construction in `tests/unit/test_csm_model.py`
- [X] T016 [P] [US1] Unit test for classifier — validate each canonical category is correctly identified from text patterns in `tests/unit/test_csm_classifier.py`
- [X] T017 [P] [US1] Unit test for SpecificationActivity type detection in `tests/unit/test_csm_classifier.py`
- [X] T018 [P] [US1] Unit test for BuildMetadata correctness in `tests/unit/test_csm_metadata.py`
- [X] T019 [US1] Unit test for `build()` function — sample evidence graph → CSM with correct categories in `tests/unit/test_csm_builder.py`
- [X] T020 [US1] Unit test for framework normalization — OpenSpec and SpecKit graphs produce structurally identical CSMs in `tests/unit/test_csm_builder.py`
- [X] T021 [US1] Unit test for empty evidence graph — produces empty CSM without errors in `tests/unit/test_csm_builder.py`
- [X] T022 [US1] Unit test for unclassifiable elements — preserved in References category in `tests/unit/test_csm_builder.py`
- [X] T023 [US1] Unit test for element immutability — frozen model enforced in `tests/unit/test_csm_model.py`
- [X] T024 [US1] Integration test for pipeline stage — Evidence Graph → CSM Builder emits CanonicalSpecificationModelBuilt event in `tests/integration/test_csm_pipeline_stage.py`

### Implementation for User Story 1

- [X] T025 [P] [US1] Implement `CsmBuilderStage` handler class in `specmetrics/kernel/csm/builder.py`
- [X] T026 [US1] Create stage plugin metadata registration in `specmetrics/plugins/stage/csm_builder.py`

**Checkpoint**: US1 is fully functional — the pipeline can transform evidence graphs into CSMs with all canonical categories, provenance preservation, and framework normalization.

---

## Phase 4: User Story 2 — Inspect specification maturity and quality (Priority: P1)

**Goal**: Specification author/reviewer inspects the CSM to understand specification evolution, unresolved assumptions, decisions taken, and cognitive complexity origins.

**Independent Test**: Generate a known specification containing assumptions, risks, decisions, glossary terms and acceptance criteria. Verify that each element appears in the appropriate CSM category with complete traceability.

### Tests for User Story 2

- [X] T027 [P] [US2] Unit test for query interface — `get_element()`, `get_elements()` by category, `get_elements_by_evidence()` in `tests/unit/test_csm_model.py`
- [X] T028 [P] [US2] Unit test for evidence traceability — `trace_evidence()` returns full provenance chain in `tests/unit/test_csm_model.py`
- [X] T029 [US2] Unit test for cross-entity linking — SpecificationActivity linked to decisions/questions/assumptions in `tests/unit/test_csm_builder.py`
- [X] T030 [P] [US2] Contract test for CSM query interface — downstream consumer enumerates categories and queries elements in `tests/contract/test_csm_interface.py`

### Implementation for User Story 2

- [X] T031 [US2] Implement query interface methods on `CanonicalSpecificationModel` in `specmetrics/kernel/csm/model.py` (if not already done in T009)

**Note**: Query interface methods are expected to be created in T009 (Phase 2). T031 is a safety task to ensure completeness.

**Checkpoint**: US2 is fully functional — the CSM query interface enables inspection of all categories, evidence traceability, and element enumeration without framework-specific knowledge.

---

## Phase 5: User Story 3 — Feed downstream measurement engines (Priority: P2)

**Goal**: Measurement engine developer implements Token Points or Cognitive Points using only the CSM interface without knowledge of OpenSpec, SpecKit or future specification frameworks.

**Independent Test**: Implement a mock measurement engine consuming only the CSM interface and verify identical behavior for repositories created using different specification frameworks.

### Tests for User Story 3

- [X] T032 [P] [US3] Unit test for `CsmConsumer` protocol conformance — mock consumer implements the protocol in `tests/unit/test_csm_model.py`
- [X] T033 [US3] Contract test — mock measurement engine consumes CSM from both OpenSpec and SpecKit sources, verifies identical structure in `tests/contract/test_csm_interface.py`
- [X] T034 [US3] Integration test — mock engine reads CSM from PipelineContext after full pipeline run in `tests/integration/test_csm_pipeline_stage.py`

### Implementation for User Story 3

- [X] T035 [P] [US3] Implement `CsmConsumer` protocol class in `specmetrics/kernel/csm/model.py`
- [X] T036 [US3] Implement serialization round-trip test — `model_dump_json()` → `model_validate_json()` produces identical model in `specmetrics/kernel/csm/model.py`

**Checkpoint**: US3 is fully functional — downstream engines can consume the CSM via the documented protocol without any framework-specific dependencies.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Run full test suite — verify `pytest tests/unit/test_csm_*.py tests/contract/test_csm_interface.py tests/integration/test_csm_pipeline_stage.py` all pass
- [X] T038 [P] Run performance benchmark — verify SC-001 (500 elements in under 3 seconds) with `pytest tests/unit/test_csm_builder.py -k test_performance_500_elements --benchmark-only`
- [X] T039 [P] Run quickstart validation scenarios from `specs/021-canonical-specification-model/quickstart.md`
- [X] T040 Code cleanup — remove unused imports, verify ruff linting passes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational — first deliverable (MVP)
- **US2 (Phase 4)**: Depends on Foundational (shared models) — can start in parallel with US1
- **US3 (Phase 5)**: Depends on Foundational + US2 — needs query interface
- **Polish (Phase 6)**: Depends on all desired user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories
- **US2 (P1)**: Can start after Phase 2 — May query CSM produced by US1, independently testable via direct CSM construction
- **US3 (P2)**: Depends on US2 (query interface) — but protocol can be developed against the model directly

### Parallel Opportunities

- T002 and T003 in Phase 1 can run in parallel
- T005–T007 in Phase 2 can run in parallel
- T010–T012 in Phase 2 can run in parallel
- All tests marked [P] within a phase can run in parallel
- US1 and US2 can be developed in parallel once Phase 2 is complete
- Within US1: T015–T018 and T025 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch tests for US1 together:
pytest tests/unit/test_csm_model.py tests/unit/test_csm_classifier.py tests/unit/test_csm_metadata.py -v &

# While those run, start the handler implementation:
# (tasks T025, T026)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — EventType, PipelineContext, CANONICAL_EVENT_ORDER
2. Complete Phase 2: Foundational — All models, classifier, builder function
3. Complete Phase 3: User Story 1 — Stage handler, plugin registration, all US1 tests
4. **STOP and VALIDATE**: Run `pytest tests/unit/test_csm_*.py tests/integration/test_csm_pipeline_stage.py -v`
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Core infrastructure ready
2. Add US1 → Build CSM from evidence graphs → Test → **MVP!**
3. Add US2 → Query and inspect CSM → Test
4. Add US3 → Downstream consumer protocol → Test
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (builder + stage plugin + tests)
   - Developer B: User Story 2 (query interface tests)
3. When US1 + US2 complete:
   - Developer A: User Story 3 (consumer protocol + tests)
   - Developer B: Polish (benchmark, linting, quickstart validation)

---

## Phase 7: Convergence

**Purpose**: Close gaps between specification intent and implementation identified by convergence assessment.

- [X] T041 Implement framework-label stripping in `specmetrics/kernel/csm/classifier.py` (add `strip_framework_labels()` with `FRAMEWORK_PATTERNS`) and apply it to `description` in `specmetrics/kernel/csm/builder.py` per FR-003/SC-002 (`partial`)
- [X] T042 Implement multi-pattern conflict detection — track all matching categories per node in `specmetrics/kernel/csm/classifier.py` and populate `ClassificationConflict` records in `specmetrics/kernel/csm/builder.py` per FR-015 (`partial`)
- [X] T043 Refactor `_find_linked()` in `specmetrics/kernel/csm/builder.py` to a two-pass approach (classify all nodes first, then link activities to discovered entities) to ensure symmetric cross-activity linking per US2/AC2 (`partial`)
- [X] T044 Add UUID v4 `@field_validator` to `CsmElement.id` in `specmetrics/kernel/csm/model.py` per data-model.md validation rules (`partial`)
- [X] T045 Add non-empty `@field_validator` to `CsmElement.description` in `specmetrics/kernel/csm/model.py` per data-model.md validation rules (`partial`)
- [X] T046 Remove unused `CATEGORY_MAP` dict from `specmetrics/kernel/csm/builder.py` per plan (`unrequested`)
