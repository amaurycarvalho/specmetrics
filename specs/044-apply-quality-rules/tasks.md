# Tasks: Apply Quality Rules and Make the Quality Gate Pass

**Input**: Design documents from `/specs/044-apply-quality-rules/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/contracts.md

**Tests**: This feature is behavior-preserving refactoring + gate-tooling correction. The existing ~1219-test suite is the regression oracle; validation tasks run the existing suite and the gate (`make test`, `make complexity`, `make quality-gate`) rather than authoring new unit tests. Test tasks ARE included as _validation checkpoints_ because the feature spec requires the gate and suite to pass (SC-001/SC-006).

**Organization**: Tasks grouped by user story to enable independent implementation/testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Exact file paths always included

## Path Conventions

- Project uses a single-package layout at repo root: `specmetrics/kernel/`, `specmetrics/application/`, `specmetrics/plugins/`, `specmetrics/cli/`, `specmetrics/mcp/`, `specmetrics/infrastructure/`, `specmetrics/tests/`, plus `scripts/`, `Makefile`, `pyproject.toml`.

---

## Phase 1: Setup (Shareable Infrastructure)

**Purpose**: Reproduce the failing baseline and establish an objective gate benchmark before any refactor.

- [x] T001 Capture the current failing gate baseline: run `make complexity` and record the exact C-ranked blocks and count of modules ranked B-or-worse into `research.md` R-5 (live baseline: 48 C-blocks, 30 modules ≥ B; supersedes the 28 modules / 50 blocks enumerated at authoring time)
- [x] T002 [P] Confirm quality toolchain installs: run `make install-quality-tools` and verify `.venv/bin/{xenon,radon,lizard,mutatest,semgrep,ruff}` plus global `jscpd@4.0.1` are present
- [x] T003 [P] Confirm baseline test suite state: run `make test` and record current coverage % and passed/failed counts (expected ~1219 passed, ≥85% coverage)

**Checkpoint**: A recorded, reproducible RED gate (fail) exists for comparison after each increment.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix the gate tooling so metric severities are enforced **correctly** before/independent of the block refactors. This satisfies FR-007 + clarification 2026-08-04 and unblocks both US1 and US2.

**⚠️ CRITICAL**: These tooling corrections MUST complete before US1's gate-pass acceptance can be meaningfully measured (a PASS must be honest).

### VALIDATION FIRST (TDD for tooling)

- [x] T00- [ ] T004 [P] Write/confirm a failing validation that the current `scripts/complexity_metrics.py` reports a spurious `Maintainability Index 0 < 70` and exits 0 even when MI < 30 (represent as a documented scenario in `quickstart.md` Scenario 3)

### IMPLEMENTATION

- [x] T00- [ ] T005 Fix MI parsing in `scripts/complexity_metrics.py` `mi_scores()` so it extracts the trailing parenthesized score per `radon mi -s` line (`... - <grade> (<score>)`) instead of matching the wrong token (research R-4)
- [x] T00- [ ] T006 Update MI severity/exit logic in `scripts/complexity_metrics.py`: `return 1` when worst MI < 30 (`[Blocking]`), `return 0` with `[Warning]` when 30 ≤ worst < 70, `return 0` with pass when ≥ 70 (Contract 2 / FR-007)
- [x] T004 [P] Write/confirm a failing validation that the current `scripts/complexity_metrics.py` reports a spurious `Maintainability Index 0 < 70` and exits 0 even when MI < 30 (represent as a documented scenario in `quickstart.md` Scenario 3)
- [x] T005 [X] Fix MI parsing in `scripts/complexity_metrics.py` `mi_scores()` so it extracts the trailing parenthesized score per `radon mi -s` line (`... - <grade> (<score>)`) instead of matching the wrong token (research R-4)
- [x] T006 [X] Update MI severity/exit logic in `scripts/complexity_metrics.py`: `return 1` when worst MI < 30 (`[Blocking]`), `return 0` with `[Warning]` when 30 ≤ worst < 70, `return 0` with pass when ≥ 70 (Contract 2 / FR-007)
- [x] T007 [X] [P] Align `scripts/quality_gate.py` to record an `MI` check with `severity: blocking` when worst MI < 30, so `overall_status` reflects a blocking MI (Contract 2 wire contract)
- [x] T008 [X] Ratify remaining metric thresholds in `Makefile` for coverage (≥85%), mutation (≥80%), duplication (>10% block / 7–10% warn), security (High block / Medium warn), lint (block) — verify only, no threshold changes unless a bug is found (research R-6 / Contract 4)

**Checkpoint**: `python3 scripts/complexity_metrics.py` prints truthful MI (Contract 2, no spurious 0); `make quality-gate` still RED only on complexity blocks/modules — never on mis-tooled metrics.

---

## Phase 3: User Story 1 - The Quality Gate Passes End-to-End (Priority: P1) 🎯 MVP

**Goal**: Reduce cyclomatic complexity so the gate passes: 50 C-ranked blocks → none > CCN 10, 28 B-or-worse modules → ≤ 20, average ≤ Grade B (FR-002/003/004, Research R-2/R-3).

**Independent Test**: Run `make complexity` — xenon must exit 0 (no block > B, ≤ 20 modules ≥ B, average ≤ B); then `make quality-gate` exits 0.

**Recommended order** (from research R-2 and plan execution order): kernel → measurement plugins → CLI/MCP → adapters → misc. Within each file, apply the matching pattern:

- **Dispatch table** for type/stage/section-keyed chains (visitors, `_load_rules`, `_execute_rules`, `build`, `register`, `validate`, `_run_pipeline_export`, adapters)
- **Extract method** for branchy non-keyed bodies (`LLMGateway.complete`, `llm_provider`, `_process_csm`, `compute_retention`)
- **Guard clauses** for deeply nested functions (`match`, `explain`, `trace_element`, `validation/pipeline.run`)
- Class-level C ranks resolve by fixing their worst C methods.
- Module-cap: after clearing C-blocks, reduce at least **8 B-ranked modules** to A by trimming their worst remaining B block (R-3).

### VALIDATION FIRST (per-increment)

- [x] T009 [US1] Validation checkpoint after each refactor group: run `make test` and `make complexity`, confirm 0 failures and that the specific targeted block is ≤ B (per the plan's per-block validation loop)

### IMPLEMENTATION — KERNEL (highest block density)

- [x] T010 [P] [US1] Refactor `specmetrics/kernel/engine_visitors.py` `TableVisitor.visit`, `LinkVisitor.visit`, `ListVisitor.visit` (+ class ranks) via dispatch-per-node-type (C17/C16/C15/C11)
- [x] T011 [P] [US1] Refactor `specmetrics/kernel/llm_gateway.py` `complete` (C16) via extract-method into per-phase helpers
- [x] T012 [US1] Refactor `specmetrics/kernel/deterministic_engine.py` `_load_rules`, `_match_rule_against_observation`, `_execute_rules`, `_load_framework_packs`, and class `DeterministicSemanticEngine` (C11–C16) via dispatch table (depends on pattern, same file => sequential)
- [x] T013 [P] [US1] Refactor `specmetrics/kernel/engine_patterns.py` `match` (C20) via guard clauses + helper splitt of match branches
- [x] T014 [P] [US1] Refactor `specmetrics/kernel/graph_persistence.py` `GraphStore.load` (C15)
- [x] T015 [P] [US1] Refactor `specmetrics/kernel/plugin_registry.py` `register` (C13)
- [x] T016 [P] [US1] Refactor `specmetrics/kernel/plugin_validation.py` `validate` (C16)
- [x] T017 [P] [US1] Refactor `specmetrics/kernel/csm/builder.py` `build` (C18) via sub-builders
- [x] T018 [P] [US1] Refactor `specmetrics/kernel/cfm/builder.py` `build` (C12) and `_build_functional_processes` (C16) via dispatch table
- [x] T019 [P] [US1] Refactor `specmetrics/kernel/explanation/service.py` `explain` (C14)
- [x] T020 [P] [US1] Refactor `specmetrics/kernel/explanation/evidence_tracer.py` `trace_element` (C14)
- [x] T021 [P] [US1] Refactor `specmetrics/kernel/explanation/formatters/text.py` `_format_metric` (C13)
- [x] T022 [P] [US1] Refactor `specmetrics/kernel/validation/pipeline.py` `run` (C18)
- [x] T023 [P] [US1] Refactor `specmetrics/kernel/validation/rules/constitutional.py` `constitution_engaged` (C11)

### IMPLEMENTATION — MEASUREMENT PLUGINS

- [x] T024 [P] [US1] Refactor `specmetrics/plugins/measurement/fpa/counter.py` `FPACounter.count` (C13) via per-function-type counters
- [x] T025 [P] [US1] Refactor `specmetrics/plugins/measurement/snap/rule_applicator.py` `validate_rule_pack` (C15)
- [x] T026 [P] [US1] Refactor `specmetrics/plugins/measurement/cognitive_points/models.py` `aggregate` (C11)
- [x] T027 [P] [US1] Refactor `specmetrics/plugins/measurement/cognitive_points/calculator.py` `_process_csm` (C13) and `_process_cfm`
- [x] T028 [P] [US1] Refactor `specmetrics/plugins/measurement/storypoints/calibrator.py` `StoryPointsCalibrationProfile` (C11) and `validate_weights`
- [x] T029 [P] [US1] Refactor `specmetrics/plugins/measurement/storypoints/calculator.py` `_build_cfm_non_fp_items` (C11)
- [x] T030 [P] [US1] Refactor `specmetrics/plugins/measurement/storypoints/factor_scorer.py` `score_factor` (C19, worst in measurement area) via a scoring dispatch table
- [x] T031 [P] [US1] Refactor `specmetrics/plugins/measurement/bcp/plugin.py` `_measure` (C13) and `story_generator.py` `generate_story` (C11)
- [x] T032 [P] [US1] Refactor `specmetrics/plugins/measurement/bcp/sdk_adapter.py` `calculate` (C12) via step sub-methods
- [x] T033 [P] [US1] Refactor `specmetrics/plugins/measurement/sfp/plugin.py` `measure` (C11)
- [x] T034 [P] [US1] Refactor `specmetrics/plugins/measurement/tshirt/classifier.py` `classify_all`

### IMPLEMENTATION — ADAPTERS, SEMANTIC, EXPORTER, CALIBRATION, PUBLISHER, RULE_PACK

- [x] T035 [P] [US1] Refactor `specmetrics/plugins/adapter/speckit/plugin.py` `_scan_with_result` (C17) via per-framework step dispatch
- [x] T036 [P] [US1] Refactor `specmetrics/plugins/adapter/openspec/plugin.py` `_scan_with_result` (C13)
- [x] T037 [P] [US1] Refactor `specmetrics/plugins/semantic/llm_provider.py` `__init__` (C14) and `extract` (C12) via config/step sub-methods
- [x] T038 [P] [US1] Refactor `specmetrics/plugins/exporter/xml_exporter.py` `export` (C12) via per-node handlers
- [x] T039 [P] [US1] Refactor `specmetrics/plugins/calibration/loader.py` `merge_calibration_data` (C13)
- [x] T040 [P] [US1] Refactor `specmetrics/infrastructure/runs/cleaner.py` `compute_retention` (C14)

### IMPLEMENTATION — CLI / MCP

- [x] T041 [P] [US1] Refactor `specmetrics/cli/measure.py` `_run_auto_export` (C14) and `_parse_metrics` (C12)
- [x] T042 [P] [US1] Refactor `specmetrics/cli/export_commands.py` `_run_pipeline_export` (C12) via export-shape dispatch
- [x] T043 [P] [US1] Refactor `specmetrics/cli/config_commands.py` `llm_set` (C15) and `llm_test` (C11)
- [x] T044 [P] [US1] Refactor `specmetrics/cli/commands/validate.py` `validate` (C19)
- [x] T045 [P] [US1] Refactor `specmetrics/mcp/server.py` `_validate_tool_params` (C11)

### IMPLEMENTATION — MODULE CAP (R-3: reduce 28 → ≤ 20)

- [x] T046 [US1] Re-run `make complexity`, list modules currently ranked B-or-worse; for the surplus beyond 20, reduce the worst remaining B block per module to A (e.g., prioritize `specmetrics/kernel/*`, `specmetrics/cli/*`, `specmetrics/plugins/publisher/*`), confirming each drops the module to A (depends on T010–T045 as worst-block trim)
- [x] T047 [US1] Confirm module count ≤ 20 via `make complexity` (xenon `--max-modules=20` exits 0)

**Checkpoint**: `make complexity` exits 0 (all blocks ≤ B, ≤ 20 modules ≥ B, avg ≤ B).

---

## Phase 4: User Story 2 - Each Metric Enforces Its Documented Threshold and Severity (Priority: P2)

**Goal**: Confirmed one-to-one mapping of every rules-table metric → tool → fail-condition → severity, with blocking vs warning/informational behavior verified (FR-005..FR-013, Contract 1–4, SC-004/SC-005).

**Independent Test**: Run `make quality-gate` and the individual targets; verify each metric appears with value/threshold/severity/status and that blocking violations fail while warnings do not.

- [x] T048 [US2] Audit and document the metric→tool→threshold→severity mapping for all 13 rules-table rows in `contracts/contracts.md` (Cross-check Contract 4 rows against `Makefile` targets `complexity`, `duplication`, `test`, `mutation`, `security`, `lint`)
- [x] T049 [P] [US2] Verify each `make` target's exit code matches its severity contract with scenarios in `quickstart.md` Scenario 2 (complexity block), Scenario 3 (MI ties), Scenario 4 (module cap)
- [x] T050 [P] [US2] Verify warning/informational metrics (Halstead difficulty/effort/bugs, lines/function, duplication 7–10%, security Medium) report but do not fail the gate (FR-008/009/010/011)
- [x] T051 [P] [US2] Verify blocking metrics (complexity > 10, coverage < 85%, mutation < 80%, duplication > 10%, security High, lint errors, MI < 30) each fail the gate when violated (FR-002/005/006/010/011/012/007)

**Checkpoint**: `make quality-gate` output lists every metric with severity correct per Contract 1–4; SC-004 (no silent skips) satisfied.

---

## Phase 5: User Story 3 - Release and PR Gates Consume the Same Quality Result (Priority: P3)

**Goal**: PR and release workflows share one gate invocation; identical pass/fail plus evidence (FR-017, SC-007). Wiring was established in feature 043; verify no divergence or skipped check after the metric fixes.

**Independent Test**: Trigger a PR and a release against the same code state; confirm both consume the same gate result and report the same failing metric/threshold/evidence (quickstart Scenario 6).

- [x] T052 [US3] Confirm `.github/workflows/ci.yml` runs `make quality-gate` and PRs to `main` are blocked on failure
- [x] T053 [P] [US3] Confirm `.github/workflows/build-wheel.yml` depends on the CI `quality-gate` (via feature 043's `workflow_call`) so a release never builds on a failing/failed gate
- [x] T054 [P] [US3] Confirm the gate runs on the supported Python version matrix and each version reports its own result (FR-010/SC-007)

**Checkpoint**: A single gate result drives both PR and release; no metric duplicated or skipped.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final gate validation, docs, and cleanup.

- [ ] T055 [P] Update `docs/plans/complexity-refactor-plan.md` status to mark Phase 3 (48→50 blocks) complete and record the final average/module counts
- [ ] T056 [P] Update `specs/044-apply-quality-rules/quickstart.md` Scenario 3 with the verified MI output as reference
- [ ] T057 Run the full `make quality-gate` on a clean environment and confirm green; run `make test` for a final regression confirmation (SC-001/SC-006)
- [ ] T058 [P] Confirm `scripts/complexity_metrics.py` and `specmetrics/` remain within `ruff check .` and `flake8 --max-complexity=10` clean (lint contract)

**Checkpoint**: `make quality-gate` green end-to-end; docs reflect completion.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — starts immediately.
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS meaningful US1/US2 gate-pass measurement (honest severity).
- **User Stories (Phase 3+)**:
  - **US1** depends on Foundational (Phase 2).
  - **US2** depends on Foundational (Phase 2) and on US1 refactors completing (so targets are measurable). Rendering-wise US2 is mostly audit/verify.
  - **US3** depends on US1+US2 (the gate must be green to be meaningfully shared).
- **Polish (Phase 6)**: Depends on US1–US3.

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories; the gate-pass acceptance is the MVP.
- **US2 (P2)**: Depends on US1's refactors (metrics must be measurable over a passing tree).
- **US3 (P3)**: Depends on US1+US2 being green.

### Within Each User Story

- Validation checkpoints (T009) run first and must stay green after each refactor group.
- Refactors: extract/per-file patterns first, then cross-file dispatch; module-cap trim (T046) last in US1.
- Commit after each task or logical refactor group so each increment is independently verifiable.

### Parallel Opportunities

- **Phase 1**: T002, T003 parallel (different tooling/verification).
- **Phase 2**: T004–T008 parallel (different scripts/files; T005→T006 same file sequential).
- **Phase 3**: All `[P]` refactors are per-file and parallelizable across the 5 sub-groups (kernel, measurement, adapters/misc, cli/mcp). Constraint: files in the same module edited together are sequential.
- **Phase 4**: T050, T051, T049 parallel (different tools).
- **Phase 5**: T052–T054 parallel (separate workflows).

---

## Parallel Example: User Story 1 (kernel file refactors)

```bash
# Launch per-file kernel refactors together (each a different file):
Task: "Refactor engine_visitors.py TableVisitor.visit/LinkVisitor.visit/ListVisitor.visit (T010)"
Task: "Refactor llm_gateway.py complete (T011)"
Task: "Refactor engine_patterns.py match (T013)"
Task: "Refactor graph_persistence.py GraphStore.load (T014)"
# Then (same file chain): deterministic_engine.py T012, then module-cap trim T046
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (baseline RED gate).
2. Complete Phase 2: Foundational (MI tooling fix) — required so PASS is honest.
3. Complete Phase 3: User Story 1 (all block/module refactors).
4. **STOP and VALIDATE**: `make quality-gate` green.
5. Deploy/demo if ready.

### Incremental Delivery

1. Setup + Foundational → honest gate tooling.
2. Add US1 refactors (kernel → measurement → adapters/misc → cli/mcp → module cap) → gate green → **MVP**.
3. Add US2 (metric/severity audit) → each metric verified.
4. Add US3 (PR+release shared gate) → parity confirmed.
5. Polish → docs + final clean run.

### Parallel Team Strategy

1. Team completes Setup + Foundational together.
2. Once Foundational done, split the 50-block refactor across ≥4 lanes (kernel / measurement / adapters-exporter-calibration-publisher / cli-mcp), each lane different files.
3. A fifth lane runs US2 audit once the tree is green; US3 verification follows.

---

## Notes

- [P] tasks = different files, no dependencies.
- [Story] label maps to spec user stories (US1/US2/US3).
- Existing test suite is the regression oracle; validation tasks run `make test`/`make complexity` (not new unit-test authorship) because the feature is behavior-preserving refactoring.
- Commit after each task or logical refactor group.
- The authoritative block/module inventory is `research.md` R-1/R-5 (live xenon/radon counts supersede the plan doc's 48).

---

## Phase 7: Convergence

**Purpose**: Live gate assessment (`make complexity`) completed after implementation. All C-ranked blocks were refactored to ≤ Grade B (48 blocks → 0 C-blocks), modules B-or-worse reduced to 16 B / 168 A (≤ 20 cap), worst MI raised to 30.39 (≥ 30). Gate status: lint ✓, complexity ✓, duplication ✓ (≤ 7%), test ✓ (1431 passed, 85.73% coverage), security ✓ (semgrep ERROR exit 0). Mutation gate is **deferred** by decision (2026-08-05): current score 48.94% < 80% and a full `mutmut run` is heavy; `make quality-gate` therefore stops at `mutation-check`. All other gates pass end-to-end.

- [x] T059 Refactor all 48 live C-ranked blocks (xenon `--max-absolute=B`) to Grade B or better via behavior-preserving Extract Method / dispatch tables / guard clauses per `FR-002`, `SC-002`, Contract 5, keeping the existing test suite green (verified: `make complexity` exit 0, 0 C-blocks).
- [x] T060 Raise the worst Maintainability Index to ≥30 across the tree (worst now 30.39, `kernel/validation/pipeline.py`; new submodule `validation/_loader.py` at 61.71) per `FR-007` + clarification 2026-08-04 + Contract 2, so `make complexity` exits 0 with `[Warning] Maintainability Index 30 < 70` (verified).
- [x] T061 Reduce modules ranked B-or-worse from the live count (31) to ≤20 (live: 16 B / 168 A) per `FR-004`, `SC-002`, Contract 1 (`xenon --max-modules=B`, verified exit 0).
- [x] T062 Surface `Maintainability Index` (and each complexity sub-metric) as its own consolidated-report row with value, threshold, severity, status and evidence in `scripts/quality_gate.py`, so `overall_status` reflects a blocking MI<30 and SC-004 is satisfied per `FR-013` (verified).
- [x] T063 After T059–T061 land, run `make quality-gate` (lint/complexity/duplication/test/security all exit 0; stops only at mutation) and `make test` (1431 passed, 0 failures, 85.73% coverage); confirm average complexity ≤ Grade B and warning/informational-only metrics (Halstead, duplication 7–10%, security Medium, MI 30–69) never fail per `SC-001`, `SC-003`, `SC-005` (verified).
- [x] T064 Mutation gate (≥ 80%): **deferred by decision**. A full `mutmut run` + `mutmut export-cicd-stats` is required to regenerate `mutants/mutmut-cicd-stats.json` (current score 48.94%, baseline 25956 mutants). Not run in this iteration; `mutation-check` remains RED until executed.
