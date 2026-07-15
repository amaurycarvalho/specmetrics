# Tasks: Canonical Functional Model Builder

**Input**: Design documents from `specs/007-canonical-functional-model/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included as tasks. Test tasks are marked with [TEST] and should be written before implementation for that story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [TEST?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[TEST]**: Test task (write first, ensure failure, then implement)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/infrastructure/`, `specmetrics/tests/` at repository root
- All paths are relative to the repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and package scaffolding for the CFM module

- [x] T001 Create `specmetrics/kernel/cfm/` package directory with `__init__.py`
- [x] T002 [P] Create test directories: `tests/unit/`, `tests/contract/`, `tests/integration/` (create test `__init__.py` files as needed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core CFM entity models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 Create `CanonicalFunctionalModel`, `Actor`, `FunctionalProcess`, `BusinessRule`, `DataGroup`, `Operation`, `UnclassifiedElement` Pydantic models in `specmetrics/kernel/cfm/model.py`
- [x] T004 [P] Create `BuildMetadata` and `ClassificationConflict` types in `specmetrics/kernel/cfm/metadata.py`
- [x] T005 [P] Create `EvidenceRef` value object (document_id, section_id, text, graph_node_id) in `specmetrics/kernel/cfm/model.py`
- [x] T006 Create `ActorType`, `RuleType`, `DataType`, `RelationshipType` Literal type aliases in `specmetrics/kernel/cfm/model.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Transform evidence graph into canonical functional model (Priority: P1) 🎯 MVP

**Goal**: CFM Builder transforms an `EvidenceGraph` into a framework-independent `CanonicalFunctionalModel` with proper classification and evidence preservation

**Independent Test**: Provide a known evidence graph with diverse semantic elements, run the CFM Builder, and verify every element is correctly classified into the appropriate CFM category with no framework-specific artifacts present

### Tests for User Story 1

- [x] T007 [P] [TEST] [US1] Write unit tests for classification logic in `tests/unit/test_cfm_classifier.py` (fact→BusinessRule/Operation, entity→Actor/DataGroup, relationship→Relationship, operation→Operation)
- [x] T008 [P] [TEST] [US1] Write unit tests for CFM Builder in `tests/unit/test_cfm_builder.py` (empty graph, normal build, conflicting classifications, unclassifiable elements, framework label stripping)

### Implementation for User Story 1

- [x] T009 [P] [US1] Implement classification logic in `specmetrics/kernel/cfm/classifier.py` — map evidence graph nodes to CFM categories by semantic_type with disambiguation for fact→BusinessRule vs Operation and entity→Actor vs DataGroup
- [x] T010 [P] [US1] Implement framework label detection and normalization function in `specmetrics/kernel/cfm/classifier.py` — strip OpenSpec/SpecKit/SpecMetrics framework-specific labels from element names and metadata
- [x] T011 [US1] Implement `build(evidence_graph: EvidenceGraph) -> CanonicalFunctionalModel` in `specmetrics/kernel/cfm/builder.py` — iterate nodes, classify, construct CFM with evidence preservation
- [x] T012 [US1] Handle edge cases in builder: empty graph produces empty CFM; conflicting classifications are flagged in BuildMetadata; unclassifiable elements go to References category
- [x] T013 [US1] Implement CFM Builder as a pipeline stage (`CfmBuilderStage`) satisfying the `EventHandler` protocol in `specmetrics/kernel/cfm/builder.py` — handle `EventType.EVIDENCE_GRAPH_BUILT`, store output via `context.with_stage_output(field_name="canonical_model", value=payload)`

**Checkpoint**: US1 complete — CFM can be built from evidence graph, all 6 categories populated, evidence preserved, framework labels stripped

---

## Phase 4: User Story 2 - Verify CFM correctness via inspection (Priority: P1)

**Goal**: Developer or analyst inspects the CFM to enumerate elements by category, trace evidence references, and verify normalization correctness

**Independent Test**: Inspect CFM output for a known input graph and verify each category contains expected elements with correct evidence references

### Tests for User Story 2

- [x] T014 [P] [TEST] [US2] Write unit tests for model query/inspection in `tests/unit/test_cfm_model.py` (enumeration by category, element lookup by ID, evidence trace query, relationship traversal)

### Implementation for User Story 2

- [x] T015 [P] [US2] Implement enumeration methods on `CanonicalFunctionalModel`: `actors()`, `functional_processes()`, `business_rules()`, `data_groups()`, `relationships()`, `operations()` returning typed dicts/list
- [x] T016 [P] [US2] Implement `get_element(element_id)`, `get_elements_by_category(category)`, `get_elements_by_evidence(document_id)` query methods in `specmetrics/kernel/cfm/model.py`
- [x] T017 [US2] Implement `trace_evidence(element_id)` returning full `EvidenceRef` chain and `get_relationships_for_element(element_id)` traversal in `specmetrics/kernel/cfm/model.py`

**Checkpoint**: US2 complete — CFM elements are fully queryable and traceable to source evidence

---

## Phase 5: User Story 3 - CFM feeds downstream consumers (Priority: P2)

**Goal**: Measurement engine plugins can consume the CFM through a stable, documented interface without framework-specific knowledge

**Independent Test**: Write a mock consumer that reads the CFM and verifies all categories are accessible through the documented interface without importing any framework-specific module

### Tests for User Story 3

- [x] T018 [P] [TEST] [US3] Write contract test for CFM public interface in `tests/contract/test_cfm_interface.py` — verify all 6 categories enumerated, evidence traceable, no framework-specific labels, immutability
- [x] T019 [P] [TEST] [US3] Write integration test for pipeline stage wiring in `tests/integration/test_cfm_pipeline_stage.py` — construct CFM Builder stage, handle EVIDENCE_GRAPH_BUILT event, verify CANONICAL_MODEL_BUILT output in context

### Implementation for User Story 3

- [x] T020 [P] [US3] Define `CFMConsumer` protocol/interface in `specmetrics/kernel/cfm/model.py` — stable public contract for downstream measurement engine plugins
- [x] T021 [US3] Ensure `CanonicalFunctionalModel` is immutable (frozen=True on Pydantic model, no setter methods, read-only accessors)
- [x] T022 [US3] Register `CfmBuilderStage` with `HandlerRegistry` in pipeline initialization so CFM stage runs after Evidence Graph stage

**Checkpoint**: US3 complete — downstream consumers can reliably consume CFM through documented interface

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Serialization, event wiring, documentation, and final validation

- [x] T023 [P] Implement CFM serialization/deserialization for debugging in `specmetrics/infrastructure/serialization/cfm_serializer.py`
- [x] T024 [P] Wire `CanonicalModelBuilt` event emission in `CfmBuilderStage.handle()` — emit structured event with element counts, build duration, conflicts
- [x] T025 Run all CFM tests: `pytest tests/unit/ tests/contract/ tests/integration/ -v`
- [x] T026 Run quickstart.md validation scenarios end-to-end
- [x] T027 Final review: verify immutability, evidence traceability, and framework label stripping across all test data

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion — MVP scope
- **User Story 2 (Phase 4)**: Depends on Foundational + US1 completion (needs built CFM)
- **User Story 3 (Phase 5)**: Depends on Foundational + US1 + US2 completion (needs stable CFM with query interface)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — No dependencies on other stories ⭐ MVP
- **US2 (P1)**: Can start after US1 — builds on query/inspection of US1 output
- **US3 (P2)**: Can start after US1 + US2 — contract testing requires stable CFM

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T001, T002: Setup tasks can run in parallel
- T003, T004, T005, T006: All foundational model tasks can run in parallel
- T007, T008: US1 test tasks can run in parallel
- T009, T010: US1 implementation models can run in parallel
- T014, T015, T016: US2 test + query model tasks can run in parallel (after US1)
- T018, T019, T020: US3 contract test + protocol tasks can run in parallel (after US2)
- T023, T024: Polish serialization + event emission can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T007 Write unit tests for classification logic in tests/unit/test_cfm_classifier.py"
Task: "T008 Write unit tests for CFM Builder in tests/unit/test_cfm_builder.py"

# Launch all classification implementations together:
Task: "T009 Implement classification logic in specmetrics/kernel/cfm/classifier.py"
Task: "T010 Implement framework label detection in specmetrics/kernel/cfm/classifier.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently — build CFM, verify classification, evidence preservation, no framework labels
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (classification + builder)
   - Developer B: User Story 1 tests
3. After US1 complete:
   - Developer A: User Story 2 (query/inspection)
   - Developer B: User Story 3 (contracts + integration)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [TEST] tasks = write before implementation, ensure failure first
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
