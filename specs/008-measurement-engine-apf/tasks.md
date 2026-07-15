# Tasks: Measurement Engine Plugin — APF

**Input**: Design documents from `specs/008-measurement-engine-apf/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to verify deterministic behavior and contract compliance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/measurement/apf/`, `tests/` at repository root
- Paths below follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the APF measurement plugin.

- [x] T001 Create `specmetrics/plugins/measurement/` package with `__init__.py`
- [x] T002 Create `specmetrics/plugins/measurement/apf/` package with `__init__.py`
- [x] T003 [P] Create `tests/unit/measurement/apf/` directory structure
- [x] T004 [P] Create `tests/integration/measurement/apf/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, complexity matrix tables, and plugin protocol that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 [P] Define APF measurement Pydantic models in `specmetrics/plugins/measurement/apf/models.py` — `APFMeasurementResult`, `MeasuredFunction`, `MeasurementSummary`, `MeasurementExplanation`, `MeasurementWarning`, `MeasurementError`, `EvidenceRef`, `FunctionType` (Literal), `ComplexityRating` (Literal), `TypeBreakdown`, `ComplexityDistributionRow` per `data-model.md`
- [x] T006 [P] Implement IFPUG CPM 4.3 complexity matrix tables for all five function types in `specmetrics/plugins/measurement/apf/complexity.py` — including data function matrix (ILF/EIF: RETs × DETs), transactional matrices (EI: FTRs × DETs, EO/EQ: FTRs × DETs), and UFP weight table (ILF=7/10/15, EIF=5/7/10, EI=3/4/6, EO=4/5/7, EQ=3/4/6)
- [x] T007 [P] Implement `MeasurementPlugin` Protocol class in `specmetrics/plugins/measurement/apf/plugin.py` with `plugin_id()`, `supported_methodology()`, `supported_function_types()`, and `measure(cfm, rule_pack)` methods per contract in `contracts/measurement-plugin-interface.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Automated APF Measurement (Priority: P1) 🎯 MVP

**Goal**: A quality engineer can run `specmetrics measure` and receive a complete APF function point count (ILF, EIF, EI, EO, EQ) automatically from the Canonical Functional Model.

**Independent Test**: Provide a known CFM with identifiable data groups and operations; verify the measurement output contains correct function type counts, complexity ratings, and total UFP matching expected IFPUG values.

### Tests for User Story 1

- [x] T008 [P] [US1] Unit test for DataGroup-to-ILF/EIF classification in `tests/unit/measurement/apf/test_counter.py`
- [x] T009 [P] [US1] Unit test for Operation-to-EI/EO/EQ classification in `tests/unit/measurement/apf/test_counter.py`
- [x] T010 [P] [US1] Unit test for complexity matrix lookups (all 5 function types × 3 complexity levels) in `tests/unit/measurement/apf/test_complexity.py`
- [x] T011 [P] [US1] Unit test for empty CFM returning zero count in `tests/unit/measurement/apf/test_counter.py`

### Implementation for User Story 1

- [x] T012 [US1] Implement `APFCounter` class in `specmetrics/plugins/measurement/apf/counter.py` — scans CFM DataGroups (data_type: internal→ILF, external→EIF, shared→ILF) and Operations (requires direction metadata: input→EI, output→EO, query→EQ); derives DET count from metadata or relationships; delegates complexity to `complexity.py`
- [x] T013 [US1] Wire basic measurement flow in `specmetrics/plugins/measurement/apf/plugin.py` — `measure()` method creates `APFCounter`, invokes it against the CFM, populates `APFMeasurementResult` with `MeasuredFunction` entries and `MeasurementSummary`, returns the result
- [x] T014 [US1] Handle edge cases in `specmetrics/plugins/measurement/apf/counter.py` — zero-count result for empty CFM; unresolvable references produce warnings
- [x] T015 [US1] Integration test: full measurement pipeline with a synthetic CFM in `tests/integration/measurement/apf/test_full_measurement.py`

**Checkpoint**: US1 complete — basic APF measurement works end-to-end with default IFPUG rules.

---

## Phase 4: User Story 2 — Explainable Measurement Results (Priority: P1)

**Goal**: Every measured function preserves evidence references to originating CFM elements, and users can inspect a full explanation for each function.

**Independent Test**: Measure a known CFM and verify every `MeasuredFunction` in the output has non-empty evidence references. Request the explanation for any function and verify it includes classification reason, complexity reason, and evidence chain.

### Tests for User Story 2

- [x] T016 [P] [US2] Unit test for evidence trail preservation in `tests/unit/measurement/apf/test_counter.py` — verify each MeasuredFunction.evidence_refs contains the originating CFM element's evidence

