# Tasks: Measure Metrics Breakdown

**Input**: Design documents from `specs/036-measure-metrics-breakdown/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**Organization**: Tasks grouped by user story from spec.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core data models and builder infrastructure that ALL user stories depend on

**⚠️ CRITICAL**: No handler modification or CLI integration work can begin until this phase is complete

- [X] T001 [P] Add `MetricBreakdownEntry` and `EntityScore` Pydantic models with `CanonicalEntityType` Literal to `specmetrics/application/models.py`
- [X] T002 [P] Add `measurement_result_raw: dict` field to `PipelineResult` dataclass in `specmetrics/application/models.py`
- [X] T003 Populate `PipelineResult.measurement_result_raw` from `ctx.measurement_result` in orchestrator `execute()` at `specmetrics/application/orchestrator.py:277`
- [X] T004 [P] Create canonical type mapping constants (`FPA_TYPE_MAP`, `SFP_TYPE_MAP`, `SNAP_TYPE_MAP`, `METRIC_UNIT_MAP`) in `specmetrics/application/metrics_json.py`
- [X] T005 [P] Create `EntityScoreBuilder` class with per-metric build methods (build_fpa_entity, build_sfp_entity, build_snap_entity, build_bcp_entity, build_storypoints_entity, build_tokenpoints_entity, build_cognitive_entity, build_tshirt_entity) in `specmetrics/application/metrics_json.py`
- [X] T006 Create `MetricBreakdownBuilder.build_all()` that reads `measurement_result_raw` dict and produces `list[MetricBreakdownEntry]` in `specmetrics/application/metrics_json.py`
- [X] T007 Create `save_metrics_json(project_path, measure_id, result)` function that writes `metrics.json` with UTF-8 pretty-printed JSON in `specmetrics/application/metrics_json.py`

**Checkpoint**: Foundation ready — handler modifications and CLI integration can now begin

---

## Phase 2: User Story 1 + 2 - Generate metrics.json with Uniform Schema (Priority: P1) 🎯 MVP

**Goal**: After running `specmetrics measure`, `metrics.json` exists with per-entity breakdown for all executed metrics, using the identical top-level and entity-level keys across all metric types.

**Independent Test**: Run `specmetrics measure --metrics all` and verify `runs/<measure_id>/metrics.json` contains entries for all 8 metrics with uniform schema. Run `--metrics fpa,sp` and verify only fpa and sp entries appear.

### Entity Serialization in Handlers (can run in parallel)

- [X] T008 [P] [US1] Add `fpa_entities` list to payload in `FPAMeasurementHandler.handle()` at `specmetrics/plugins/measurement/fpa/plugin.py:111`
- [X] T009 [P] [US1] Add `sfp_entities` list to payload in `SFPMeasurementHandler.handle()` at `specmetrics/plugins/measurement/sfp/plugin.py`
- [X] T010 [P] [US1] Add `snap_entities` list to payload in `SNAPMeasurementHandler.handle()` at `specmetrics/plugins/measurement/snap/plugin.py`
- [X] T011 [P] [US1] Add `bcp_entities` list to payload in `BCPHandler.handle()` at `specmetrics/plugins/measurement/bcp/plugin.py`
- [X] T012 [P] [US1] Add `storypoints_entities` list to payload in `StoryPointsHandler.handle()` at `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T013 [P] [US1] Add `token_entities` list to payload in `TokenPointsHandler.handle()` at `specmetrics/plugins/measurement/token_points/plugin.py`
- [X] T014 [P] [US1] Add `cognitive_entities` list to payload in `CognitivePointsHandler.handle()` at `specmetrics/plugins/measurement/cognitive_points/plugin.py`
- [X] T015 [P] [US1] Add `tshirt_entities` list to payload in `TShirtHandler.handle()` at `specmetrics/plugins/measurement/tshirt/plugin.py`

### CLI Integration

- [X] T016 [US1] Import and call `save_metrics_json()` after `save_run_artifacts()` in `run_measure()` at `specmetrics/cli/measure.py:198`

### Uniform Schema Verification

- [X] T017 [US2] Implement schema validation in `MetricBreakdownBuilder` — ensure all entries have `name`, `metric`, `total`, `unit`, `entity_count`, `entities`, `status`; all entities have `id`, `name`, `type`, `score` in `specmetrics/application/metrics_json.py`
- [X] T018 [US2] Implement canonical type validation in `EntityScoreBuilder` — ensure entity `type` is one of the 14 `CanonicalEntityType` values in `specmetrics/application/metrics_json.py`

**Checkpoint**: metrics.json generated with correct uniform schema for all metrics — MVP ready

---

## Phase 3: User Story 3 - Explainability Through Entity Metadata (Priority: P2)

