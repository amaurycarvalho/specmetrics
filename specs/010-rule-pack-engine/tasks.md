---

description: "Task list for Rule Pack Engine implementation"

---

# Tasks: Rule Pack Engine

**Input**: Design documents from `specs/010-rule-pack-engine/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL — only include if explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/tests/` at repository root

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create plugin directory structure and package boilerplate

- [x] T001 Create `specmetrics/plugins/rule_pack/` package with `__init__.py`
- [x] T002 Create `tests/plugins/rule_pack/` test package with `__init__.py`
- [x] T003 [P] Create sample Rule Pack YAML files at `.specify/rules/` for development and testing
- [x] T004 Register `RulePackEnginePlugin` entry point in `pyproject.toml` under `specmetrics.plugins.rule_pack`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared RulePack model extraction and plugin skeleton

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Extract shared `RulePack` Pydantic model from `specmetrics/plugins/measurement/apf/models.py` to new `specmetrics/kernel/cfm/models.py` with added fields: `rules: list[Rule]`, `glossary_overrides: dict[str, str]`
- [x] T006 Create `Rule` model with `type` (literal: exclusion, complexity_override, weight_override, vaf, element_exclusion), `id`, `description`, and `config` fields in `specmetrics/kernel/cfm/models.py`
- [x] T007 Create `AppliedRuleRecord` Pydantic model with `rule_pack_id`, `rule_id`, `rule_type`, `description`, `before_state`, `after_state` fields in `specmetrics/kernel/cfm/models.py`
- [x] T008 Create `RuleValidationReport` Pydantic model with `loaded_files`, `total_rules`, `active_rules`, `errors`, `warnings` fields in `specmetrics/kernel/cfm/models.py`
- [x] T009 Create `RulePackEnginePlugin` skeleton in `specmetrics/plugins/rule_pack/plugin.py` implementing `EventHandler` protocol with `handled_event_type = EventType.RULE_PACK_APPLIED`, `handler_id = "rule_pack_engine"`, `stage_name = "Rule Pack Engine"`
- [x] T010 Register the engine plugin via `HandlerRegistry` in the existing plugin discovery chain (verify `EventType.RULE_PACK_APPLIED` is resolved)

**Checkpoint**: Foundation ready — RulePack model is shared, plugin skeleton registers in the pipeline

---

## Phase 3: User Story 1 — Define and Load Rule Packs (Priority: P1) 🎯 MVP

**Goal**: Team leads author YAML Rule Pack files; the engine discovers, loads, and validates them

**Independent Test**: Create a `.specify/rules/test.yml` with 3 rules, run the pipeline, verify engine logs all 3 as active

### Implementation for User Story 1

- [x] T011 [P] [US1] Implement `RulePackLoader` in `specmetrics/plugins/rule_pack/loader.py` — discover `.yml` files in `.specify/rules/`, parse via `ruamel.yaml`, return list of `RulePack` objects sorted alphabetically by filename
- [x] T012 [P] [US1] Implement `RulePackValidator` in `specmetrics/plugins/rule_pack/validator.py` — validate RulePack `id` format, rule `type` enum, rule `config` structure per type; return `RuleValidationReport` with errors and warnings
- [x] T013 [US1] Wire loader and validator into `RulePackEnginePlugin.handle()` in `specmetrics/plugins/rule_pack/plugin.py` — on `RULE_PACK_APPLIED` event, load and validate all Rule Packs, store validated packs in context metadata
- [x] T014 [US1] Implement graceful no-op behavior in `specmetrics/plugins/rule_pack/plugin.py` — when `.specify/rules/` is empty or absent, pass CFM through unmodified with no active rules
- [x] T015 [US1] Implement error handling in `specmetrics/plugins/rule_pack/plugin.py` — invalid YAML files produce descriptive error messages (file path, line number, issue) without crashing the pipeline

**Checkpoint**: Rule Pack files are discovered, parsed, validated, and made available to the pipeline. Empty rules directory produces no-op.

---

## Phase 4: User Story 2 — Apply Counting Rule Exclusions (Priority: P1) 🎯 MVP

**Goal**: Quality engineers define exclusion rules; engine marks matching functions as excluded from counting

**Independent Test**: Provide CFM with 5 EQs and a Rule Pack with `exclude: [EQ]`, verify output CFM marks all 5 EQs as excluded