### Implementation for User Story 2

- [x] T017 [P] [US2] Implement `MeasurementExplainer` class in `specmetrics/plugins/measurement/apf/explainer.py` — builds `MeasurementExplanation` for each `MeasuredFunction` with `classification_reason`, `complexity_reason`, `rule_exceptions`, and `evidence_chain` tracing: spec section → evidence graph → CFM element → measured function
- [x] T018 [US2] Integrate explainer into `plugin.py` — after counter runs, invoke `MeasurementExplainer` to populate `APFMeasurementResult.explanations`
- [x] T019 [US2] Integrate evidence reference propagation into `counter.py` — each `MeasuredFunction` copies `EvidenceRef` from the originating CFM element's `.evidence` field
- [x] T020 [US2] Integration test: verify evidence trail completeness in `tests/integration/measurement/apf/test_full_measurement.py`

**Checkpoint**: US2 complete — all measured functions are explainable with evidence trails.

---

## Phase 5: User Story 3 — Rule Pack Integration (Priority: P1)

**Goal**: Organizational Rule Packs can override default IFPUG counting rules — custom complexity thresholds, weight tables, function type exclusions, and VAF adjustments — without modifying the engine or the CFM.

**Independent Test**: Apply a Rule Pack that excludes External Inquiries; the resulting count must be lower by exactly the number of EQs identified. Apply a Rule Pack with overridden complexity thresholds; the complexity ratings must reflect the custom thresholds.

### Tests for User Story 3

- [x] T021 [P] [US3] Unit test for Rule Pack parsing and default fallback in `tests/unit/measurement/apf/test_rule_applicator.py`
- [x] T022 [P] [US3] Unit test for function type exclusion in `tests/unit/measurement/apf/test_rule_applicator.py`
- [x] T023 [P] [US3] Unit test for complexity threshold override in `tests/unit/measurement/apf/test_rule_applicator.py`
- [x] T024 [P] [US3] Unit test for weight table override in `tests/unit/measurement/apf/test_rule_applicator.py`

### Implementation for User Story 3

- [x] T025 [P] [US3] Implement `RulePack` Pydantic model in `specmetrics/plugins/measurement/apf/models.py` — fields for `complexity_overrides`, `weight_overrides`, `excluded_types`, `element_exclusions`, `vaf` (GSC ratings), with all fields optional (defaults to IFPUG standard)
- [x] T026 [P] [US3] Implement `RulePackApplicator` class in `specmetrics/plugins/measurement/apf/rule_applicator.py` — loads Rule Pack from YAML, resolves overrides against default IFPUG matrices, applies exclusions by function type or CFM element ID, computes VAF from GSC ratings
- [x] T027 [US3] Integrate Rule Pack applicator into `plugin.py` — `measure()` accepts optional `rule_pack` parameter; passes it through counter and explainer; records `rule_pack_id` in `APFMeasurementResult`
- [x] T028 [US3] Update `MeasurementExplainer` to include `rule_exceptions` — when a Rule Pack modifies a function's count or complexity, document the specific override and its effect
- [x] T029 [US3] Integration test: Rule Pack exclusions and complexity overrides in `tests/integration/measurement/apf/test_full_measurement.py`

**Checkpoint**: US3 complete — Rule Packs customize measurement without changing engine code or CFM.

---

## Phase 6: User Story 4 — Plugin Discovery & Pipeline Integration (Priority: P2)

**Goal**: The Measurement Engine is automatically discovered via Python Entry Points and registered with the Plugin Registry. The Pipeline Engine invokes it at the `MEASUREMENT_COMPLETED` stage.

**Independent Test**: Install the APF plugin package; start the system and verify it appears in the Plugin Registry. Run the pipeline and verify `MeasurementCompleted` event is emitted with a valid `APFMeasurementResult` in the context.

### Tests for User Story 4

- [x] T030 [P] [US4] Unit test for entry point discovery in `tests/unit/measurement/apf/test_plugin.py`

### Implementation for User Story 4

- [x] T031 [P] [US4] Implement `APFMeasurementPlugin` class in `specmetrics/plugins/measurement/apf/plugin.py` — satisfies `MeasurementPlugin` protocol; exposes `plugin_id() -> "apf"`, `supported_methodology()`, `supported_function_types()`, and `measure(cfm, rule_pack)`
- [x] T032 [P] [US4] Register entry point in project's `pyproject.toml` under `specmetrics.plugins.measurement` group pointing to `APFMeasurementPlugin`
- [x] T033 [P] [US4] Wire `MeasurementCompleted` event emission in `plugin.py` — `measure()` returns `APFMeasurementResult` and the pipeline emits `EventType.MEASUREMENT_COMPLETED`
- [x] T034 [US4] Integration test: pipeline event flow in `tests/integration/measurement/apf/test_full_measurement.py` — verify the plugin registers correctly and `measurement_result` appears in pipeline context

