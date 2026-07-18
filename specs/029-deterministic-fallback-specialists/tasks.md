---

description: "Task list for Specialized Deterministic Fallbacks"

---

# Tasks: Specialized Deterministic Fallbacks

**Input**: Design documents from `specs/029-deterministic-fallback-specialists/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The feature specification defines Independent Test criteria per user story. Test fixtures and e2e validation scenarios are included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/tests/` at repository root
- **Rule packs**: `specmetrics/kernel/rules/`
- **Test fixtures**: `tests/fixtures/speckit/`, `tests/openspec/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project structure for specialist rule packs

- [ ] T001 Create `speckit_rules.yaml` skeleton with version metadata field in `specmetrics/kernel/rules/speckit_rules.yaml`
- [ ] T002 [P] Create `openspec_rules.yaml` skeleton with version metadata field in `specmetrics/kernel/rules/openspec_rules.yaml`
- [ ] T003 [P] Create Speckit test fixtures directory structure under `tests/fixtures/speckit/` with minimal `spec.md`, `plan.md`, `tasks.md`
- [ ] T004 [P] Verify `tests/openspec/` exists with FlowSource OpenSpec examples (29 domains, 3 active changes, 38 archived changes)

**Checkpoint**: Skeleton rule packs and test fixtures ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rule pack loading, versioning, and engine integration — MUST complete before any user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Update `DeterministicSemanticEngine._load_framework_packs()` in `specmetrics/kernel/deterministic_engine.py` to discover and load `speckit_rules.yaml` and `openspec_rules.yaml` from `specmetrics/kernel/rules/`
- [ ] T006 [P] Implement version metadata parsing: extract `version` field from rule pack YAML, validate semver format (`\d+.\d+.\d+`)
- [ ] T007 Implement version compatibility check: emit WARN log when major version of rule pack mismatches engine compatibility range
- [ ] T008 [P] Add `ExtractionRule` schema support for `capture_groups` and `target_sections` fields in `specmetrics/kernel/models/rule.py`
- [ ] T009 [P] Implement per-rule failure isolation in `DeterministicSemanticEngine._execute_rules()` — catch regex exceptions, log rule_id and error, skip failing rule, continue processing remaining rules (FR-035)
- [ ] T010 [P] Add per-document `ExtractionResult` accumulator tracking `rules_attempted`, `rules_succeeded`, `rules_failed`, `duration_ms` in `specmetrics/kernel/deterministic_engine.py`
- [ ] T011 Implement extraction success rate metric: log WARN when per-document rate < 99%, exposing failing rule IDs (FR-037)
- [ ] T012 [P] Write unit tests for rule pack loading and version checking in `tests/unit/kernel/rules/test_rule_pack_loading.py`

**Checkpoint**: Foundation ready — specialist rule packs can be loaded, validated, and executed with failure isolation and observability

---

## Phase 3: User Story 1 - Speckit specialist fallback extracts full semantic model from feature specs (Priority: P1) 🎯 MVP

**Goal**: `specmetrics measure` on a SpecKit repository uses speckit-specific regex rules to populate CFM and CSM without LLM

**Independent Test**: Run `specmetrics measure --engine deterministic --repo ./specs/` on specmetrics itself (29 features). CFM has non-empty actors, functional_processes, business_rules, data_groups. CSM has non-empty decisions, assumptions, constraints, acceptance_criteria.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create User Story extraction rule (FR-002): match `^### User Story (\d+) [—–-] (.+) \(Priority: (P[1-3])\)` → CFM functional process in `specmetrics/kernel/rules/speckit_rules.yaml`
- [ ] T014 [P] [US1] Create priority justification rule (FR-003): match `^\*\*Why this priority\*\*: (.+)$` → business rule fact in `speckit_rules.yaml`
- [ ] T015 [P] [US1] Create inline GIVEN/WHEN/THEN rule (FR-004): match `^(\d+)\. \*\*Given\*\* (.+), \*\*When\*\* (.+), \*\*Then\*\* (.+)$` → precondition, operation, assertion facts in `speckit_rules.yaml`
- [ ] T016 [P] [US1] Create multi-line GIVEN/WHEN/THEN rule (FR-005): match `^-\s+\*\*Given\*\* (.+)$` / `\*\*When\*\*` / `\*\*Then\*\*` / `\*\*And\*\*` → facts in `speckit_rules.yaml`
- [ ] T017 [P] [US1] Create FR-NNN requirement rule (FR-006): match `^-\s+\*\*FR-(\d{3})\*\*: (.+)$` → business rule with ID reference in `speckit_rules.yaml`
- [ ] T018 [P] [US1] Create SC-NNN success criteria rule (FR-007): match `^-\s+\*\*SC-(\d{3})\*\*: (.+)$` → acceptance criterion in `speckit_rules.yaml`
- [ ] T019 [P] [US1] Create Key Entities extraction rule (FR-008): match `^-\s+\*\*(.+)\*\*: (.+)$` under `### Key Entities` → entity/actor/data group in `speckit_rules.yaml`
- [ ] T020 [P] [US1] Create Assumptions rule (FR-009): match `^-\s+(.+)$` under `## Assumptions` → CSM assumption in `speckit_rules.yaml`
- [ ] T021 [P] [US1] Create Constitution Check rule (FR-010): match `^\*\*Engaged Principles\*\*: (.+)$` → CSM constraint in `speckit_rules.yaml`
- [ ] T022 [P] [US1] Create Edge Cases rule (FR-011): match `^-\s+What happens (.+)\? (.+)$` under `### Edge Cases` → open question in `speckit_rules.yaml`
- [ ] T023 [P] [US1] Create IMP-NNN implementation note rule (FR-012): match `^-\s+\*\*IMP-\d+\*\*: (.+)$` → CSM decision element in `speckit_rules.yaml`
- [ ] T024 [P] [US1] Create task line rule (FR-013): match `^-\s+\[([ xX])\]\s+(T\d{3})...` in `tasks.md` → CSM specification activity in `speckit_rules.yaml`
- [ ] T025 [P] [US1] Create Actor extraction from entity definitions rule (FR-001): match `^-\s+\*\*(.+)\*\*: (.+)$` under `### Key Entities` with uppercase role-like word → Actor in `speckit_rules.yaml`
- [ ] T026 [US1] Verify speckit rules against `specs/007-canonical-functional-model/spec.md` produce ≥ 20 elements (SC-005 target)
- [ ] T027 [US1] Verify speckit rules against all 29 specmetrics specs produce non-empty CFM (≥10 elements) and CSM (≥5 elements) (SC-001 target)

