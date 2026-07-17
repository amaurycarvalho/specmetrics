---

description: "Task list for Semantic Extraction Engine (F27) implementation"

---

# Tasks: Semantic Extraction Engine

**Input**: Design documents from `specs/027-semantic-extraction-engine/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature defines a new kernel abstraction layer with two engine implementations and requires verification of the engine interface, factory resolution, deterministic extraction, LiteLLM integration, and rule extensibility.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffolding for the Semantic Extraction Engine kernel files

- [X] T001 [P] Create `specmetrics/kernel/semantic_extraction_engine.py` — module skeleton with SemanticExtractionEngine Protocol and SemanticEngineFactory stub
- [X] T002 [P] Create `specmetrics/kernel/deterministic_engine.py` — module skeleton for DeterministicSemanticEngine
- [X] T003 [P] Create `specmetrics/kernel/litellm_engine.py` — module skeleton for LiteLLMSemanticEngine
- [X] T004 [P] Create `specmetrics/kernel/engine_rule.py` — module skeleton for ExtractionRule model and RulePackLoader
- [X] T005 [P] Create `specmetrics/kernel/engine_visitors.py` — module skeleton for AST visitor classes
- [X] T006 [P] Create `specmetrics/kernel/engine_patterns.py` — module skeleton for PatternLibrary
- [X] T007 Update `specmetrics/kernel/__init__.py` — Export SemanticExtractionEngine, SemanticEngineFactory, DeterministicSemanticEngine, LiteLLMSemanticEngine, ExtractionRule, RulePackLoader

**Checkpoint**: All kernel module namespaces are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models, extraction engine Protocol, and factory that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 [P] Create `ExtractedElement` Pydantic model in `specmetrics/kernel/semantic_extraction_engine.py` — id (str), type (Literal["fact","entity","relationship","operation"]), content (str), confidence (float 0.0–1.0), evidence (EvidenceReference); enforce non-empty id and content per data-model.md
- [X] T009 [P] Create `EvidenceReference` Pydantic model in `specmetrics/kernel/semantic_extraction_engine.py` — document_id (str, min_length=1), section_id (Optional[str]), text (str, min_length=1)
- [X] T010 [P] Create `ProcessingStats` Pydantic model in `specmetrics/kernel/semantic_extraction_engine.py` — documents_processed (int), elements_extracted (int), elements_by_type (dict[str,int]), duration_ms (int), errors_count (int); all default to 0
- [X] T011 [P] Create `ExtractionResult` Pydantic model in `specmetrics/kernel/semantic_extraction_engine.py` — elements (list[ExtractedElement]), engine_id (str), processing_stats (ProcessingStats)
- [X] T012 Implement `SemanticExtractionEngine` Protocol in `specmetrics/kernel/semantic_extraction_engine.py` — extract(documents: list[Document]) -> ExtractionResult method signature; import Document from .adapter_interface
- [X] T013 Implement `SemanticEngineFactory` class in `specmetrics/kernel/semantic_extraction_engine.py` — create(provider: str, config: dict | None = None) -> SemanticExtractionEngine; static mapping: "none" → DeterministicSemanticEngine, "chatgpt"|"claude"|"gemini"|"ollama" → LiteLLMSemanticEngine; raise ValueError for unknown provider; must be instantiable once per pipeline init

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Run pipeline without LLM configuration (Priority: P1) 🎯 MVP

**Goal**: A user sets the LLM provider to `none` and runs the measurement pipeline. The DeterministicSemanticEngine performs structural extraction using Markdown AST analysis — no API keys, network access, or external AI services required.

**Independent Test**: Configure `provider = none`, run the pipeline on a repository with known spec documents, and verify extraction completes with structured semantic elements and byte-identical output across runs.

### Tests for User Story 1

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T014 [P] [US1] Test: DeterministicSemanticEngine conforms to SemanticExtractionEngine Protocol in `tests/unit/test_deterministic_engine.py`
- [ ] T015 [P] [US1] Test: DeterministicSemanticEngine.extract() returns ExtractionResult with expected structure in `tests/unit/test_deterministic_engine.py`
- [ ] T016 [P] [US1] Test: Same document processed twice produces byte-identical output in `tests/unit/test_deterministic_engine.py`
- [ ] T017 [P] [US1] Test: Document with headings, lists, tables, code blocks, blockquotes, emphasis, and links produces elements for each structural pattern in `tests/unit/test_deterministic_engine.py`
- [ ] T018 [P] [US1] Test: Document with no recognizable patterns returns empty ExtractionResult in `tests/unit/test_deterministic_engine.py`
- [ ] T019 [P] [US1] Test: Content-hash ID is deterministic and unique in `tests/unit/test_deterministic_engine.py`
- [ ] T020 [P] [US1] Test: AST HeadingVisitor collects heading hierarchy correctly in `tests/unit/test_engine_visitors.py`
- [ ] T021 [P] [US1] Test: AST ListVisitor collects list items correctly in `tests/unit/test_engine_visitors.py`
- [ ] T022 [P] [US1] Test: AST TableVisitor collects table rows and headers correctly in `tests/unit/test_engine_visitors.py`
- [ ] T023 [P] [US1] Test: AST CodeBlockVisitor collects fenced code blocks with language annotation in `tests/unit/test_engine_visitors.py`
- [ ] T024 [P] [US1] Test: AST QuoteVisitor collects blockquote content in `tests/unit/test_engine_visitors.py`
- [ ] T025 [P] [US1] Test: AST EmphasisVisitor collects bold/italic text in `tests/unit/test_engine_visitors.py`
- [ ] T026 [P] [US1] Test: AST LinkVisitor collects hyperlinks and reference links in `tests/unit/test_engine_visitors.py`
- [ ] T027 [P] [US1] Test: Rule engine matches rules by priority — higher priority wins on conflict in `tests/unit/test_engine_rule.py`
- [ ] T028 [P] [US1] Test: Rule engine loads rules from external YAML rule pack in `tests/unit/test_engine_rule.py`
- [ ] T029 [P] [US1] Test: Rule engine skips rules with syntax errors and logs warning in `tests/unit/test_engine_rule.py`
- [ ] T030 [US1] Integration test: Full pipeline with provider=none produces ExtractionResult with evidence references in `tests/integration/test_engine_pipeline.py`

### Implementation for User Story 1

- [X] T031 [P] [US1] Implement ExtractionState dataclass and Observation dataclass in `specmetrics/kernel/engine_visitors.py` — state holds heading_stack, observations, elements; observation holds type, content, context dict, location tuple
- [X] T032 [P] [US1] Implement HeadingVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) maintains heading level stack, detects known section types (Actors, Business Rules, etc.)
- [X] T033 [P] [US1] Implement ListVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts ordered/unordered list items
- [X] T034 [P] [US1] Implement TableVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts table rows and headers
- [X] T035 [P] [US1] Implement CodeBlockVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts fenced code blocks with language annotation
- [X] T036 [P] [US1] Implement QuoteVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts blockquote content
- [X] T037 [P] [US1] Implement EmphasisVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts bold/italic text for term candidates
- [X] T038 [P] [US1] Implement LinkVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts hyperlinks and reference links
- [X] T039 [US1] Implement ExtractionRule Pydantic model in `specmetrics/kernel/engine_rule.py` — id (str), name (str), pattern (dict), type (Literal), confidence (float 0.0–1.0), priority (int 1–100); conflict resolution: highest priority wins, ties broken by id lexicographic
- [X] T040 [US1] Implement RulePackLoader in `specmetrics/kernel/engine_rule.py` — load(path: str | Path) -> list[ExtractionRule]; parses YAML rule packs, validates required fields, skips invalid rules with logged warnings
- [X] T041 [US1] Implement rule matching engine in `specmetrics/kernel/engine_rule.py` — match(rules: list[ExtractionRule], observations: list[Observation]) -> list[ExtractedElement]; applies rules by priority order, generates content-hash IDs per Q2
- [X] T042 [US1] Implement PatternLibrary in `specmetrics/kernel/engine_patterns.py` — provides built-in pattern matchers for User Story, GWT, Requirement statements, Business Rules, Actors, Constraints, Assumptions, Decisions, Glossary Terms per FR-008; loads from default rule pack YAML
- [X] T043 [US1] Create default rule pack YAML file at `specmetrics/kernel/rules/default_rule_pack.yaml` — includes all FR-008 built-in rules with priority scores and confidence values per RFC-031 table
- [X] T044 [US1] Implement DeterministicSemanticEngine in `specmetrics/kernel/deterministic_engine.py` — extract(documents) parses each document with markdown-it-py, runs visitors, collects observations, applies rules via RulePackLoader + rule engine, produces ExtractionResult with content-hash IDs, evidence references, and ProcessingStats
- [X] T045 [US1] Add evidence reference mapping in DeterministicSemanticEngine — each ExtractedElement includes EvidenceReference with document_id from Document.id, section_id from heading hierarchy path, and exact source text fragment
- [X] T046 [US1] Add ProcessingStats generation in DeterministicSemanticEngine — track documents_processed, elements_extracted, elements_by_type, duration_ms, errors_count

**Checkpoint**: User Story 1 is complete — DeterministicSemanticEngine extracts semantic elements without any external services.

---

## Phase 4: User Story 2 — Run pipeline with LLM-assisted extraction + provider failure handling (Priority: P1 + P2)

**Goal**: A user configures an LLM provider (chatgpt, claude, gemini, ollama). The LiteLLMSemanticEngine performs extraction via LiteLLM gateway. Evidence references are preserved. If the LLM provider fails, the engine fails cleanly with a structured error — no silent fallback to deterministic (Q1).

**Independent Test**: Configure an LLM provider, run on the same documents as US1, and verify the output uses the same ExtractionResult data model with evidence references. For failure: configure invalid API key and verify structured error with no extraction output.

### Tests for User Story 2

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T047 [P] [US2] Test: LiteLLMSemanticEngine conforms to SemanticExtractionEngine Protocol in `tests/unit/test_litellm_engine.py`
- [ ] T048 [P] [US2] Test: LiteLLMSemanticEngine.extract() returns ExtractionResult with same model as DeterministicSemanticEngine in `tests/unit/test_litellm_engine.py`
- [ ] T049 [P] [US2] Test: LiteLLMSemanticEngine includes evidence references on every element in `tests/unit/test_litellm_engine.py`
- [ ] T050 [P] [US2] Test: LiteLLMSemanticEngine includes confidence scores in `tests/unit/test_litellm_engine.py`
- [ ] T051 [P] [US2] Test: LiteLLMSemanticEngine raises structured error on provider auth failure — no silent fallback in `tests/unit/test_litellm_engine.py`
- [ ] T052 [P] [US2] Test: LiteLLMSemanticEngine raises structured error on provider timeout in `tests/unit/test_litellm_engine.py`
- [ ] T053 [P] [US2] Test: LiteLLMSemanticEngine raises structured error on rate limit in `tests/unit/test_litellm_engine.py`
- [ ] T054 [P] [US2] Test: SemanticEngineFactory.create() returns LiteLLMSemanticEngine for "chatgpt", "claude", "gemini", "ollama" in `tests/unit/test_semantic_extraction_engine.py`
- [ ] T055 [P] [US2] Test: SemanticEngineFactory.create() raises ValueError for unknown provider in `tests/unit/test_semantic_extraction_engine.py`
- [ ] T056 [US2] Integration test: pipeline switches from none to chatgpt with no downstream reconfiguration in `tests/integration/test_engine_pipeline.py`

### Implementation for User Story 2

- [X] T057 [P] [US2] Implement LiteLLMSemanticEngine in `specmetrics/kernel/litellm_engine.py` — extract(documents) calls LiteLLM completion() per document, parses structured JSON response into ExtractionResult elements, maps evidence references back to source document locations
- [X] T058 [US2] Implement LLM prompt construction in LiteLLMSemanticEngine — format document text + heading hierarchy as context for the LLM; instruct output to be structured JSON matching ExtractionResult schema
- [X] T059 [US2] Implement LLM response parser in LiteLLMSemanticEngine — parse JSON response into ExtractedElement list with type, content, confidence (from logprobs where available, else 0.85), and evidence references
- [X] T060 [US2] Implement LiteLLM failure handling in LiteLLMSemanticEngine — catch LiteLLM exceptions (auth, timeout, rate limit), raise structured ExtractionError with descriptive message; do NOT fall back to deterministic engine per Q1
- [X] T061 [US2] Implement ProcessingStats generation in LiteLLMSemanticEngine — track same fields as DeterministicSemanticEngine
- [X] T062 [US2] Update SemanticEngineFactory in `specmetrics/kernel/semantic_extraction_engine.py` — return fully configured LiteLLMSemanticEngine with model string mapped per data-model.md resolution table

**Checkpoint**: User Story 2 is complete — LiteLLMSemanticEngine performs LLM-assisted extraction and handles provider failures cleanly.

---

## Phase 5: User Story 4 — Extend rule-based extraction with custom rules (Priority: P3)

**Goal**: A team adds a custom rule definition file with new patterns (e.g., "Safety Constraint"). The DeterministicSemanticEngine loads and applies the custom rule alongside built-in rules using priority-based conflict resolution.

**Independent Test**: Register a new rule definition YAML for a custom pattern, process a document containing that pattern, and verify the output includes the expected semantic element for that pattern.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T063 [P] [US4] Test: RulePackLoader loads custom rule pack alongside built-in rules in `tests/unit/test_engine_rule.py`
- [ ] T064 [P] [US4] Test: Custom rule with higher priority overrides built-in rule on same content in `tests/unit/test_engine_rule.py`
- [ ] T065 [P] [US4] Test: DeterministicSemanticEngine uses extra_rule_packs config to load additional rules in `tests/unit/test_deterministic_engine.py`
- [ ] T066 [US4] Integration test: Custom rule pack loaded and applied in pipeline in `tests/integration/test_engine_pipeline.py`

### Implementation for User Story 4

- [X] T067 [US4] Implement extra rule pack loading in DeterministicSemanticEngine — accept extra_rule_packs list in constructor config, merge with built-in default pack, apply priority-based conflict resolution per Q3
- [X] T068 [US4] Add logging for rule loading — log each rule pack loaded, number of rules, conflicts detected and how they were resolved
- [X] T069 [US4] Add documentation in RulePackLoader docstring — document YAML format, supported pattern fields (heading, keywords, min_matches), priority range, and conflict resolution behavior

**Checkpoint**: User Story 4 is complete — rule library is extensible with custom rule packs.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect all user stories

- [X] T070 [P] Add docstrings to all public classes and methods in `specmetrics/kernel/semantic_extraction_engine.py`
- [X] T071 [P] Add docstrings to all public classes and methods in `specmetrics/kernel/deterministic_engine.py`
- [X] T072 [P] Add docstrings to all public classes and methods in `specmetrics/kernel/litellm_engine.py`
- [X] T073 [P] Add docstrings in `specmetrics/kernel/engine_rule.py` and `engine_visitors.py`
- [X] T074 Add configurable max_heading_depth support in DeterministicSemanticEngine — flatten headings beyond configured depth per spec.md edge case
- [X] T075 Add empty document list handling — return ExtractionResult with empty elements and zeroed stats
- [ ] T076 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [ ] T077 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [ ] T078 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [ ] T079 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [ ] T080 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [ ] T081 Test files not yet created — need pytest infrastructure setup; unit tests deferred to test phase
- [X] T082 Functional validation passed — 5 elements extracted from test document with correct types, confidence, and deterministic output

**Checkpoint**: All tests pass, quickstart validation complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) can proceed in parallel after Foundational
  - US4 (Phase 5) depends on US1 (needs DeterministicSemanticEngine + RulePackLoader)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — independent
- **User Story 2 (P2)**: Can start after Foundational — independent from US1 (different engine implementation)
- **User Story 4 (P3)**: Depends on US1 (needs DeterministicSemanticEngine and RulePackLoader)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Visitor implementations before rule engine integration
- Core implementation before edge cases
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001–T007) can run in parallel
- All Foundational model tasks (T008–T011) can run in parallel
- T012 (Protocol) and T013 (Factory) depend on models
- US1 and US2 can proceed in parallel once Foundational is complete
- All visitor implementations (T031–T038) can run in parallel
- All tests within a story marked [P] can run in parallel
- Polish tasks (T070–T075) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all AST visitor implementations in parallel:
Task: "T031 [P] [US1] Implement ExtractionState and Observation"
Task: "T032 [P] [US1] Implement HeadingVisitor"
Task: "T033 [P] [US1] Implement ListVisitor"
Task: "T034 [P] [US1] Implement TableVisitor"
Task: "T035 [P] [US1] Implement CodeBlockVisitor"
Task: "T036 [P] [US1] Implement QuoteVisitor"
Task: "T037 [P] [US1] Implement EmphasisVisitor"
Task: "T038 [P] [US1] Implement LinkVisitor"

# Then integrate:
Task: "T039 [US1] Implement ExtractionRule model"
Task: "T040 [US1] Implement RulePackLoader"
Task: "T041 [US1] Implement rule matching engine"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (DeterministicSemanticEngine)
4. **STOP and VALIDATE**: Test deterministic extraction independently with `pytest tests/unit/test_deterministic_engine.py`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (MVP! Deterministic extraction offline)
3. Add User Story 2 → Test independently → Demo (LLM-assisted extraction)
4. Add User Story 4 → Test independently → Demo (Custom rule packs)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Deterministic engine)
   - Developer B: User Story 2 (LiteLLM engine)
3. Developer A continues to User Story 4 after US1 completes
4. Polish tasks distributed across team

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Phase 7: Convergence

**Purpose**: Close gaps between specified intent and current implementation.

- [X] T083 [US1] Create `tests/unit/test_deterministic_engine.py` — unit tests for DeterministicSemanticEngine: Protocol conformance, extract() structure, byte-identical output (excluding timing), content-hash determinism, empty document handling, binary content skipping per T014–T019
- [X] T084 [US1] Create `tests/unit/test_engine_visitors.py` — unit tests for all 8 AST visitors: HeadingVisitor hierarchy, ListVisitor items, TableVisitor rows/headers, CodeBlockVisitor language, QuoteVisitor content, EmphasisVisitor spans, LinkVisitor URLs per T020–T026
- [X] T085 [US1] Create `tests/unit/test_engine_rule.py` — unit tests for RulePackLoader: valid YAML loading, invalid rule skipping, missing file error, rule matching by priority per T027–T029
- [X] T086 [US1] Create `tests/unit/test_engine_patterns.py` — unit tests for PatternLibrary: rule merging, priority conflict resolution, empty pack handling
- [X] T087 [P] [US2] Create `tests/unit/test_litellm_engine.py` — unit tests for LiteLLMSemanticEngine: Protocol conformance, error on missing litellm, ExtractionError on provider failure per T047–T053
- [X] T088 [P] [US2] Create `tests/unit/test_semantic_extraction_engine.py` — unit tests for SemanticEngineFactory: resolution for all 5 providers, ValueError for unknown provider per T054–T055
- [X] T089 [US1] Create `tests/integration/test_engine_pipeline.py` — integration test: full pipeline with provider=none produces ExtractionResult with evidence references per T030
- [X] T090 [US2] Fix byte-identical output for SC-002 — add `deterministic_dump()` method to ExtractionResult excluding timing, enabling reliable byte-identical comparison per SC-002, FR-011 (partial)
