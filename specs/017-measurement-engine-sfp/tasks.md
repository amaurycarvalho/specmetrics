---
description: "Task list for SFP Measurement Engine implementation"

---

# Tasks: Measurement Engine Plugin — SFP

**Input**: Design documents from `specs/017-measurement-engine-sfp/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to verify deterministic behavior, component identification, evidence trails, and Rule Pack integration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/measurement/sfp/`, `tests/` at repository root
- Paths below follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the SFP measurement plugin.

- [ ] T001 Create `specmetrics/plugins/measurement/sfp/` package with `__init__.py`
- [ ] T002 [P] Create `tests/unit/measurement/sfp/` directory structure
- [ ] T003 [P] Create `tests/integration/measurement/sfp/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and plugin protocol that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Define SFP measurement Pydantic models in `specmetrics/plugins/measurement/sfp/models.py` — `SFPMeasurementResult`, `MeasuredComponent`, `MeasurementSummary`, `TypeBreakdown`, `MeasurementExplanation`, `MeasurementWarning`, `MeasurementError`, `EvidenceRef`, `ComponentType` (Literal: `functional_process`, `logical_function`) per `data-model.md`
- [ ] T005 [P] Implement `MeasurementPlugin` Protocol class in `specmetrics/plugins/measurement/sfp/plugin.py` with `plugin_id()`, `supported_methodology()`, `supported_component_types()`, and `measure(cfm, rule_pack)` methods per contract in `contracts/measurement-plugin-interface.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Automatic SFP Measurement (Priority: P1) 🎯 MVP

**Goal**: A software estimator can run `specmetrics measure --method sfp` and receive a complete SFP measurement (Functional Process count, Logical Function count, total SFP) automatically from the Canonical Functional Model.

**Independent Test**: Provide a known CFM with identifiable Elementary Processes and Data Groups; verify the measurement output contains correct component type counts and total SFP matching expected fixed contribution values.

### Tests for User Story 1

- [ ] T006 [P] [US1] Unit test for ElementaryProcess-to-FunctionalProcess classification in `tests/unit/measurement/sfp/test_counter.py` — verify CFM nodes with `node_type == "elementary_process"` are identified as Functional Processes. Covers FR-014.
- [ ] T007 [P] [US1] Unit test for DataGroup-to-LogicalFunction classification in `tests/unit/measurement/sfp/test_counter.py` — verify CFM Data Groups representing user-recognizable business information are identified as Logical Functions. Covers FR-011.
- [ ] T008 [P] [US1] Unit test for fixed contribution value assignment in `tests/unit/measurement/sfp/test_counter.py` — verify each Functional Process gets its fixed SFP value and each Logical Function gets its fixed SFP value. Covers FR-019, FR-020.
- [ ] T009 [P] [US1] Unit test for empty CFM returning zero counts in `tests/unit/measurement/sfp/test_counter.py` — covers Edge Cases: Empty CFM.
- [ ] T010 [P] [US1] Unit test for duplicate component merging in `tests/unit/measurement/sfp/test_counter.py` — verify duplicate CFM elements (matching node ID + content fingerprint) are merged into a single MeasuredComponent with a warning emitted. Covers FR-017, FR-018.
- [ ] T011 [P] [US1] Unit test for deterministic output (byte-identical on repeated execution) in `tests/unit/measurement/sfp/test_counter.py` — covers SC-001.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `SFPCounter` class in `specmetrics/plugins/measurement/sfp/counter.py` — scans CFM for Elementary Processes (→ FunctionalProcess) and Data Groups (→ LogicalFunction) via node type/attribute matching; assigns fixed contribution values per component type; merges duplicates by CFM node ID + content fingerprint (SHA-256 of `document_id`, `section_id`, `text`, `semantic_type`). Covers FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021–FR-027 (no complexity, no DET/RET/FTR), FR-033 (evidence references).
- [ ] T013 [US1] Wire basic measurement flow in `specmetrics/plugins/measurement/sfp/plugin.py` — `measure()` method creates `SFPCounter`, invokes it against the CFM, populates `SFPMeasurementResult` with `MeasuredComponent` entries and `MeasurementSummary`, returns the result. Covers FR-001, FR-002, FR-003, FR-004, FR-006, FR-010.
- [ ] T014 [US1] Handle edge cases in `specmetrics/plugins/measurement/sfp/counter.py` — zero-count result for empty CFM; missing Functional Processes produce zero FP count; missing Logical Files produce zero LF count; unresolvable references produce warnings. Covers Edge Cases: Empty CFM, Missing Functional Processes, Missing Logical Files.
- [ ] T015 [US1] Integration test: full measurement with a synthetic CFM in `tests/integration/measurement/sfp/test_full_measurement.py` — create a CFM with known Elementary Processes and Data Groups, run measurement, verify component counts, total SFP, and evidence presence.

