# Tasks: T-Shirt Sizing Improvements

**Input**: Design documents from `/specs/041-tshirt-sizing/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included for US1 (mapping) and US2-US4 (outputs). US5 and US6 are verification/documentation.

**Organization**: Tasks are grouped by user story. The mapping update (US1) is foundational and blocks the output stories (US2-US4), which can run in parallel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup

**Purpose**: Confirm baseline before changes begin

- [X] T001 Run existing T-Shirt test suite to establish baseline: `pytest tests/unit/test_tshirt_*.py tests/contract/test_tshirt_measurement.py tests/integration/test_tshirt_pipeline.py -v`
- [X] T002 Document current test results and any existing failures for regression comparison

---

## Phase 2: User Story 1 - Accurate T-Shirt Classification (Priority: P1) 🎯 MVP

**Goal**: Update the default mapping table so Story Point value 8 maps to L (not M) and value 40 maps to XL (not XXL).

**Independent Test**: Run T-Shirt classifier with SP=8 → expect L, SP=40 → expect XL, SP=5 → expect M. All 9 Fibonacci values must be covered by the 6 sizes with no UNKNOWN.

### Tests for User Story 1

- [X] T003 [P] [US1] Update `test_tshirt_classifier.py` to verify SP=8 maps to `"L"` with rule `"default: 8-13 → L"` in `tests/unit/test_tshirt_classifier.py`
- [X] T004 [P] [US1] Update `test_tshirt_classifier.py` to verify SP=40 maps to `"XL"` with rule `"default: 20-40 → XL"` in `tests/unit/test_tshirt_classifier.py`
- [X] T005 [P] [US1] Add test in `test_tshirt_classifier.py` verifying all 9 Fibonacci values (1,2,3,5,8,13,20,40,100) map to exactly 6 size categories with no UNKNOWN in `tests/unit/test_tshirt_classifier.py`
- [X] T006 [P] [US1] Add test in `test_tshirt_classifier.py` verifying the new M=[5] range: SP=5 maps to M, SP values adjacent (3, 8) do NOT map to M in `tests/unit/test_tshirt_classifier.py`

### Implementation for User Story 1

- [X] T007 [US1] Update `DEFAULT_MAPPING` in `specmetrics/plugins/measurement/tshirt/classifier.py`: change M range from (5,8) to (5,5), L from (13,13) to (8,13), XL from (20,20) to (20,40), XXL from (40,100) to (100,100)
- [X] T008 [US1] Run classifier tests to confirm mapping change passes: `pytest tests/unit/test_tshirt_classifier.py -v`
- [X] T009 [US1] Verify existing model tests still pass with updated mapping: `pytest tests/unit/test_tshirt_models.py -v`

**Checkpoint**: Mapping table corrected. SP=8 → L, SP=40 → XL. All 9 Fibonacci values mapped without gaps.

---

## Phase 3: User Story 2 - Correct measure.json Output (Priority: P1)

**Goal**: Fix the T-Shirt `measure.json` entry to show actual entity count (not 0) and include per-size breakdown.

**Independent Test**: Run full pipeline, inspect `measure.json` T-Shirt entry: `total > 0`, `breakdown` has per-size counts summing to total.

### Tests for User Story 2

- [X] T010 [P] [US2] Update `test_tshirt_pipeline.py` to verify the pipeline payload contains `"tshirt"` key with correct entity count in `tests/integration/test_tshirt_pipeline.py`
- [X] T011 [P] [US2] Update `test_tshirt_pipeline.py` to verify the pipeline payload contains `"tshirt_breakdown"` key with per-size `{size: {count: N}}` structure in `tests/integration/test_tshirt_pipeline.py`
- [X] T012 [P] [US2] Update `test_tshirt_measurement.py` to verify the contract includes `tshirt` and `tshirt_breakdown` keys in `tests/contract/test_tshirt_measurement.py`

### Implementation for User Story 2

- [X] T013 [US2] Add `"tshirt": result.total_items` to the payload dict in `_finalize()` method in `specmetrics/plugins/measurement/tshirt/plugin.py`
- [X] T014 [US2] Add `"tshirt_breakdown": {k: {"count": v} for k, v in result.distribution.items()}` to the payload dict in `_finalize()` in `specmetrics/plugins/measurement/tshirt/plugin.py`
- [X] T015 [US2] Update tshirt key_map entry from `"tshirt": ("tshirt", None)` to `"tshirt": ("tshirt", "tshirt_breakdown")` in `_build_stage_entities()` in `specmetrics/application/orchestrator.py`
- [X] T016 [US2] Run integration tests to verify measure.json pipeline: `pytest tests/integration/test_tshirt_pipeline.py -v`

**Checkpoint**: measure.json shows correct T-Shirt total and per-size breakdown.

---

## Phase 4: User Story 3 - Correct metrics.json Output (Priority: P1)

**Goal**: Fix `metrics.json` T-Shirt entry to use `unit: "entities"` and include all required per-entity fields.

**Independent Test**: Run full pipeline, inspect `metrics.json` T-Shirt entry: `unit: "entities"`, entities have all 6 fields.

### Tests for User Story 3

- [X] T017 [P] [US3] Update `test_tshirt_pipeline.py` to verify `metrics.json` T-Shirt entry has `unit: "entities"` in `tests/integration/test_tshirt_pipeline.py`
- [X] T018 [P] [US3] Update `test_tshirt_pipeline.py` to verify each entity in `metrics.json` has fields `id`, `name`, `type`, `story_point_value`, `tshirt_size`, `mapping_rule` in `tests/integration/test_tshirt_pipeline.py`

### Implementation for User Story 3

- [X] T019 [US3] Change `METRIC_UNIT_MAP["tshirt"]` from `"story_points"` to `"entities"` in `specmetrics/application/metrics_json.py`
- [X] T020 [US3] Update `build_tshirt_entity()` to include `story_point_value` and `tshirt_size` as top-level fields in the entity dict in `specmetrics/application/metrics_json.py`
- [X] T021 [US3] Update `build_tshirt_entity()` to use actual entity type from source data instead of hardcoded `"functional_process"` in `specmetrics/application/metrics_json.py`
- [X] T022 [US3] Verify `_build_metric_metadata()` for tshirt returns `scale` string and `mapping` dict with correct representative values in `specmetrics/application/metrics_json.py`
- [X] T023 [US3] Run integration tests to verify metrics.json output: `pytest tests/integration/test_tshirt_pipeline.py -v`

**Checkpoint**: metrics.json shows correct entity fields, unit, and metadata.

---

## Phase 5: User Story 4 - Correct CLI Display (Priority: P2)

**Goal**: Fix CLI output to show `TShirt: N entities` (not 0) with per-size breakdown line.

**Independent Test**: Run `specmetrics measure`, verify terminal shows TShirt total > 0 and breakdown line.

### Tests for User Story 4

- [X] T024 [P] [US4] Add test verifying CLI text output includes non-zero T-Shirt total when Story Points data is present in `tests/integration/test_tshirt_pipeline.py` (or a CLI-specific test)
- [X] T025 [P] [US4] Add test verifying CLI output includes per-size breakdown line with format `XS: N  S: N  ...` in `tests/integration/test_tshirt_pipeline.py`

### Implementation for User Story 4

- [X] T026 [US4] Update `format_text_result()` to read `tshirt` total from metric_results and display `TShirt: N entities` in `specmetrics/cli/formatters.py`
- [X] T027 [US4] Add breakdown line rendering: if metric result has `breakdown` key, render indented line with per-size counts in `specmetrics/cli/formatters.py`
- [X] T028 [US4] Verify `METRIC_DISPLAY_MAP["tshirt"]` correctly maps to `"TShirt"` in `specmetrics/application/models.py`

**Checkpoint**: CLI shows correct T-Shirt total and breakdown.

---

## Phase 6: User Story 5 - Cross-Specification T-Shirt Comparison (Priority: P2)

**Goal**: Verify that with corrected outputs, T-shirt distributions can be meaningfully compared across specifications.

**Independent Test**: Run T-Shirt on two specs with different effort profiles. Verify distribution reflects expected difference.

### Implementation for User Story 5

- [X] T029 [P] [US5] Add integration test verifying two specs with different Story Point distributions produce measurably different T-Shirt distributions (proportion of L/XL/XXL differs by ≥10%) in `tests/integration/test_tshirt_pipeline.py`
- [X] T030 [US5] Run quickstart.md validation scenarios 5 (measure.json breakdown), 6 (metrics.json fields), and 7 (CLI display) and confirm cross-spec data is comparable

**Checkpoint**: Cross-specification comparison validated through corrected outputs.

---

## Phase 7: User Story 6 - T-Shirt RFC Documentation (Priority: P2)

**Goal**: Create RFC document in `docs/rfcs/` documenting the T-Shirt Sizing methodology.

**Independent Test**: Open RFC, verify methodology, mapping table, output formats, and Kanban guidance are present.

### Implementation for User Story 6

- [X] T031 [P] [US6] Create `docs/rfcs/RFC-042 - T-Shirt Sizing.md` with methodology overview: relationship to Story Points, classification logic
- [X] T032 [P] [US6] Add mapping section: complete mapping table with Story Point ranges, T-shirt sizes, and rationale for each grouping
- [X] T033 [P] [US6] Add output formats section: measure.json schema, metrics.json schema, CLI display format with examples
- [X] T034 [P] [US6] Add configuration section: custom mapping support, validation rules, default values
- [X] T035 [P] [US6] Add usage guidance section: cross-specification comparison, Kanban work item sizing as a manual practice

**Checkpoint**: RFC-042 fully documents the T-Shirt Sizing methodology.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, regression check, and cleanup

- [X] T036 Run full T-Shirt test suite: `pytest tests/unit/test_tshirt_*.py tests/contract/test_tshirt_measurement.py tests/integration/test_tshirt_pipeline.py -v`
- [X] T037 [P] Verify backward compatibility: old test fixtures (with SP=8 mapping to M under old mapping) are updated and pass
- [X] T038 Run quickstart.md validation scenarios 1-9 and confirm all pass
- [X] T039 [P] Run ruff linting on modified files: `ruff check specmetrics/plugins/measurement/tshirt/ specmetrics/application/orchestrator.py specmetrics/application/metrics_json.py specmetrics/cli/formatters.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **US1 Mapping (Phase 2)**: Depends on Setup — BLOCKS all output stories
- **US2 measure.json (Phase 3)**: Depends on US1 — can run in parallel with US3 and US4
- **US3 metrics.json (Phase 4)**: Depends on US1 — can run in parallel with US2 and US4
- **US4 CLI Display (Phase 5)**: Depends on US1 and US2 — needs measure.json fix to read correct total
- **US5 Comparison (Phase 6)**: Depends on US2, US3, US4 — validates corrected outputs
- **US6 RFC (Phase 7)**: Can start in parallel with any phase; finalize after US1-US4
- **Polish (Phase 8)**: Depends on all user stories

