---
description: "Task list for SNAP Measurement Engine implementation"

---

# Tasks: Measurement Engine Plugin — SNAP

**Input**: Design documents from `specs/018-measurement-engine-snap/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to verify deterministic behavior, candidate identification, category assessment, evidence trails, and Rule Pack integration.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/measurement/snap/`, `tests/` at repository root
- Paths below follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the SNAP measurement plugin.

- [ ] T001 Create `specmetrics/plugins/measurement/snap/` package with `__init__.py`
- [ ] T002 [P] Create `tests/unit/measurement/snap/` directory structure
- [ ] T003 [P] Create `tests/integration/measurement/snap/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, category definitions, and plugin protocol that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Define SNAP assessment Pydantic models in `specmetrics/plugins/measurement/snap/models.py` — `SNAPMeasurementResult`, `CategoryAssessment`, `AssessedItem`, `AssessmentSummary`, `CategoryBreakdown`, `AssessmentExplanation`, `AssessmentWarning`, `AssessmentError`, `EvidenceRef` per `data-model.md`
- [ ] T005 [P] Implement `MeasurementPlugin` Protocol class in `specmetrics/plugins/measurement/snap/plugin.py` with `plugin_id()`, `supported_methodology()`, `supported_function_types()`, and `measure(cfm, rule_pack)` methods per contract in `contracts/measurement-plugin-interface.md`
- [ ] T006 [P] Implement default assessment category registry in `specmetrics/plugins/measurement/snap/models.py` — define the four default SNAP categories (Presentation, Data Operations, Operational Capabilities, Technical Interaction) with SemVer version strings, category IDs, and fixed contribution value slots. Covers FR-011, FR-012, FR-013, FR-015.

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Automatic SNAP Measurement (Priority: P1) 🎯 MVP

**Goal**: A software estimator can run `specmetrics measure --method snap` and receive a complete SNAP assessment (category breakdowns, item counts, total SNAP) automatically from the Canonical Functional Model.

**Independent Test**: Provide a known CFM with semantic metadata markers; verify the assessment output contains correct category assignments, item counts, and total SNAP matching expected fixed contribution values.

### Tests for User Story 1

- [ ] T007 [P] [US1] Unit test for assessment candidate identification from semantic metadata markers in `tests/unit/measurement/snap/test_assessor.py` — verify CFM nodes with markers like `presentation_interface` and `data_operation` are identified. Covers FR-016.
- [ ] T008 [P] [US1] Unit test for candidate-to-category classification in `tests/unit/measurement/snap/test_assessor.py` — verify each semantic marker maps to the correct assessment category per data-model.md classification mapping. Covers FR-011.
- [ ] T009 [P] [US1] Unit test for fixed contribution value assignment per category in `tests/unit/measurement/snap/test_assessor.py` — verify each assessed item gets the correct contribution value for its category. Covers FR-020.
- [ ] T010 [P] [US1] Unit test for empty CFM returning zero counts in `tests/unit/measurement/snap/test_assessor.py` — covers Edge Cases: Empty CFM.
- [ ] T011 [P] [US1] Unit test for duplicate candidate merging in `tests/unit/measurement/snap/test_assessor.py` — verify duplicate CFM elements (matching node ID + content fingerprint) are merged into a single AssessedItem with warning. Covers FR-017.
- [ ] T012 [P] [US1] Unit test for deterministic output (byte-identical on repeated execution) in `tests/unit/measurement/snap/test_assessor.py` — covers SC-001.
- [ ] T013 [P] [US1] Unit test for single-category item assignment in `tests/unit/measurement/snap/test_assessor.py` — verify each item belongs to exactly one category. Covers FR-012.
- [ ] T014 [P] [US1] Unit test for missing semantic metadata handling in `tests/unit/measurement/snap/test_assessor.py` — verify items missing required metadata produce reports as unresolved warnings. Covers FR-024, Edge Cases: Missing presentation/operational metadata.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `SNAPAssessor` class in `specmetrics/plugins/measurement/snap/assessor.py` — scans CFM nodes for semantic metadata markers; maps each marker to an assessment category using the classification table; assigns fixed contribution values per category; creates `AssessedItem` entries with evidence refs; merges duplicates by CFM node ID + content fingerprint (SHA-256). Covers FR-011, FR-012, FR-013, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-024.
- [ ] T016 [US1] Wire basic assessment flow in `specmetrics/plugins/measurement/snap/plugin.py` — `measure()` method creates `SNAPAssessor`, invokes it against the CFM, populates `SNAPMeasurementResult` with `CategoryAssessment` groups, `AssessedItem` entries, and `AssessmentSummary`, returns the result. Covers FR-001, FR-002, FR-003, FR-004, FR-006, FR-010.
- [ ] T017 [US1] Handle edge cases in `specmetrics/plugins/measurement/snap/assessor.py` — zero-count result for empty CFM; missing presentation/operational metadata produce warnings; unsupported interaction types produce unresolved warnings. Covers Edge Cases.
- [ ] T018 [US1] Integration test: full assessment with a synthetic CFM in `tests/integration/measurement/snap/test_full_assessment.py` — create a CFM with known semantic metadata markers, run assessment, verify category breakdowns, item counts, total SNAP, and evidence presence.

**Checkpoint**: US1 complete — basic SNAP assessment works end-to-end with default category definitions and contribution values.

---

## Phase 4: User Story 2 — Explainable Assessment Results (Priority: P1)

**Goal**: Every assessed item preserves evidence references to originating CFM elements, and users can inspect a full explanation for each item.

**Independent Test**: Assess a known CFM and verify every `AssessedItem` in the output has non-empty evidence references. Request the explanation for any item and verify it includes identification reason, contribution reason, and evidence chain.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for evidence trail preservation in `tests/unit/measurement/snap/test_assessor.py` — verify each `AssessedItem.evidence_refs` contains the originating CFM element's evidence. Covers FR-030, FR-031.
- [ ] T020 [P] [US2] Unit test for category-specific evidence in `tests/unit/measurement/snap/test_assessor.py` — verify evidence refs include the category context. Covers FR-022.
- [ ] T021 [P] [US2] Unit test for assessment explanation completeness in `tests/unit/measurement/snap/test_plugin.py` — verify each `AssessmentExplanation` includes `identification_reason`, `contribution_reason`, and `evidence_chain`. Covers FR-030.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `AssessmentExplainer` class in `specmetrics/plugins/measurement/snap/explainer.py` — builds `AssessmentExplanation` for each `AssessedItem` with `identification_reason` (why CFM semantic marker maps to this category), `contribution_reason` (default value or Rule Pack override), `rule_exceptions` (if any), and `evidence_chain` tracing: spec section → evidence graph → CFM element → assessed item. Covers FR-030, FR-031, FR-032, FR-022.
- [ ] T023 [US2] Integrate explainer into `plugin.py` — after assessor runs, invoke `AssessmentExplainer` to populate `SNAPMeasurementResult.explanations`. Covers FR-030.
- [ ] T024 [US2] Integrate evidence reference propagation into `assessor.py` — each `AssessedItem` copies `EvidenceRef` from the originating CFM element's evidence field. Covers FR-030.
- [ ] T025 [US2] Integration test: verify evidence trail completeness in `tests/integration/measurement/snap/test_full_assessment.py` — assess a CFM with known evidence refs, verify every item has non-empty evidence chain.

**Checkpoint**: US2 complete — all assessed items are explainable with evidence trails.

---

## Phase 5: User Story 3 — Organizational Policies (Priority: P2)

**Goal**: Organizational Rule Packs can exclude assessment categories, exclude individual assessment items, redefine inclusion policies, and override category contribution values — without modifying the engine or the CFM.

**Independent Test**: Apply a Rule Pack that excludes the Technical Interaction category; the resulting assessment must have zero items in that category. Apply a Rule Pack with overridden inclusion policies; assessment candidates matching the new policy must be identified.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for Rule Pack exclusion of entire assessment category in `tests/unit/measurement/snap/test_rule_applicator.py` — covers FR-025.
- [ ] T027 [P] [US3] Unit test for Rule Pack exclusion of individual items by CFM element ID in `tests/unit/measurement/snap/test_rule_applicator.py` — covers FR-026.
- [ ] T028 [P] [US3] Unit test for Rule Pack redefinition of inclusion policies (custom semantic marker → category mapping) in `tests/unit/measurement/snap/test_rule_applicator.py` — covers FR-027.
- [ ] T029 [P] [US3] Unit test for contribution value override per category in `tests/unit/measurement/snap/test_rule_applicator.py` — verify Rule Pack can change the fixed value per category.
- [ ] T030 [P] [US3] Unit test that Rule Pack cannot modify the deterministic algorithm in `tests/unit/measurement/snap/test_rule_applicator.py` — covers FR-028.
- [ ] T031 [P] [US3] Unit test that all Rule Pack adjustments are reported in output in `tests/unit/measurement/snap/test_rule_applicator.py` — covers FR-029.
- [ ] T032 [P] [US3] Unit test for FR-023: excluded assessment candidates reported in output in `tests/unit/measurement/snap/test_rule_applicator.py`.
- [ ] T033 [P] [US3] Unit test for SC-006: Invalid Rule Pack generates warnings, does not prevent assessment in `tests/unit/measurement/snap/test_rule_applicator.py`.

### Implementation for User Story 3

- [ ] T034 [US3] Implement `RulePackApplicator` class in `specmetrics/plugins/measurement/snap/rule_applicator.py` — loads and validates Rule Pack YAML; applies category exclusions, item exclusions (by ID or name pattern), inclusion policy redefinitions (custom marker→category mapping), and contribution value overrides. Excluded items marked as `excluded=True` with zero contribution but preserved in output. Invalid Rule Packs generate warnings without aborting. Covers FR-025, FR-026, FR-027, FR-028, FR-029, FR-023.
- [ ] T035 [US3] Integrate RulePackApplicator into `plugin.py` — `measure()` loads the Rule Pack (if provided), passes it to `SNAPAssessor` via `RulePackApplicator`, applies rules after candidate identification, and populates `rule_applied` and warnings in the output. Covers FR-005.
- [ ] T036 [US3] Integration test: full assessment with Rule Pack in `tests/integration/measurement/snap/test_full_assessment.py` — apply a Rule Pack that excludes a category and overrides values, verify output reflects all adjustments.

**Checkpoint**: US3 complete — organizational policies can customize SNAP assessment via external Rule Packs.

---

## Phase 6: User Story 4 — Pipeline Integration (Priority: P2)

**Goal**: The SNAP plugin is automatically discovered by the Plugin Registry, registers as a measurement plugin, integrates with the event-driven pipeline, and supports asynchronous execution and incremental recomputation.

**Independent Test**: Register the SNAP plugin via Python Entry Points, verify it appears in the plugin registry. Execute the full pipeline with a CFM and verify SNAP assessment is invoked automatically after Rule Pack processing.

### Tests for User Story 4

- [ ] T037 [P] [US4] Unit test for plugin discovery via `specmetrics.plugins.measurement` entry point in `tests/unit/measurement/snap/test_plugin.py` — covers FR-007. Verifies SC-005.
- [ ] T038 [P] [US4] Unit test for `MeasurementCompleted` event emission in `tests/unit/measurement/snap/test_plugin.py` — verify the plugin emits the measurement event with `SNAPMeasurementResult` payload. Covers FR-034.
- [ ] T039 [P] [US4] Unit test for incremental recomputation — only modified candidates recalculated in `tests/unit/measurement/snap/test_assessor.py` — covers FR-036, FR-037. Verifies SC-004.

### Implementation for User Story 4

- [ ] T040 [US4] Register `pyproject.toml` entry point for SNAP plugin — add `[project.entry-points."specmetrics.plugins.measurement"] snap = "specmetrics.plugins.measurement.snap:SNAPMeasurementPlugin"`. Covers FR-007.
- [ ] T041 [US4] Implement event emission in `plugin.py` — `measure()` emits `MeasurementCompleted` event with `SNAPMeasurementResult` payload. Covers FR-034.
- [ ] T042 [US4] Implement asynchronous execution support in `plugin.py` — the measure method signature accepts an async execution flag and returns a future/coroutine. Covers FR-035.
- [ ] T043 [US4] Implement incremental recomputation in `assessor.py` — accept a previous assessment result and a list of modified CFM element IDs; only recalculate those candidates. Covers FR-036, FR-037. Verifies SC-004.
- [ ] T044 [US4] Integration test: full pipeline execution with SNAP plugin in `tests/integration/measurement/snap/test_full_assessment.py` — verify SNAP assessment is automatically invoked during pipeline execution.

**Checkpoint**: US4 complete — SNAP plugin is fully integrated into the SpecMetrics pipeline.

---

## Phase 7: Observability & Cross-Cutting Concerns

**Purpose**: Structured logging, OpenTelemetry metrics, and edge case hardening.

- [ ] T045 [P] Implement structured INFO/ERROR logging in `plugin.py` — log assessment start, completion, per-category counts, warnings, and failures via structlog. Covers FR-038.
- [ ] T046 [P] Implement OpenTelemetry metrics in `plugin.py` — emit histogram for assessment duration and gauges for per-category assessment item counts. Covers FR-039.
- [ ] T047 [P] Performance benchmark test in `tests/unit/measurement/snap/test_assessor.py` — verify medium-sized CFM (≤500 candidates) completes in under 5 seconds. Covers SC-003.
- [ ] T048 [P] Scalability verification test in `tests/integration/measurement/snap/test_full_assessment.py` — verify that doubling the CFM size results in ≤15% deviation from linear scaling. Covers SC-007.
- [ ] T049 [P] Category version validation test in `tests/unit/measurement/snap/test_assessor.py` — verify category SemVer is validated at load time; invalid versions produce errors. Covers FR-015.
- [ ] T050 [P] Edge case tests for corrupted plugin metadata and unsupported interaction types in `tests/unit/measurement/snap/test_plugin.py`. Covers Edge Cases.

---

## Dependencies

```text
Phase 1 (Setup)
  └─► Phase 2 (Foundational: models + protocol + categories)
        ├─► Phase 3 (US1: Automatic Assessment) ◄── MVP
        │     ├─► Phase 4 (US2: Explainability)
        │     └─► Phase 5 (US3: Rule Packs)
        └─► Phase 6 (US4: Pipeline Integration)
              └─► Phase 7 (Observability & Polish)