### Implementation for User Story 2

- [x] T016 [P] [US2] Implement core `RuleApplicator` in `specmetrics/plugins/rule_pack/applicator.py` — iterate over CFM `functional_processes`, apply exclusion rules by `function_type` (ILF, EIF, EI, EO, EQ), return mapping of affected element IDs to exclusion status
- [x] T017 [P] [US2] Implement element-level exclusion in `specmetrics/plugins/rule_pack/applicator.py` — support `element_exclusion` rule type that excludes specific CFM element IDs regardless of function type
- [x] T018 [US2] Implement VAF computation in `specmetrics/plugins/rule_pack/applicator.py` — parse GSC ratings from `vaf` rules, compute VAF = 0.65 + 0.01 * sum(GSC), store computed VAF in CFM metadata
- [x] T019 [US2] Wire applicator into `RulePackEnginePlugin.handle()` in `specmetrics/plugins/rule_pack/plugin.py` — apply validated Rule Packs to CFM, update context with applied exclusions
- [x] T020 [US2] Handle conflicting exclusion rules across multiple Rule Packs in `specmetrics/plugins/rule_pack/plugin.py` — log warning on conflict, last-loaded file takes precedence

**Checkpoint**: Exclusion rules are applied to CFM functions. VAF is computed from GSC ratings. Conflicting rules log warnings.

---

## Phase 5: User Story 3 — Custom Complexity Thresholds (Priority: P2)

**Goal**: Team leads adjust DET/RET/FTR thresholds for complexity classification

**Independent Test**: Provide CFM with EI at standard complexity thresholds plus a Rule Pack with lowered thresholds, verify output reflects custom classification

### Implementation for User Story 3

- [x] T021 [P] [US3] Implement complexity override logic in `specmetrics/plugins/rule_pack/applicator.py` — parse `complexity_override` rules, override DET/RET (data functions) and DET/FTR (transactional functions) thresholds for specified function types
- [x] T022 [P] [US3] Implement weight override logic in `specmetrics/plugins/rule_pack/applicator.py` — parse `weight_override` rules, override UFP weight for specified (function_type, complexity) combinations
- [x] T023 [US3] Wire complexity and weight overrides into the applicator application sequence in `specmetrics/plugins/rule_pack/applicator.py` — enforce order: exclusions → complexity overrides → weight overrides → VAF
- [x] T024 [US3] Validate threshold values in `specmetrics/plugins/rule_pack/validator.py` — reject negative DET/RET/FTR, enforce first threshold < second, reject unknown function types

**Checkpoint**: Complexity and weight overrides are applied in correct order alongside exclusion rules.

---

## Phase 6: User Story 4 — Trace Applied Rules (Priority: P2)

**Goal**: Quality engineers inspect which rules affected each function

**Independent Test**: Apply a Rule Pack that excludes EQs, verify each excluded function in output has an `AppliedRuleRecord` referencing the specific rule

### Implementation for User Story 4

- [x] T025 [P] [US4] Implement `RuleAnnotator` in `specmetrics/plugins/rule_pack/annotator.py` — create `AppliedRuleRecord` for each applied rule action, capturing `rule_pack_id`, `rule_id`, `rule_type`, `before_state` (pre-application values), and `after_state` (post-application values)
- [x] T026 [P] [US4] Wire annotator into applicator in `specmetrics/plugins/rule_pack/applicator.py` — every exclusion, override, and VAF computation produces an `AppliedRuleRecord`
- [x] T027 [US4] Implement glossary override support in `specmetrics/plugins/rule_pack/applicator.py` — parse `glossary_overrides` from Rule Pack, apply custom labels to function type and complexity names in annotations
- [x] T028 [US4] Store all `AppliedRuleRecord` instances in CFM metadata under `applied_rules` key in `specmetrics/plugins/rule_pack/plugin.py` — downstream consumers (Measurement Engine) read annotations from CFM metadata
- [x] T029 [US4] Add "default rules applied" annotation in `specmetrics/plugins/rule_pack/plugin.py` — when no Rule Pack is loaded, annotate CFM with a note that default IFPUG rules were used

**Checkpoint**: Every applied rule has a traceable record. Glossary overrides customize report labels. Empty rules produce default annotation.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Integration testing, documentation, and quickstart validation