**Checkpoint**: US1 complete — basic SFP measurement works end-to-end with default fixed contribution values.

---

## Phase 4: User Story 2 — Explainable Measurement Results (Priority: P1)

**Goal**: Every measured component preserves evidence references to originating CFM elements, and users can inspect a full explanation for each component.

**Independent Test**: Measure a known CFM and verify every `MeasuredComponent` in the output has non-empty evidence references. Request the explanation for any component and verify it includes identification reason, contribution reason, and evidence chain.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for evidence trail preservation in `tests/unit/measurement/sfp/test_counter.py` — verify each `MeasuredComponent.evidence_refs` contains the originating CFM element's evidence. Covers FR-033, FR-034.
- [ ] T017 [P] [US2] Unit test for measurement explanation completeness in `tests/unit/measurement/sfp/test_plugin.py` — verify each `MeasurementExplanation` includes `identification_reason`, `contribution_reason`, and `evidence_chain`. Covers FR-033.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `MeasurementExplainer` class in `specmetrics/plugins/measurement/sfp/explainer.py` — builds `MeasurementExplanation` for each `MeasuredComponent` with `identification_reason` (why CFM element maps to this component type), `contribution_reason` (default value or Rule Pack override), `rule_exceptions` (if any), and `evidence_chain` tracing: spec section → evidence graph → CFM element → measured component. Covers FR-033, FR-034, FR-035.
- [ ] T019 [US2] Integrate explainer into `plugin.py` — after counter runs, invoke `MeasurementExplainer` to populate `SFPMeasurementResult.explanations`. Covers FR-033.
- [ ] T020 [US2] Integrate evidence reference propagation into `counter.py` — each `MeasuredComponent` copies `EvidenceRef` from the originating CFM element's evidence field. Covers FR-033.
- [ ] T021 [US2] Integration test: verify evidence trail completeness in `tests/integration/measurement/sfp/test_full_measurement.py` — measure a CFM with known evidence refs, verify every component has non-empty evidence chain.

**Checkpoint**: US2 complete — all measured components are explainable with evidence trails.

---

## Phase 5: User Story 3 — Rule Pack Customization (Priority: P2)

**Goal**: Organizational Rule Packs can exclude Functional Processes or Logical Functions, redefine inclusion criteria, and override fixed contribution values — without modifying the engine or the CFM.

**Independent Test**: Apply a Rule Pack that excludes Logical Functions; the resulting count must be zero Logical Functions. Apply a Rule Pack with overridden contribution values; the total SFP must reflect the custom values.

### Tests for User Story 3