```

## Parallel Execution Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003 (both directory creation) |
| Phase 2 | T004, T005, T006 (models + protocol + categories are independent) |
| Phase 3 (US1) | T007–T014 (all tests parallel); T015 + T016 (assessor + plugin wiring) |
| Phase 4 (US2) | T019–T021 (tests); T022 (explainer) |
| Phase 5 (US3) | T026–T033 (all tests parallel); T034 (applicator) |
| Phase 6 (US4) | T037–T039 (tests); T040 (entry point); T041–T043 have some dependencies |
| Phase 7 | T045–T050 (all independent) |

## Implementation Strategy

### MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US1)** — This is the minimum viable product:
- Directory structure, Pydantic models, plugin protocol, category registry
- Assessment candidate identification from semantic metadata markers
- Category-based classification and fixed contribution assignment
- Deterministic output
- Edge case handling (empty CFM, missing metadata, duplicates)

**Value at MVP**: A software estimator can run `specmetrics measure --method snap` and receive a correct, deterministic SNAP assessment with category breakdown.

### Incremental Delivery

1. **MVP** (Phase 1–3): Basic assessment with default categories and values, no explainability, no Rule Packs
2. **US2** (Phase 4): Add evidence trails and explanations without changing assessor logic
3. **US3** (Phase 5): Add Rule Pack support — category/item exclusion, inclusion policy, value override
4. **US4** (Phase 6): Full pipeline integration — discovery, events, async, incremental
5. **Polish** (Phase 7): Observability, benchmarks, category version validation, remaining edge cases

Each phase is independently testable and adds production value without breaking previous phases.

---

## Summary

| Phase | User Story | Tasks | Priority |
|-------|-----------|-------|----------|
| 1 | Setup | 3 | Required |
| 2 | Foundational | 3 | Required |
| 3 | US1: Automatic SNAP Assessment | 12 | P1 🎯 MVP |
| 4 | US2: Explainable Assessment | 7 | P1 |
| 5 | US3: Organizational Policies | 11 | P2 |
| 6 | US4: Pipeline Integration | 8 | P2 |
| 7 | Observability & Polish | 6 | Cross-cutting |
| **Total** | | **50** | |
