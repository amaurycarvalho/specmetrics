---

description: "Task list for Deterministic Semantic Engine (F28) implementation"

---

# Tasks: Deterministic Semantic Engine

**Input**: Design documents from `specs/028-deterministic-semantic-engine/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included — this feature defines a new kernel module with visitor classes, rule engine, and pattern library requiring unit and integration test coverage.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Module scaffolding for the Deterministic Semantic Engine kernel files

- [ ] T001 [P] Create `specmetrics/kernel/deterministic_engine.py` — module skeleton for DeterministicSemanticEngine
- [ ] T002 [P] Create `specmetrics/kernel/engine_rule.py` — module skeleton for ExtractionRule model + RulePackLoader
- [ ] T003 [P] Create `specmetrics/kernel/engine_visitors.py` — module skeleton for AST visitor classes
- [ ] T004 [P] Create `specmetrics/kernel/engine_patterns.py` — module skeleton for PatternLibrary
- [ ] T005 [P] Create `specmetrics/kernel/rules/` directory for rule pack YAML files
- [ ] T006 Update `specmetrics/kernel/__init__.py` — Export DeterministicSemanticEngine

**Checkpoint**: All kernel module namespaces are in place.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and internal types that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Create `ExtractionState` dataclass in `specmetrics/kernel/engine_visitors.py` — fields: heading_stack (list[str]), observations (list[Observation]), elements (list[ExtractedElement])
- [ ] T008 [P] Create `Observation` dataclass in `specmetrics/kernel/engine_visitors.py` — fields: type (str), content (str), context (dict), location (tuple[str, str | None])
- [ ] T009 [P] Create `ExtractionRule` Pydantic model in `specmetrics/kernel/engine_rule.py` — fields: id (str), name (str), pattern (dict), type (Literal["fact","entity","relationship","operation"]), confidence (float, 0.0–1.0), priority (int, 1–100); Pydantic validators for range checks
- [ ] T010 Implement `RulePackLoader` in `specmetrics/kernel/engine_rule.py` — static method load(path) reads YAML with ruamel.yaml, validates required fields, returns list[ExtractionRule]; skips invalid rules with logged warning per research.md section 4

**Checkpoint**: Foundation ready — visitor and rule engine implementation can begin.

---

## Phase 3: User Story 1+2+3 — Core Deterministic Engine (Priority: P1) 🎯 MVP

**Goal**: The DeterministicSemanticEngine processes specification documents through AST visitors, applies the rule engine and pattern library, and produces ExtractionResult with evidence references, deterministic confidence scores, and byte-identical output for identical inputs.

**Independent Test**: Provide a document with headings, lists, tables, code blocks, blockquotes, emphasis, and links; run extraction twice; verify output contains appropriate semantic elements and is byte-identical across runs.

### Tests for User Story 1+2+3

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T011 [P] [US1] Test: HeadingVisitor collects headings with correct level and hierarchy in `tests/unit/test_engine_visitors.py`
- [ ] T012 [P] [US1] Test: ListVisitor extracts ordered and unordered list items in `tests/unit/test_engine_visitors.py`
- [ ] T013 [P] [US1] Test: TableVisitor extracts table rows and headers in `tests/unit/test_engine_visitors.py`
- [ ] T014 [P] [US1] Test: ParagraphVisitor collects paragraph text content in `tests/unit/test_engine_visitors.py`
- [ ] T015 [P] [US1] Test: CodeBlockVisitor extracts fenced code blocks with language annotations in `tests/unit/test_engine_visitors.py`
- [ ] T016 [P] [US1] Test: QuoteVisitor extracts blockquote content in `tests/unit/test_engine_visitors.py`
- [ ] T017 [P] [US1] Test: EmphasisVisitor extracts bold and italic text in `tests/unit/test_engine_visitors.py`
- [ ] T018 [P] [US1] Test: LinkVisitor extracts hyperlinks and reference links in `tests/unit/test_engine_visitors.py`
- [ ] T019 [P] [US1] Test: Empty token list handled by all visitors without exceptions in `tests/unit/test_engine_visitors.py`
- [ ] T020 [P] [US3] Test: RulePackLoader.load() returns correct ExtractionRule list from valid YAML in `tests/unit/test_engine_rule.py`
- [ ] T021 [P] [US3] Test: RulePackLoader.load() skips invalid rules and logs warning in `tests/unit/test_engine_rule.py`
- [ ] T022 [P] [US3] Test: RulePackLoader.load() raises FileNotFoundError for missing file in `tests/unit/test_engine_rule.py`
- [ ] T023 [P] [US3] Test: PatternLibrary.match() returns highest-priority rule on conflict (Q2) in `tests/unit/test_engine_patterns.py`
- [ ] T024 [P] [US3] Test: PatternLibrary.match() returns ExtractedElement with correct type and confidence in `tests/unit/test_engine_patterns.py`
- [ ] T025 [P] [US3] Test: Default rule pack contains all FR-006 patterns in `tests/unit/test_engine_patterns.py`
- [ ] T026 [P] [US2] Test: DeterministicSemanticEngine conforms to SemanticExtractionEngine Protocol in `tests/unit/test_deterministic_engine.py`
- [ ] T027 [P] [US2] Test: Same document processed twice produces byte-identical output (FR-011) in `tests/unit/test_deterministic_engine.py`
- [ ] T028 [P] [US1] Test: Document with all structural types produces elements for each pattern (FR-004) in `tests/unit/test_deterministic_engine.py`
- [ ] T029 [P] [US2] Test: Evidence references include document_id, section_id, text, and rule_id (FR-008) in `tests/unit/test_deterministic_engine.py`
- [ ] T030 [P] [US2] Test: Confidence scores match RFC-031 table (FR-009) in `tests/unit/test_deterministic_engine.py`
- [ ] T031 [P] [US2] Test: Content-hash IDs are deterministic and unique (FR-014) in `tests/unit/test_deterministic_engine.py`
- [ ] T032 [P] [US1] Test: ProcessingStats reported with correct counts (Q3) in `tests/unit/test_deterministic_engine.py`
- [ ] T033 [P] [US1] Test: Document with no recognizable patterns returns empty ExtractionResult in `tests/unit/test_deterministic_engine.py`
- [ ] T034 [P] [US1] Test: Binary content is skipped with logged warning in `tests/unit/test_deterministic_engine.py`
- [ ] T035 [US3] Integration test: Full pipeline with provider=none produces ExtractionResult in `tests/integration/test_deterministic_pipeline.py`

### Implementation for User Story 1+2+3

- [ ] T036 [P] [US1] Implement HeadingVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) maintains heading level stack via token.nesting, detects known section types (Actors, Business Rules, Constraints, etc.)
- [ ] T037 [P] [US1] Implement ListVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts bullet_list/ordered_list items with nesting level
- [ ] T038 [P] [US1] Implement TableVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts thead/tbody rows, th/td cells
- [ ] T039 [P] [US1] Implement ParagraphVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) collects paragraph text content
- [ ] T040 [P] [US1] Implement CodeBlockVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts fenced code content and language tag from token.info
- [ ] T041 [P] [US1] Implement QuoteVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts blockquote content
- [ ] T042 [P] [US1] Implement EmphasisVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts strong and em text spans
- [ ] T043 [P] [US1] Implement LinkVisitor in `specmetrics/kernel/engine_visitors.py` — visit(tokens, state) extracts link URLs, text, and reference links
- [ ] T044 [US3] Create `specmetrics/kernel/rules/default_rule_pack.yaml` — built-in rules for User Story, GWT, Requirement statements, Business Rules, Actors, Constraints, Assumptions, Decisions, Glossary Terms with priorities and confidence per research.md section 3
- [ ] T045 [US3] Implement PatternLibrary in `specmetrics/kernel/engine_patterns.py` — __init__ loads rule packs via RulePackLoader, match(observations) iterates rules by priority, returns ExtractedElement list with content-hash IDs per Q1
- [ ] T046 [US3] Implement rule matching logic in PatternLibrary — for each observation, check all rules for pattern match (keyword search or heading match); select highest priority matching rule; generate ExtractedElement with type, confidence, evidence (including rule_id), and content-hash ID
- [ ] T047 [US1] Implement DeterministicSemanticEngine in `specmetrics/kernel/deterministic_engine.py` — extract(documents) iterates documents, parses each with markdown-it-py, runs all visitors in sequence, runs PatternLibrary.match(), produces ExtractionResult
- [ ] T048 [US1] Add document parsing with markdown-it-py in DeterministicSemanticEngine — import markdown_it, create parser instance, parse document content into token stream
- [ ] T049 [US1] Add visitor orchestration in DeterministicSemanticEngine — create ExtractionState per document, call each visitor's visit(tokens, state) in sequence
- [ ] T050 [US2] Add EvidenceReference generation with rule_id in DeterministicSemanticEngine — for each matched element, create EvidenceReference(document_id, section_id from heading stack, source text, rule_id from matching rule)
- [ ] T051 [US2] Add content-hash ID generation — sha256(f"{document_id}::{section_path}::{text}")[:16] per Q1
- [ ] T052 [US2] Add ProcessingStats generation — track documents_processed, elements_extracted, elements_by_type dict, duration_ms via time.monotonic(), errors_count
- [ ] T053 [US1] Add configurable max_heading_depth in DeterministicSemanticEngine — flatten headings beyond configured depth; default 6
- [ ] T054 [US1] Add binary content detection — skip content with high ratio of control characters per existing pattern in extraction_stage.py

**Checkpoint**: Core engine complete — DeterministicSemanticEngine extracts elements, preserves evidence, and produces byte-identical output.

---

## Phase 4: User Story 4 — Extend with Custom Rule Packs (Priority: P2)

**Goal**: A team creates a custom rule pack YAML file with domain-specific patterns. The engine loads it alongside built-in rules, using priority scores for conflict resolution.

**Independent Test**: Create a custom rule pack with a new pattern (e.g., "Security Constraint"), process a document containing that pattern, and verify the output includes the expected element.

### Tests for User Story 4

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T055 [P] [US4] Test: DeterministicSemanticEngine loads extra_rule_packs from config in `tests/unit/test_deterministic_engine.py`
- [ ] T056 [P] [US4] Test: Custom rule with higher priority overrides built-in rule on same content in `tests/unit/test_deterministic_engine.py`
- [ ] T057 [P] [US4] Test: Rule pack loading order respects priority, not load order in `tests/unit/test_engine_patterns.py`
- [ ] T058 [P] [US4] Test: PatternLibrary handles empty rule pack gracefully in `tests/unit/test_engine_patterns.py`

### Implementation for User Story 4

- [ ] T059 [US4] Add extra_rule_packs config support in DeterministicSemanticEngine — constructor accepts extra_rule_packs list, passes to PatternLibrary alongside default_rule_pack
- [ ] T060 [US4] Implement rule pack merge in PatternLibrary — load built-in pack first, then extra packs; merge all rules; priority resolves conflicts per Q2
- [ ] T061 [US4] Add conflict resolution logging — log when multiple rules match same observation and which rule wins; log rule pack loading summary

**Checkpoint**: User Story 4 complete — rule library is extensible with custom packs.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect the entire deterministic engine

- [ ] T062 [P] Add docstrings to all visitor classes in `specmetrics/kernel/engine_visitors.py`
- [ ] T063 [P] Add docstrings to ExtractionRule and RulePackLoader in `specmetrics/kernel/engine_rule.py`
- [ ] T064 [P] Add docstrings to PatternLibrary in `specmetrics/kernel/engine_patterns.py`
- [ ] T065 [P] Add docstrings to DeterministicSemanticEngine in `specmetrics/kernel/deterministic_engine.py`
- [ ] T066 Add framework-specific rule packs — create `rules/openspec_rules.yaml` and `rules/speckit_rules.yaml` for OpenSpec/SpecKit framework detection per FR-007
- [ ] T067 Add framework detection logic in DeterministicSemanticEngine — check document.document_type to load corresponding framework rule packs
- [ ] T068 Run `pytest tests/unit/test_engine_visitors.py` and fix all failures
- [ ] T069 Run `pytest tests/unit/test_engine_rule.py` and fix all failures
- [ ] T070 Run `pytest tests/unit/test_engine_patterns.py` and fix all failures
- [ ] T071 Run `pytest tests/unit/test_deterministic_engine.py` and fix all failures
- [ ] T072 Run `pytest tests/integration/test_deterministic_pipeline.py` and fix all failures
- [ ] T073 Run quickstart.md validation scenarios end-to-end

**Checkpoint**: All tests pass, quickstart validation complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3)**: Depends on Foundational — core engine (US1+US2+US3 combined as one P1 phase)
- **User Story 4 (Phase 4)**: Depends on Phase 3 (needs DeterministicSemanticEngine and PatternLibrary)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1+US2+US3 (P1)**: Can start after Foundational — all three are implemented together in one phase
- **US4 (P2)**: Depends on US1+US3 (needs DeterministicSemanticEngine and PatternLibrary)

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Models/entities before orchestration logic
- Visitor implementations before engine integration
- Core implementation before edge cases
- Phase complete before moving to next

### Parallel Opportunities

- All Setup tasks (T001–T005) can run in parallel
- All Foundational model tasks (T007–T009) can run in parallel
- All visitor implementations (T036–T043) can run in parallel
- All tests within a phase marked [P] can run in parallel
- Polish tasks (T062–T067) can run in parallel

---

## Parallel Example: Phase 3

```bash
# Launch all AST visitor implementations in parallel:
Task: "T036 [P] [US1] Implement HeadingVisitor"
Task: "T037 [P] [US1] Implement ListVisitor"
Task: "T038 [P] [US1] Implement TableVisitor"
Task: "T039 [P] [US1] Implement ParagraphVisitor"
Task: "T040 [P] [US1] Implement CodeBlockVisitor"
Task: "T041 [P] [US1] Implement QuoteVisitor"
Task: "T042 [P] [US1] Implement EmphasisVisitor"
Task: "T043 [P] [US1] Implement LinkVisitor"

# Then integrate:
Task: "T044 [US3] Create default rule pack YAML"
Task: "T045 [US3] Implement PatternLibrary"
Task: "T047 [US1] Implement DeterministicSemanticEngine"
```

---

## Implementation Strategy

### MVP First (Phase 3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1+US2+US3 (Core Deterministic Engine)
4. **STOP and VALIDATE**: Test with `pytest tests/unit/test_deterministic_engine.py`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Phase 3 (Core engine) → Test independently → Demo (MVP! Offline extraction)
3. Add Phase 4 (Custom rule packs) → Test independently → Demo (Extensible rules)
4. Add Phase 5 (Polish) → Framework support, documentation, full validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Visitor implementations (T036–T043)
   - Developer B: Rule engine + PatternLibrary (T044–T046)
   - Developer C: DeterministicSemanticEngine integration (T047–T054)
3. After Phase 3 completes:
   - Developer A: Custom rule packs (Phase 4)
   - Developer B: Framework rule packs + Polish (Phase 5)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