- [ ] T022 [P] [US3] Unit test for Rule Pack exclusion of Functional Processes by CFM element ID in `tests/unit/measurement/sfp/test_rule_applicator.py` — covers FR-028.
- [ ] T023 [P] [US3] Unit test for Rule Pack exclusion of Logical Functions by name pattern in `tests/unit/measurement/sfp/test_rule_applicator.py` — covers FR-029.
- [ ] T024 [P] [US3] Unit test for Rule Pack redefinition of inclusion criteria (custom node type/attribute matching) in `tests/unit/measurement/sfp/test_rule_applicator.py` — covers FR-030.
- [ ] T025 [P] [US3] Unit test for contribution value override in `tests/unit/measurement/sfp/test_rule_applicator.py` — verify Rule Pack can change the fixed SFP value per component type.
- [ ] T026 [P] [US3] Unit test that Rule Pack cannot modify the deterministic algorithm in `tests/unit/measurement/sfp/test_rule_applicator.py` — covers FR-031.
- [ ] T027 [P] [US3] Unit test that all Rule Pack adjustments are reported in output in `tests/unit/measurement/sfp/test_rule_applicator.py` — covers FR-032.
- [ ] T028 [P] [US3] Unit test for SC-006: Invalid Rule Pack generates warnings, does not prevent measurement in `tests/unit/measurement/sfp/test_rule_applicator.py`.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `RulePackApplicator` class in `specmetrics/plugins/measurement/sfp/rule_applicator.py` — loads and validates Rule Pack YAML; applies exclusions (by CFM element ID or name pattern), redefines inclusion criteria (custom node type/attribute matching rules), and overrides contribution values. Rule Pack adjustments are collected for reporting. Invalid Rule Packs generate warnings without aborting. Covers FR-028, FR-029, FR-030, FR-031, FR-032.
- [ ] T030 [US3] Integrate RulePackApplicator into `plugin.py` — `measure()` loads the Rule Pack (if provided), passes it to `SFPCounter` via `RulePackApplicator`, applies rules after component identification, and populates `rule_applied` and warnings in the output. Covers FR-005.
- [ ] T031 [US3] Integration test: full measurement with Rule Pack in `tests/integration/measurement/sfp/test_full_measurement.py` — apply a Rule Pack that excludes specific components and overrides values, verify output reflects all adjustments.

**Checkpoint**: US3 complete — organizational policies can customize SFP measurement via external Rule Packs.

---

## Phase 6: User Story 4 — Pipeline Integration (Priority: P2)

**Goal**: The SFP plugin is automatically discovered by the Plugin Registry, registers as a measurement plugin, integrates with the event-driven pipeline, and supports asynchronous execution and incremental recomputation.

**Independent Test**: Register the SFP plugin via Python Entry Points, verify it appears in the plugin registry. Execute the full pipeline with a CFM and verify SFP measurement is invoked automatically after Rule Pack processing.

### Tests for User Story 4

- [ ] T032 [P] [US4] Unit test for plugin discovery via `specmetrics.plugins.measurement` entry point in `tests/unit/measurement/sfp/test_plugin.py` — covers FR-007. Verifies SC-005.
- [ ] T033 [P] [US4] Unit test for `MeasurementCompleted` event emission in `tests/unit/measurement/sfp/test_plugin.py` — verify the plugin emits the measurement event with `SFPMeasurementResult` payload. Covers FR-037.
- [ ] T034 [P] [US4] Unit test for incremental recomputation — only modified components recalculated in `tests/unit/measurement/sfp/test_counter.py` — covers FR-039, FR-040. Verifies SC-004.

### Implementation for User Story 4

- [ ] T035 [US4] Register `pyproject.toml` entry point for SFP plugin — add `[project.entry-points."specmetrics.plugins.measurement"] sfp = "specmetrics.plugins.measurement.sfp:SFPMeasurementPlugin"`. Covers FR-007.
- [ ] T036 [US4] Implement event emission in `plugin.py` — `measure()` emits `MeasurementCompleted` event with `SFPMeasurementResult` payload. Covers FR-037.
- [ ] T037 [US4] Implement asynchronous execution support in `plugin.py` — the measure method signature accepts an async execution flag and returns a future/coroutine. Covers FR-038.
- [ ] T038 [US4] Implement incremental recomputation in `counter.py` — accept a previous measurement result and a list of modified CFM element IDs; only recalculate those components. Covers FR-039, FR-040. Verifies SC-004.
- [ ] T039 [US4] Integration test: full pipeline execution with SFP plugin in `tests/integration/measurement/sfp/test_full_measurement.py` — verify SFP measurement is automatically invoked during pipeline execution.