**Goal**: Each entity's `metadata` object contains sufficient context to understand why the entity received its score (complexity ratings, factor breakdowns, bloom levels, weights).

**Independent Test**: Open `metrics.json` for FPA — verify entities have `function_type`, `complexity`, and count fields in metadata. For Story Points — verify `raw_score`, `normalized_value`, and `factor_breakdown` are present.

- [X] T019 [P] [US3] Enrich FPA entity metadata with `function_type`, `complexity`, `det_count`, `ret_count`/`ftr_count` in `specmetrics/plugins/measurement/fpa/plugin.py`
- [X] T020 [P] [US3] Enrich SFP entity metadata with `component_type` in `specmetrics/plugins/measurement/sfp/plugin.py`
- [X] T021 [P] [US3] Enrich SNAP entity metadata with `category_id`, `cfm_semantic_marker` in `specmetrics/plugins/measurement/snap/plugin.py`
- [X] T022 [P] [US3] Enrich BCP entity metadata with `component_breakdown`, `generated_story` in `specmetrics/plugins/measurement/bcp/plugin.py`
- [X] T023 [P] [US3] Enrich Story Points entity metadata with `raw_score`, `normalized_value`, `factor_breakdown`, `applied_rules` in `specmetrics/plugins/measurement/storypoints/plugin.py`
- [X] T024 [P] [US3] Enrich Token Points entity metadata with `applied_weight`, `model_source`, `element_type` in `specmetrics/plugins/measurement/token_points/plugin.py`
- [X] T025 [P] [US3] Enrich Cognitive Points entity metadata with `bloom_level`, `cognitive_weight`, `model_source` in `specmetrics/plugins/measurement/cognitive_points/plugin.py`
- [X] T026 [P] [US3] Enrich TShirt entity metadata with `tshirt_size`, `mapping_rule` in `specmetrics/plugins/measurement/tshirt/plugin.py`

**Checkpoint**: All entity metadata populated — entities are self-explanatory without consulting source files

---

## Phase 4: User Story 4 - Integration with Existing Run Artifacts (Priority: P2)

**Goal**: `metrics.json` coexists with existing run artifacts without breaking the export command or modifying existing files.

**Independent Test**: Run `specmetrics measure`, verify `metadata.json`, `measure.json`, and all stage JSON files are unchanged. Run `specmetrics export run <measure_id> --format json` and verify export succeeds.

- [X] T027 [US4] Verify `save_run_artifacts()` in `specmetrics/application/orchestrator.py:114` is NOT modified — metrics.json is written by separate function
- [X] T028 [US4] Verify `_run_auto_export()` in `specmetrics/cli/measure.py:44` handles presence of `metrics.json` without errors — exclude it from copy loop if needed
- [X] T029 [US4] Verify `read_run_artifacts()` in `specmetrics/application/orchestrator.py:148` ignores `metrics.json` (only reads stage files via glob pattern)
- [X] T030 [US4] Handle edge case: write `metrics.json` with `status: "failed"` and `errors` array when `measurement_result_raw` is missing or empty in `specmetrics/application/metrics_json.py`
- [X] T031 [US4] Handle edge case: ensure metrics not selected via `--metrics` filter produce no entry (absent from array, not empty entry) in `specmetrics/application/metrics_json.py`

**Checkpoint**: metrics.json is a non-disruptive addition to the run directory

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Tests, validation, and final verification

- [X] T032 [P] Create unit tests for `EntityScoreBuilder` per-metric build methods in `tests/test_metrics_json.py`
- [X] T033 [P] Create unit tests for `MetricBreakdownBuilder.build_all()` with mock `measurement_result_raw` in `tests/test_metrics_json.py`
- [X] T034 [P] Create integration test: run `specmetrics measure` on a fixture project and validate `metrics.json` schema in `tests/test_metrics_json.py`
- [X] T035 [P] Create integration test: verify `--metrics fpa,sp` filter produces only fpa and sp entries in `tests/test_metrics_json.py`
- [X] T036 [P] Create edge case test: empty project produces valid metrics.json with entity_count=0 in `tests/test_metrics_json.py`
- [X] T037 [P] Create edge case test: missing `measurement_result_raw` produces error entry in `tests/test_metrics_json.py`
- [X] T038 Run quickstart.md validation scenarios 1-8 and confirm all pass
- [X] T039 Run `ruff check` and `ruff format` on all changed files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — can start immediately
- **US1 + US2 (Phase 2)**: Depends on Phase 1 completion — BLOCKS MVP
- **US3 (Phase 3)**: Depends on Phase 2 (handlers must be emitting entities before metadata can be enriched)
- **US4 (Phase 4)**: Depends on Phase 2 (metrics.json must exist before integration can be validated)
- **Polish (Phase 5)**: Depends on all user story phases