**Checkpoint**: US4 complete — APF plugin is fully integrated into the SpecMetrics pipeline.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, determinism verification, and documentation.

- [x] T035 [P] Implement determinism verification test — measure identical CFM twice, assert `model_dump_json()` outputs are byte-identical in `tests/unit/measurement/apf/test_counter.py`
- [x] T036 [P] Run quickstart.md validation scenarios end-to-end per `specs/008-measurement-engine-apf/quickstart.md`
- [x] T037 Update `specs/008-measurement-engine-apf/checklists/requirements.md` with task completion status
- [x] T038 Document any CFM model changes needed (e.g., Operation direction metadata, DataGroup field counts) in `specmetrics/kernel/cfm/model.py` notes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–6)**: All depend on Foundational phase completion
  - US1 (Phase 3) must complete before US2 (Phase 4) — explainer depends on counter
  - US3 (Phase 5) can run in parallel with US2 — Rule Pack applicator is independent of explainer
  - US4 (Phase 6) requires US1 for the `measure()` integration but can be scaffolded in parallel
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 — Automated APF Measurement (P1)**: Foundational only — no story dependencies
- **US2 — Explainable Results (P1)**: Depends on US1 (consumes `MeasuredFunction` from counter), but explainer module can be implemented with known interface
- **US3 — Rule Pack Integration (P1)**: Can start after Foundational — independent of US1/US2 logic
- **US4 — Plugin Discovery (P2)**: Can start after Foundational — independent wiring

### Within Each User Story

- Tests first, then implementation
- Models before services
- Core logic before integration
- Story complete before moving to next

### Parallel Opportunities

- T003 and T004 can run in parallel
- T005, T006, T007 can run in parallel within Phase 2
- Tests within a phase marked [P] can run in parallel
- US2 (Phase 4) and US3 (Phase 5) can proceed in parallel after US1 completes
- All models and tests marked [P] within any phase can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all foundational tasks together:
Task: "Define Pydantic models in specmetrics/plugins/measurement/apf/models.py"
Task: "Implement complexity matrices in specmetrics/plugins/measurement/apf/complexity.py"
Task: "Implement MeasurementPlugin Protocol in specmetrics/plugins/measurement/apf/plugin.py"
```

## Parallel Example: US1 + US3 (concurrent after Foundation)

```bash
# Developer A: User Story 1
Task: "Implement APFCounter in specmetrics/plugins/measurement/apf/counter.py"
Task: "Wire measurement flow in specmetrics/plugins/measurement/apf/plugin.py"

# Developer B: User Story 3 (independent of US1)
Task: "Implement RulePack model in specmetrics/plugins/measurement/apf/models.py"
Task: "Implement RulePackApplicator in specmetrics/plugins/measurement/apf/rule_applicator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (models + complexity matrices + protocol)
3. Complete Phase 3: User Story 1 (counter + basic measurement)
4. **STOP and VALIDATE**: Run `test_full_measurement.py` — verify APF counts are correct against known CFM
5. MVP delivers: automated APF measurement with default IFPUG rules

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Basic APF measurement → **MVP delivered** 🎯
3. Add US2 → Explainable results → Audit-ready measurement
4. Add US3 → Rule Pack support → Customizable organizational policies
5. Add US4 → Pipeline integration → End-to-end automated pipeline

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 → US2 (serial: explainer depends on counter)
   - Developer B: US3 (independent — Rule Pack processing)
   - Developer C: US4 scaffold (plugin wiring, entry points)
3. All stories integrate and are independently testable

---

## Summary

| Phase | Description | Tasks | Story | Priority |
|-------|-------------|-------|-------|----------|
| 1 | Setup | 4 | — | — |
| 2 | Foundational | 3 | — | — |
| 3 | Automated APF Measurement | 8 | US1 | P1 🎯 |
| 4 | Explainable Results | 5 | US2 | P1 |
| 5 | Rule Pack Integration | 9 | US3 | P1 |
| 6 | Plugin Discovery & Pipeline | 5 | US4 | P2 |
| 7 | Polish & Validation | 4 | — | — |
| **Total** | | **38** | | |

**MVP Scope**: Phases 1–3 (15 tasks) — automated APF measurement with default IFPUG rules, end-to-end.