**Checkpoint**: US4 complete — SFP plugin is fully integrated into the SpecMetrics pipeline.

---

## Phase 7: Observability & Cross-Cutting Concerns

**Purpose**: Structured logging, OpenTelemetry metrics, and edge case hardening.

- [ ] T040 [P] Implement structured INFO/ERROR logging in `plugin.py` — log measurement start, completion, component counts, warnings, and failures via structlog. Covers FR-041.
- [ ] T041 [P] Implement OpenTelemetry metrics in `plugin.py` — emit histogram for measurement duration and gauges for Functional Process count and Logical Function count. Covers FR-042.
- [ ] T042 [P] Performance benchmark test in `tests/unit/measurement/sfp/test_counter.py` — verify medium-sized CFM (≤500 FP, ≤300 LF) completes in under 5 seconds. Covers SC-003.
- [ ] T043 [P] Scalability verification test in `tests/integration/measurement/sfp/test_full_measurement.py` — verify that doubling the CFM size results in ≤15% deviation from linear scaling. Covers SC-007.
- [ ] T044 [P] Edge case tests for corrupted plugin metadata and cyclic references in `tests/unit/measurement/sfp/test_plugin.py`. Covers Edge Cases.

---

## Dependencies

```text
Phase 1 (Setup)
  └─► Phase 2 (Foundational: models + protocol)
        ├─► Phase 3 (US1: Automatic Measurement) ◄── MVP
        │     ├─► Phase 4 (US2: Explainability)
        │     └─► Phase 5 (US3: Rule Packs)
        └─► Phase 6 (US4: Pipeline Integration)
              └─► Phase 7 (Observability & Polish)
```

## Parallel Execution Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003 (both directory creation) |
| Phase 2 | T004, T005 (models + protocol are independent) |
| Phase 3 (US1) | T006–T011 (all tests are parallel); T012–T013 (counter + plugin wiring depend on T004, T005) |
| Phase 4 (US2) | T016–T017 (tests); T018 (explainer can be built independently) |
| Phase 5 (US3) | T022–T028 (all tests parallel); T029 (applicator) |
| Phase 6 (US4) | T032–T034 (tests); T035 (entry point is fast); T036–T038 have some dependencies |
| Phase 7 | T040–T044 (all independent) |

## Implementation Strategy

### MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1)** — This is the minimum viable product:
- Directory structure, Pydantic models, plugin protocol
- Component identification (Functional Processes + Logical Functions)
- Fixed contribution value assignment
- Deterministic output
- Edge case handling (empty CFM, missing components, duplicates)

**Value at MVP**: A software estimator can run `specmetrics measure --method sfp` and receive a correct, deterministic SFP measurement.

### Incremental Delivery

1. **MVP** (Phase 1–3): Basic measurement with default values, no explainability, no Rule Packs
2. **US2** (Phase 4): Add evidence trails and explanations without changing counter logic
3. **US3** (Phase 5): Add Rule Pack support — exclusion, inclusion, value override
4. **US4** (Phase 6): Full pipeline integration — discovery, events, async, incremental
5. **Polish** (Phase 7): Observability, benchmarks, remaining edge cases

Each phase is independently testable and adds production value without breaking previous phases.

---

## Summary

| Phase | User Story | Tasks | Priority |
|-------|-----------|-------|----------|
| 1 | Setup | 3 | Required |
| 2 | Foundational | 2 | Required |
| 3 | US1: Automatic SFP Measurement | 10 | P1 🎯 MVP |
| 4 | US2: Explainable Measurement | 6 | P1 |
| 5 | US3: Rule Pack Customization | 10 | P2 |
| 6 | US4: Pipeline Integration | 8 | P2 |
| 7 | Observability & Polish | 5 | Cross-cutting |
| **Total** | | **44** | |
