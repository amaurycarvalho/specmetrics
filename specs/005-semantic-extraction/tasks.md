---

description: "Task list for Semantic Extraction (F04) implementation"

---

# Tasks: Semantic Extraction

**Input**: Design documents from `specs/005-semantic-extraction/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature defines a new pipeline stage and requires verification of extraction provider interface compliance, evidence provenance, and F02 plugin integration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/application/`,
  `specmetrics/sdk/`, `specmetrics/plugins/`, `specmetrics/cli/`,
  `specmetrics/mcp/`, `specmetrics/infrastructure/`, `specmetrics/tests/`
  at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization for extraction infrastructure

- [X] T001 [P] Create `specmetrics/kernel/extraction_provider.py` —
  ExtractionProvider Protocol, ExtractedElement model, EvidenceReference model,
  ExtractionResult model, ProcessingStats model
- [X] T002 [P] Create `specmetrics/kernel/extraction_registry.py` —
  ProviderRouter class for document-type to provider mapping
- [X] T003 Create `specmetrics/kernel/extraction_stage.py` — ExtractionStage
  EventHandler skeleton (placeholder handle method)
- [X] T004 Update `specmetrics/kernel/__init__.py` — Export ExtractionProvider,
  ExtractedElement, EvidenceReference, ExtractionResult, ProcessingStats,
  ProviderRouter, ExtractionStage

**Checkpoint**: Extraction interface namespaces are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and provider interface that MUST be complete before
ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] [US1] Create `ExtractedElement` Pydantic model in
  `specmetrics/kernel/extraction_provider.py` — id, type (fact/entity/relationship/
  operation), confidence (0.0–1.0), evidence (EvidenceReference), content per
  data-model.md
- [X] T006 [P] [US1] Create `EvidenceReference` Pydantic model in
  `specmetrics/kernel/extraction_provider.py` — document_id, section_id (optional),
  text
- [X] T007 [P] [US1] Create `ExtractionResult` and `ProcessingStats` Pydantic
  models in `specmetrics/kernel/extraction_provider.py`
- [X] T008 [US1] Create `ExtractionProvider` Protocol in
  `specmetrics/kernel/extraction_provider.py` — extract() and supports_type()
  method signatures

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Extract semantic elements from specification documents (Priority: P1) 🎯 MVP

**Goal**: A developer triggers the measurement pipeline. The ExtractionStage
receives normalized Document objects from the Specification Adapter layer and
extracts structured semantic elements — facts, entities, relationships, and
operations.

**Independent Test**: Can be tested by providing a mock set of normalized
Document objects, running the extraction stage, and verifying the output
contains expected semantic elements.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T009 [P] [US1] Test: A class implementing ExtractionProvider Protocol
  passes structural check in `tests/unit/test_extraction_provider.py`
- [X] T010 [P] [US1] Test: A class missing extract() does NOT pass Protocol
  check in `tests/unit/test_extraction_provider.py`
- [X] T011 [P] [US1] Test: A class missing supports_type() does NOT pass
  Protocol check in `tests/unit/test_extraction_provider.py`
- [X] T012 [P] [US1] Test: ExtractionStage handles DOCUMENTS_DISCOVERED event
  and returns ExtractionResult in `tests/unit/test_extraction_stage.py`
- [X] T013 [P] [US1] Test: ExtractionStage routes documents to correct provider
  based on document_type in `tests/unit/test_extraction_stage.py`
- [X] T014 [US1] Test: ExtractionStage processes multiple documents and
  consolidates results in `tests/unit/test_extraction_stage.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement ExtractionProvider Protocol in
  `specmetrics/kernel/extraction_provider.py` — structural typing with
  extract() and supports_type()
- [X] T016 [P] [US1] Implement ProviderRouter in
  `specmetrics/kernel/extraction_registry.py` — resolve document types to
  providers, register providers with optional type overrides
- [X] T017 [US1] Implement ExtractionStage in
  `specmetrics/kernel/extraction_stage.py` — EventHandler for
  DOCUMENTS_DISCOVERED, iterates documents and delegates to resolved providers,
  consolidates results

**Checkpoint**: User Story 1 is complete — extraction stage processes documents.

---

## Phase 4: User Story 2 — Extraction preserves evidence provenance (Priority: P1)

**Goal**: An analyst inspects a measurement result and needs to verify its origin.
Each extracted semantic element carries a reference to the exact document, section,
and text fragment that supports it.

**Independent Test**: Can be tested by extracting from a known document and
verifying that every extracted element includes a non-empty source reference with
document ID, section identifier, and text excerpt.

### Tests for User Story 2

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T018 [P] [US2] Test: EvidenceReference accepts valid document_id and text
  in `tests/unit/test_extraction_provider.py`
- [X] T019 [P] [US2] Test: ExtractedElement requires valid evidence reference
  in `tests/unit/test_extraction_provider.py`
- [X] T020 [US2] Test: ExtractionStage output includes evidence references for
  each element in `tests/unit/test_extraction_stage.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement EvidenceReference validation — document_id and
  text must be non-empty in
  `specmetrics/kernel/extraction_provider.py`