**Checkpoint**: At this point, User Story 1 should be fully functional — Speckit extraction produces rich CFM/CSM from specmetrics itself

---

## Phase 4: User Story 2 - OpenSpec specialist extracts CFM/CSM from OpenSpec master specs, change proposals, designs, and delta specs (Priority: P1)

**Goal**: `specmetrics measure --repo tests/openspec/` produces CFM and CSM from all FlowSource OpenSpec document types using openspec-specific regex rules

**Independent Test**: Run `specmetrics measure --repo tests/openspec/ --engine deterministic --stage extract`. Production of at least 40 elements from master specs, 15 from proposals, 10 from designs, 20 from delta specs — all without any LLM.

### Implementation for User Story 2

- [ ] T028 [P] [US2] Create Requirement heading rule (FR-014): match `### Requirement: <Title> (<optional-ID>)` → fact + data group reference in `specmetrics/kernel/rules/openspec_rules.yaml`
- [ ] T029 [P] [US2] Create Portuguese DEVE statement rule (FR-015): match `O sistema DEVE <action>`, `NÃO DEVE`, `<Entity> DEVE`, `<Entity> DEVEM` → business rule fact in `openspec_rules.yaml`
- [ ] T030 [P] [US2] Create English SHALL statement rule (FR-016): match `The system SHALL`, `SHALL NOT`, `<Component> SHALL`, `SHOULD`, `MAY` → fact in `openspec_rules.yaml`
- [ ] T031 [P] [US2] Create Scenario heading rule (FR-017): match `#### Scenario: <title>` → operation element in `openspec_rules.yaml`
- [ ] T032 [P] [US2] Create GIVEN precondition rule (FR-018): match `- **GIVEN** <condition>` + `- **AND** <condition>` following GIVEN → precondition fact in `openspec_rules.yaml`
- [ ] T033 [P] [US2] Create WHEN operation trigger rule (FR-019): match `- **WHEN** <action>` → operation trigger, including variable assignments and user actions in `openspec_rules.yaml`
- [ ] T034 [P] [US2] Create THEN assertion rule (FR-020): match `- **THEN** <expected>` → business rule assertion, preserving full formula in `openspec_rules.yaml`
- [ ] T035 [P] [US2] Create capability ID rule (FR-021): match `FS###`, `DC###`, `DR###`, `DT###`, `DP###`, `IC###`, `LC###`, `REQ-*` → data group reference in `openspec_rules.yaml`
- [ ] T036 [P] [US2] Create Decision record rule (FR-022): match `### Decision <N>: <Title>` (colon) and `### <N>. <Title>` (dot) headings in `design.md` → CSM Decision with rationale, alternatives in `openspec_rules.yaml`
- [ ] T037 [P] [US2] Create Risk/Trade-off rule (FR-023): match `- [Risk] <desc> → Mitigation: <action>` and `- [Trade-off] <desc> → Acceptable because <reason>` → CSM Risk in `openspec_rules.yaml`
- [ ] T038 [P] [US2] Create Why/What Changes/Context/Goals rule (FR-024): extract `## Why`, `## What Changes`, `## Context`, `## Goals / Non-Goals` from `proposal.md` and `design.md` → CSM assumptions and constraints in `openspec_rules.yaml`
- [ ] T039 [P] [US2] Create Capabilities rule (FR-025): match `### New Capabilities` and `### Modified Capabilities` from `proposal.md` → functional processes / decision elements in `openspec_rules.yaml`
- [ ] T040 [P] [US2] Create task checklist rule (FR-026): match `## <N>. <Category>` headings and `- [ ] <N.N>` / `- [x] <N.N>` from `tasks.md` → CSM specification activities in `openspec_rules.yaml`
- [ ] T041 [P] [US2] Create domain entity rule (FR-027): match TitleCase entity names from known catalog (TradeDay, Diagnosis, etc.) → data group in `openspec_rules.yaml`
- [ ] T042 [P] [US2] Create Purpose section rule (FR-028): extract `## Purpose` from master specs → functional process in `openspec_rules.yaml`
- [ ] T043 [P] [US2] Create inline actor reference rule (FR-029): match Portuguese role nouns (Usuário, Sistema, Cliente, Analista, Operador) and English equivalents → Actor in `openspec_rules.yaml`
- [ ] T044 [P] [US2] Create delta spec detection rules: distinguish `## ADDED Requirements` (CFM elements) vs `## MODIFIED Requirements` (CSM decisions), detect `(substitui "...")` markers in flat `.spec.delta.md` format in `openspec_rules.yaml`
- [ ] T045 [P] [US2] Create no-change spec detection: skip `specs/spec.md`, `_index.md`, `README.md` containing `"No specification changes required"` to avoid false positives in `openspec_rules.yaml`
- [ ] T046 [US2] Verify openspec rules against `tests/openspec/specs/ticker-analysis/spec.md` produce ≥ 25 elements (SC-006 target)
- [ ] T047 [US2] Verify openspec rules against `tests/openspec/changes/diagnosis-panel/design.md` produce ≥ 3 decisions (SC-007 target)
- [ ] T048 [US2] Verify openspec rules against all 29 master specs in `tests/openspec/specs/` produce ≥ 60 elements (SC-008 target)