- [x] T030 [P] Add structlog logging throughout `specmetrics/plugins/rule_pack/` — log file discovery, rule counts, validation results, applied rules, and conflicts at appropriate levels (info for normal ops, warning for conflicts, error for invalid files)
- [x] T031 [P] Register `RulePackEnginePlugin` with the Kernel Pipeline Engine's `CANONICAL_EVENT_ORDER` — ensure the pipeline iterates through `RULE_PACK_APPLIED` between `CANONICAL_MODEL_BUILT` and `MEASUREMENT_COMPLETED`
- [x] T032 Implement full integration test in `tests/plugins/rule_pack/test_plugin.py` — create `PipelineContext` with a known CFM, run `RulePackEnginePlugin.handle()`, verify annotated CFM output
- [x] T033 Implement loading edge case tests in `tests/plugins/rule_pack/test_loader.py` — empty directory, missing directory, mixed valid/invalid files, alphabetical ordering
- [x] T034 Implement validator tests in `tests/plugins/rule_pack/test_validator.py` — invalid YAML, duplicate rule IDs, unknown function types, invalid thresholds, missing required fields
- [x] T035 Implement applicator tests in `tests/plugins/rule_pack/test_applicator.py` — exclusion, complexity override, weight override, VAF computation, element exclusion, conflicting rules, empty Rule Pack
- [x] T036 Validate all 5 quickstart scenarios from `specs/010-rule-pack-engine/quickstart.md` run successfully
- [x] T037 Update `pyproject.toml` entry points with final `RulePackEnginePlugin` path if it moved during implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - US3 (Phase 5) logically builds on US2's applicator infrastructure
  - US4 (Phase 6) integrates into all prior phases' applicator work
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (P1)**: Can start after Foundational — Loader must be available but can use mock RulePacks for parallel development
- **US3 (P2)**: Requires US2's applicator infrastructure (applicator.py)
- **US4 (P2)**: Integrates into all prior phases' work (annotator wires into applicator)

### Within Each User Story

- Models before logic
- Logic before integration with plugin.py
- Core implementation before edge case handling

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- US1 and US2 can be developed in parallel (different files — loader vs applicator)
- US4 annotator can start independently of US3
- All test tasks in Polish phase marked [P] can run in parallel

---

## Parallel Examples

### Phase 1: Setup

```bash
# Create package structure in parallel:
Task: "Create specmetrics/plugins/rule_pack/__init__.py"
Task: "Create tests/plugins/rule_pack/__init__.py"
Task: "Create sample Rule Pack YAML files at .specify/rules/"
```

### Phase 2: Foundational

```bash
# Create models in parallel:
Task: "Create RulePack model in specmetrics/kernel/cfm/models.py"
Task: "Create Rule model in specmetrics/kernel/cfm/models.py"
Task: "Create AppliedRuleRecord model in specmetrics/kernel/cfm/models.py"
Task: "Create RuleValidationReport model in specmetrics/kernel/cfm/models.py"
```

### User Stories 1 & 2 (parallel development)

```bash
# Developer A — US1:
Task: "Implement RulePackLoader in specmetrics/plugins/rule_pack/loader.py"
Task: "Implement RulePackValidator in specmetrics/plugins/rule_pack/validator.py"

# Developer B — US2:
Task: "Implement core RuleApplicator in specmetrics/plugins/rule_pack/applicator.py"
Task: "Implement element-level exclusion in specmetrics/plugins/rule_pack/applicator.py"
Task: "Implement VAF computation in specmetrics/plugins/rule_pack/applicator.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 — loader + validator (Rule Pack discovery and parsing)
4. Complete Phase 4: US2 — applicator (exclusions + VAF)
5. **STOP and VALIDATE**: Create a test Rule Pack with exclusions, run pipeline, verify annotations
6. MVP is ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US2 → Test independently → Deploy/Demo (MVP — load exclusions and apply them)
3. Add US3 → Test independently → Deploy/Demo (add complexity overrides)
4. Add US4 → Test independently → Deploy/Demo (full traceability)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (loader + validator)
   - Developer B: US2 (applicator + exclusions)
3. After US1 + US2:
   - Developer A: US3 (complexity overrides)
   - Developer B: US4 (annotator)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