- [X] T022 [US2] Integrate evidence provenance into ExtractionStage — each
  ExtractedElement from a provider carries provider-assigned evidence, stage
  verifies evidence completeness in
  `specmetrics/kernel/extraction_stage.py`

**Checkpoint**: User Story 2 is complete — evidence provenance is preserved.

---

## Phase 5: User Story 3 — Extraction providers are pluggable (Priority: P2)

**Goal**: A developer implements an extraction provider plugin and registers it
via the F02 plugin system. The system discovers it at startup and routes
documents to it based on document type.

**Independent Test**: Can be tested by implementing a mock extraction provider
as a plugin, registering it through F02, and verifying it is invoked when a
document of its declared type is processed.

### Tests for User Story 3

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T023 [P] [US3] Test: ProviderRouter.register() stores provider for
  document type in `tests/unit/test_extraction_registry.py`
- [X] T024 [P] [US3] Test: ProviderRouter.resolve() returns correct provider
  for matching type in `tests/unit/test_extraction_registry.py`
- [X] T025 [P] [US3] Test: ProviderRouter.resolve() returns None when no
  provider matches in `tests/unit/test_extraction_registry.py`
- [X] T026 [US3] Integration test: Mock provider registered via F02 plugin
  mechanism is available through ProviderRouter in
  `tests/integration/test_extraction_pipeline.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement ProviderRouter.resolve() — iterates registered
  providers calling supports_type(), returns first match in
  `specmetrics/kernel/extraction_registry.py`
- [X] T028 [US3] Implement F02 plugin discovery integration — extraction
  providers with plugin_type SEMANTIC are discovered and registered with
  ProviderRouter in `specmetrics/kernel/extraction_registry.py`
- [X] T029 [US3] Update `specmetrics/kernel/__init__.py` — ensure ProviderRouter
  is exported

**Checkpoint**: User Story 3 is complete — extraction providers are pluggable.

---

## Phase 6: User Story 4 — Industry-standard extraction strategies work out of the box (Priority: P2)

**Goal**: A user runs extraction immediately after installation without configuring
extraction providers. The system includes a built-in LLM-assisted extraction
provider and a structural provider for known SDD frameworks.

**Independent Test**: Can be tested by installing the platform, providing a
repository with documents, and running extraction without any plugin configuration.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T030 [P] [US4] Test: Built-in LLM provider handles documents with valid
  LiteLLM response in `tests/unit/test_llm_provider.py`
- [X] T031 [P] [US4] Test: Built-in LLM provider degrades gracefully when
  LLM unavailable in `tests/unit/test_llm_provider.py`
- [X] T032 [US4] Integration test: Full pipeline with built-in provider produces
  ExtractionResult in `tests/integration/test_extraction_pipeline.py`

### Implementation for User Story 4

- [X] T033 [P] [US4] Implement built-in LLM-assisted extraction provider in
  `specmetrics/plugins/semantic/llm_provider.py` — uses LiteLLM gateway,
  graceful degradation to structural parsing, supports all document types
- [X] T034 [US4] Register built-in provider as default in ProviderRouter —
  automatically available when no explicit routing configured in
  `specmetrics/kernel/extraction_registry.py`

**Checkpoint**: User Story 4 is complete — extraction works out of the box.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Add docstrings to all public extraction classes and methods
- [X] T036 Run quickstart.md validation scenarios end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (extraction logic vs evidence model)
  - US3 depends on US1 + Foundational (provider routing needs ExtractionProvider interface)
  - US4 depends on US3 (built-in providers use the plugin registration mechanism)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational
- **User Story 2 (P1)**: Can start after Foundational — independent from US1
- **User Story 3 (P2)**: Depends on US1 + Foundational (needs ExtractionProvider and ProviderRouter)
- **User Story 4 (P2)**: Depends on US3 (needs provider registration for built-in provider)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- T001 and T002 can run in parallel
- US1 and US2 can proceed in parallel once Foundational is complete
- All tests within a story marked [P] can run in parallel
- ExtractionProvider and EvidenceReference models can be built in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "T009 [P] [US1] Test: Protocol check - valid provider"
Task: "T010 [P] [US1] Test: Protocol check - missing extract()"
Task: "T011 [P] [US1] Test: Protocol check - missing supports_type()"
Task: "T012 [P] [US1] Test: ExtractionStage handles event"
Task: "T013 [P] [US1] Test: ExtractionStage routes correctly"
Task: "T014 [US1] Test: ExtractionStage consolidates results"

# Launch implementation tasks in parallel:
Task: "T015 [P] [US1] Implement ExtractionProvider Protocol"
Task: "T016 [P] [US1] Implement ProviderRouter"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test extraction stage independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP!)
3. Add User Story 2 → Test independently → Demo
4. Add User Story 3 → Test independently → Demo (F02 integration)
5. Add User Story 4 → Test independently → Demo (out-of-box experience)
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break
  independence