### User Story Dependencies

- **US1 + US2 (P1)**: Combined phase — both depend on Foundational only. US2's schema validation tasks (T017, T018) can run after builder is implemented.
- **US3 (P2)**: Can start after US1 handler tasks (T008-T015) — enriches payloads that handlers already emit
- **US4 (P2)**: Can start after Phase 2 CLI integration (T016) — validates integration

### Within Each Phase

- Phase 1: T001, T002, T004 can run in parallel; T003 depends on T002; T005-T007 depend on T001+T004
- Phase 2: T008-T015 (all 8 handlers) can run in parallel; T016 depends on any one handler being ready; T017-T018 depend on T005-T006
- Phase 3: T019-T026 (all 8 handlers) can run in parallel
- Phase 4: T027-T031 can run in any order
- Phase 5: T032-T037 (all tests) can run in parallel; T038-T039 run sequentially after

### Parallel Opportunities

- 8 handler modifications (T008-T015) all touch different files — fully parallel
- 8 metadata enrichment tasks (T019-T026) all touch different files — fully parallel
- All test tasks (T032-T037) — fully parallel
- US3 and US4 phases can proceed in parallel if team capacity allows

---

## Parallel Example: Handler Entity Serialization (Phase 2)

```bash
# All 8 handler modifications touch different files — launch together:
Task: "Add fpa_entities list to payload in specmetrics/plugins/measurement/fpa/plugin.py"
Task: "Add sfp_entities list to payload in specmetrics/plugins/measurement/sfp/plugin.py"
Task: "Add snap_entities list to payload in specmetrics/plugins/measurement/snap/plugin.py"
Task: "Add bcp_entities list to payload in specmetrics/plugins/measurement/bcp/plugin.py"
Task: "Add storypoints_entities list to payload in specmetrics/plugins/measurement/storypoints/plugin.py"
Task: "Add token_entities list to payload in specmetrics/plugins/measurement/token_points/plugin.py"
Task: "Add cognitive_entities list to payload in specmetrics/plugins/measurement/cognitive_points/plugin.py"
Task: "Add tshirt_entities list to payload in specmetrics/plugins/measurement/tshirt/plugin.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Foundational (models, builder, PipelineResult)
2. Complete Phase 2: US1 + US2 (handler entities + CLI integration)
3. **STOP and VALIDATE**: Run `specmetrics measure --metrics all` on a test project, verify `metrics.json` exists with all entries
4. Run quickstart scenarios 1-3, 5, 7

### Incremental Delivery

1. Foundational → Models and builder ready
2. Add US1+US2 → metrics.json generated with uniform schema (MVP!)
3. Add US3 → Entities carry full explainability metadata
4. Add US4 → Verified integration with existing artifacts
5. Polish → Tests and validation complete

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 together (models + builder)
2. Once Foundational is done:
   - Developer A: FPA + SFP + SNAP + BCP handlers (T008-T011, T019-T022)
   - Developer B: Story Points + Token Points + Cognitive Points + TShirt handlers (T012-T015, T023-T026)
   - Developer C: MetricsJsonBuilder + CLI integration (T005-T007, T016-T018)
3. US3 and US4 can be done by same developers in parallel after Phase 2

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- T008-T015 (handler entity serialization) and T019-T026 (metadata enrichment) may be done in the same edit per handler rather than two separate touches — the split reflects the two user stories they serve
- The `entity_count` field MUST equal `len(entities)` — this is enforced by the builder
- All entity `id` values MUST use compound URI format `source_model:category:element_name`
- Failed BCP items are NOT included in entities array — only successful items appear
- The `metrics.json` file is NOT listed in `pyproject.toml` or entry points — it's a run artifact, not a plugin

---

## Phase 6: Convergence

**Purpose**: Close gaps identified by `/speckit.converge` after initial implementation.

- [X] T040 Extract metric-specific warning keys (bcp_warnings, storypoints_warnings, token_warnings, cognitive_warnings) from `measurement_result_raw` and populate `MetricBreakdownEntry.warnings` per US1/AC3 (partial)
- [X] T041 Add `field_validator` on `EntityScore.id` to enforce compound URI pattern `<source_model>:<category>:<name>` where `source_model` is `cfm` or `csm` per FR-004 (partial)
- [X] T042 Add `fpa_vaf` to FPA handler payload at `specmetrics/plugins/measurement/fpa/plugin.py` from `result.summary.vaf` per plan: metadata table (partial)
- [X] T043 Extract `sfp_breakdown` from `measurement_result_raw` and include `fp_contribution`/`lf_contribution` in SFP metric metadata per plan: metadata table (partial)
- [X] T044 Extract `snap_by_category` from `measurement_result_raw` and include `categories` list in SNAP metric metadata per plan: metadata table (partial)