**Checkpoint**: Both Speckit and OpenSpec specialist extraction are functional

---

## Phase 5: User Story 3 - Regex-based extraction rules cover all CFM and CSM entity types (Priority: P1)

**Goal**: All 14 entity categories across CFM (actors, functional_processes, business_rules, data_groups, operations, relationships) and CSM (decisions, assumptions, constraints, risks, open_questions, acceptance_criteria, glossary_terms, specification_activities) contain at least one element

**Independent Test**: Run deterministic pipeline on a spec that explicitly contains content for all categories and verify every CFM and CSM category has at least one element.

### Implementation for User Story 3

- [ ] T049 [P] [US3] Verify content-hash ID generation (FR-031): confirm both rule packs produce deterministic IDs via `sha256(f"{document_id}::{section_id}::{text}")[:16]` in `specmetrics/kernel/deterministic_engine.py`
- [ ] T050 [P] [US3] Verify confidence score assignment (FR-030): confirm both rule packs use scores per the RFC table (explicit heading=1.00, convention=0.95, heuristic=0.85, inference=0.70)
- [ ] T051 [US3] Create cross-spec validation script in `tests/unit/kernel/rules/test_entity_coverage.py` that verifies all 14 CFM/CSM categories produce at least one element on a representative document set
- [ ] T052 [US3] Validate minimal spec handling: run on a spec with only title and description — confirm pipeline does not fail and empty collections are returned gracefully