### User Story Dependencies

```
Setup → US1 (Mapping) → US2 (measure.json) ─┬─→ US4 (CLI) ─┬─→ US5 (Comparison)
                          US3 (metrics.json) ─┘               │
                          US6 (RFC) ──────────────────────────┘
```

US2, US3, and US6 can run in parallel after US1. US4 depends on US2 (needs correct `tshirt` key). US5 validates the combined output from US2-US4.

### Parallel Opportunities

- **Phase 2**: T003, T004, T005, T006 (tests) can run in parallel
- **Phase 3 + Phase 4 + Phase 7**: US2, US3, and US6 are independent of each other — can run simultaneously
- **Phase 7**: All 5 RFC tasks (T031-T035) can run in parallel
- **Phase 8**: T037, T039 can run in parallel

---

## Parallel Example: After US1 Complete

```bash
# Launch output fixes in parallel:
Developer A: Phase 3 - US2 measure.json (plugin.py + orchestrator.py)
Developer B: Phase 4 - US3 metrics.json (metrics_json.py)
Developer C: Phase 7 - US6 RFC (docs/rfcs/)

# After US2 complete:
Developer A: Phase 5 - US4 CLI display (formatters.py)

# All converge:
Phase 6 - US5 Cross-spec comparison validation
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: US1 — Mapping table update
3. **STOP and VALIDATE**: Run classifier tests, verify SP=8→L, SP=40→XL
4. This delivers the core value: corrected classification

### Incremental Delivery

1. Setup → Baseline established
2. US1 → Mapping corrected → **MVP!**
3. US2 → measure.json fixed → Data visible in outputs
4. US3 → metrics.json fixed → Entity details correct
5. US4 → CLI fixed → Terminal feedback works
6. US5 → Cross-spec comparison validated
7. US6 → RFC documented → **Complete**

### Quick Win Strategy

Since US2, US3, and US6 are all independent after US1, they can be completed in any order or simultaneously. US4 and US5 follow as quick validation steps.

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [Story] label maps task to specific user story for traceability
- The mapping change (US1) is the critical path — only 2 lines change in `DEFAULT_MAPPING`
- Payload fixes (US2) are additive — adding keys without removing existing ones
- The orchestrator key_map change (T015) is a one-line edit
- All existing contract tests must continue passing after the fix
- RFC documentation (US6) can be drafted in parallel with implementation

---

## Phase 9: Convergence

**Purpose**: Close gaps identified between specified intent and current implementation

- [X] T040 Fix hardcoded mapping metadata in `_build_metric_metadata()` at `specmetrics/application/metrics_json.py:330`: change `L: 8` to `L: 13` and `XL: 13` to `XL: 40` to reflect the highest Story Point value per range in the corrected DEFAULT_MAPPING per FR-005 (partial)
- [X] T041 Add cross-framework T-Shirt distribution comparison test (SpecKit vs OpenSpec fixtures) verifying < 20% difference per size category, or document as infeasible per US5/AC2 (missing) [REMOVED - test removed as infeasible without both SDD frameworks]