**Checkpoint**: All entity categories covered, deterministic IDs and confidence scores verified

---

## Phase 6: User Story 4 - Framework-specific rule packs replace current minimal versions (Priority: P2)

**Goal**: New specialist rule packs contain richer patterns than current minimal versions, producing more elements and more varied types

**Independent Test**: Compare element count and type diversity between old and new rule packs on the same document set — new pack produces more elements and more varied types.

### Implementation for User Story 4

- [ ] T053 [P] [US4] Remove minimal heading-only rules from current `openspec_rules.yaml` in `specmetrics/kernel/rules/openspec_rules.yaml` — replace with full specialist content
- [ ] T054 [P] [US4] Remove minimal heading-only rules from current `speckit_rules.yaml` in `specmetrics/kernel/rules/speckit_rules.yaml` — replace with full specialist content
- [ ] T055 [US4] Run comparison validation: process a SpecKit spec with old vs new speckit rules — new pack produces ≥ 10 elements vs ≤ 3 with old (US4 acceptance scenario 1)
- [ ] T056 [US4] Run comparison validation: process an OpenSpec spec with old vs new openspec rules — new pack produces ≥ 8 elements vs ≤ 4 with old (US4 acceptance scenario 2)

**Checkpoint**: Specialist rule packs fully replace minimal versions with measurable improvement

---

## Phase 7: Cross-Cutting Concerns & Observability

**Purpose**: Non-functional requirements that span all user stories

- [ ] T057 [P] Add semver version metadata to `speckit_rules.yaml` with initial version `1.0.0`
- [ ] T058 [P] Add semver version metadata to `openspec_rules.yaml` with initial version `1.0.0`
- [ ] T059 Run full e2e validation: `specmetrics measure --engine deterministic --repo ./specs/` on specmetrics (29 features) — verify all 8 plugins produce non-zero output (SC-003)
- [ ] T060 Run e2e on `tests/openspec/`: `specmetrics measure --repo tests/openspec/ --engine deterministic` — verify ≤ 30s end-to-end (SC-002)
- [ ] T061 Verify byte-identical re-execution (SC-004): run twice, compare output excluding `duration_ms`
- [ ] T062 Generate rule pack documentation from YAML schemas in `docs/rules/`

**Checkpoint**: All cross-cutting requirements verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational completion — no US2 dependency
- **US2 (Phase 4)**: Depends on Foundational completion — no US1 dependency
- **US3 (Phase 5)**: Depends on US1 and US2 completion (validates cross-entity coverage)
- **US4 (Phase 6)**: Depends on US1 and US2 completion (replaces minimal packs with rich ones)
- **Cross-Cutting (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational — No dependencies on US1 (independent implementation)
- **User Story 3 (P1)**: Depends on US1 and US2 (validates their combined output)
- **User Story 4 (P2)**: Depends on US1 and US2 (replaces their minimal predecessors)

### Within Each User Story

- Rules before verification tests
- Core extraction patterns before edge-case patterns
- Master spec rules before change artifact rules
- Implementation complete before acceptance scenario validation

### Parallel Opportunities

- All Phase 1 Setup tasks marked [P] can run in parallel
- All Phase 2 Foundational tasks marked [P] can run in parallel
- US1 and US2 can run in FULL PARALLEL after Foundational — Speckit and OpenSpec rule packs are independent
- All FR rules within a story marked [P] can run in parallel (different regex patterns, same file)
- US3 and US4 require US1+US2 to be complete

---

## Parallel Example: User Story 1

```bash
# Launch all Speckit extraction rules in parallel (different regex patterns):
Task: "Create User Story extraction rule in speckit_rules.yaml"
Task: "Create FR-NNN requirement rule in speckit_rules.yaml"
Task: "Create SC-NNN success criteria rule in speckit_rules.yaml"
Task: "Create Key Entities extraction rule in speckit_rules.yaml"
Task: "Create Assumptions rule in speckit_rules.yaml"
```

## Parallel Example: User Story 2

```bash
# Launch all OpenSpec extraction rules in parallel:
Task: "Create Portuguese DEVE statement rule in openspec_rules.yaml"
Task: "Create English SHALL statement rule in openspec_rules.yaml"
Task: "Create Decision record rule in openspec_rules.yaml"
Task: "Create Risk/Trade-off rule in openspec_rules.yaml"
Task: "Create Scenario/GIVEN/WHEN/THEN rules in openspec_rules.yaml"
```

## Parallel Strategy: US1 + US2

```bash
# Team A works on Speckit (US1), Team B works on OpenSpec (US2) simultaneously:
# After Phase 2 completes:

# Developer/Team A:
Task: "Create all Speckit extraction rules in speckit_rules.yaml"
Task: "Verify against specmetrics/features"

# Developer/Team B:
Task: "Create all OpenSpec extraction rules in openspec_rules.yaml"
Task: "Verify against tests/openspec/ examples"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Speckit specialist)
4. **STOP and VALIDATE**: Run `specmetrics measure --engine deterministic --repo ./specs/` on specmetrics — CFM/CSM should be non-empty
5. Deploy/demo if ready — Speckit support delivers the primary e2e testing mechanism

### Incremental Delivery

1. Setup + Foundational → Engine can load versioned rule packs with failure isolation
2. Add US1 (Speckit) → Test on specmetrics itself → Deploy/Demo (MVP!)
3. Add US2 (OpenSpec) → Test on `tests/openspec/` → Deploy/Demo
4. Add US3 (Full coverage) → Validate all 14 entity categories → Deploy/Demo
5. Add US4 (Replace minimal) → Comparison validation → Deploy/Demo
6. Cross-cutting → Observability, documentation, e2e timing verification

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together
2. Once Foundational is done:
   - Developer A: Phase 3 (US1 — Speckit rules)
   - Developer B: Phase 4 (US2 — OpenSpec rules)
3. US1 and US2 complete completely independently (different rule pack files)
4. Developers reunite for Phase 5 (US3 — cross-entity coverage validation)
5. Final Phase: cross-cutting concerns

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Speckit and OpenSpec rule packs are independent — can be built in parallel
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
