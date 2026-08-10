# Research: Apply Quality Rules and Make the Quality Gate Pass

**Date**: 2026-08-04
**Input**: `specs/044-apply-quality-rules/spec.md` (044-apply-quality-rules) + `docs/plans/complexity-refactor-plan.md` + live gate output.

This research resolves the technical unknowns raised by the spec for making `make quality-gate` pass. Findings recorded as Decision / Rationale / Alternatives.

---

## R-1: Baseline — what is actually failing today

**Context**: The gate fails (`make quality-gate` → `make complexity` → xenon). Need an accurate, current inventory of failing blocks and modules to scope the work.

**Decision**: Measured live against the current tree (baseline recaptured 2026-08-04, T001):
- **48 blocks ranked C** (cyclomatic complexity > 10) via `xenon --max-absolute=B`. These are exclusively in `./specmetrics/` and `./scripts/`. Represented by radon lines `[CF] <file> <line> <name> - C (CCN)`. (48 is the live count at baseline; the 50 originally recorded at authoring time was superseded by the live run, which is authoritative for acceptance.)
- **30 modules ranked B or worse** (28 B + 2 C) via `xenon --max-modules=20`, exceeding the ceiling of 20. **At least 10 must be brought to Grade A** so the module count drops to ≤ 20. The 2 C-ranked modules (`factor_scorer.py`, `cli/commands/validate.py`) will drop to B once their C-blocks are resolved, so the module-count reduction targets the B-ranked modules.
- Average complexity is **B (8.52)**; with the C-blocks removed the average will drop below B, satisfying `--max-average=B`.
- Maintainability Index reported as **0** — this is a **parsing bug** in `scripts/complexity_metrics.py`, not a real reading (radon mi actually emits grades like `A (66.69)`); see R-4.

**Rationale**: Grounding every task in the measured list prevents guessing and lets the gate be used as the objective acceptance check (`xenon` must exit 0).

**Alternatives considered**: Guesstimating scope from the plan's Phase-3 table (44 rows) — superseded by the live count (50), which is authoritative.

---

## R-2: How to reduce the 50 C-blocks without behavior change

**Context**: FR-002/FR-015/SC-006 require CCN ≤ 10 per block, no public-signature or output changes, tests green.

**Decision**: Apply the plan's established refactoring patterns, per block, chosen by the source of complexity:
- **Dispatch table / Strategy** — the dominant pattern. Large `if/elif` chains keyed by type/stage/section (e.g., `DeterministicSemanticEngine._load_rules`, `_execute_rules`, `engine_visitors.*.visit`, `cfm/builder`, `csm/builder`, `PluginRegistry.register`, `PluginValidator.validate`, adapters' `_scan_with_result`, `cli/export_commands._run_pipeline_export`). Extract each branch to a private method and route via a module-level `_HANDLERS` dict.
- **Extract Method** — branchy bodies that are not type-keyed (e.g., `LLMGateway.complete`, `llm_provider.__init__/extract`, `_process_csm`, `compute_retention`, `validate`, `_format_metric`, `score_factor`). Split cohesive sub-steps into helpers.
- **Guard clauses** — functions with deep nesting (`match`, `build`, `explain`, `trace_element`, `validation/pipeline.run`): invert nested conditionals to early-return.
- **Postponed class-level C ranks** (e.g., `DeterministicSemanticEngine` class rank C 11): the class rank is the max of methods/props; resolving the C methods (`_load_rules`, `_execute_rules`, `_match_rule_against_observation`, `_load_framework_packs`) drops the class to B or better automatically.

**Rationale**: These are the exact patterns already validated in Phases 1–2 of the plan (`make test` 1219 passed) and are pure, verifiable restructuring.

**Alternatives considered**: Rewriting logic — rejected (behavior/risk); flattening via config — rejected (only applies to type-keyed blocks and would add indirection without reducing count).

---

## R-3: How to reduce modules ranked B-or-worse from 28 to ≤ 20

**Context**: Clarification 2026-08-04 enforces `--max-modules=20`. Xenon ranks a module by its worst block; a module ranks B if any block is B, and C/above if any block is ≥ C. The module rank is driven by the maximum block grade.

**Decision**: Module rank reduction is a **consequence of block reduction + worst-remaining-block trimming**:
1. Removing all 50 C-blocks automatically eliminates every module currently ranked C (those are the worst offenders). This alone drops the module count.
2. For modules that rank B due to a *single* B block, reduce that worst remaining block to A where cheap (its CCN is often 6–10, one small extraction) to push the module to A.
3. Priority: fix the worst per-module blocks first so each module crosses to A; target eliminating at least **8 B-ranked modules** in addition to the C-block cleanup to reach ≤ 20 of the 28 seen.

**Rationale**: Being selective — only required B-modules beyond the 8 needed — keeps scope bounded while satisfying the enforced ceiling. The 28 modules are enumerated in R-5.

**Alternatives considered**: Relaxing the ceiling — rejected by clarification (Option A). Blindly refactoring all 28 — unnecessary; only the surplus beyond 20 (≥ 8) is required for pass.

---

## R-4: Correct the Maintainability Index evaluation (MI < 30 blocking, 30–69 warning, ≥ 70 pass)

**Context**: FR-007 + clarification 2026-08-04. `scripts/complexity_metrics.py` currently:
- Parses `radon mi -s` output incorrectly: `mi_scores()` uses `\(([\d.]+)\)\s*$`, but radon emits `<path> - <grade> (<score>)` where parenthesized tokens appear mid-line followed by more content, so it returns an empty/min-0 and prints `[Warning] Maintainability Index 0 < 70`.
- Always returns `0` (`main()` → 0), i.e., MI can never block.

**Decision**:
1. Fix the parser to extract the trailing parenthesized score per line (e.g., regex `\((score)\)` anchored at the numeric-grade pattern `<grade> ([\d.]+)$`).
2. Update severity/exit semantics: if the worst MI < 30 → print `[Blocking] Maintainability Index < 30` and **return exit code 1** so `make complexity` fails; if 30 ≤ worst < 70 → `[Warning]`, exit 0; else `>= 70` pass, exit 0.
3. Align `scripts/quality_gate.py`'s model (severity enum) so a `blocking` MI record fails the gate; add an `MI` check entry.

**Rationale**: Matches the clarified severity contract and converts the currently-spurious 0 into truthful reporting.

**Alternatives considered**: Keeping MI pass-through 0 — rejected (would silently report a blocking MI as a warning); treating `radon mi` absence as skip — rejected (fail-loud per FR-014).

---

## R-5: Enumeration of the 28 B-or-worse modules and 50 C-blocks

**Context**: Scope breakdown for `tasks.md`.

**28 modules ranked B or worse (target ≤ 20):**
1. `specmetrics/kernel/engine_visitors.py`
2. `specmetrics/kernel/deterministic_engine.py`
3. `specmetrics/kernel/engine_patterns.py`
4. `specmetrics/kernel/graph_persistence.py`
5. `specmetrics/kernel/plugin_validation.py`
6. `specmetrics/kernel/explanation/service.py`
7. `specmetrics/kernel/explanation/comparison.py`
8. `specmetrics/kernel/validation/pipeline.py`
9. `specmetrics/kernel/validation/rules/constitutional.py`
10. `specmetrics/kernel/csm/evidence_processing.py`
11. `specmetrics/kernel/csm/activity_classifier.py`
12. `specmetrics/cli/measure.py`
13. `specmetrics/cli/plugins.py`
14. `specmetrics/cli/commands/explain.py`
15. `specmetrics/cli/commands/clean.py`
16. `specmetrics/mcp/tools/explain.py`
17. `specmetrics/mcp/tools/export.py`
18. `specmetrics/plugins/measurement/fpa/counter.py`
19. `specmetrics/plugins/measurement/snap/rule_applicator.py`
20. `specmetrics/plugins/measurement/snap/assessor.py`
21. `specmetrics/plugins/measurement/cognitive_points/calculator.py`
22. `specmetrics/plugins/measurement/storypoints/calibrator.py`
23. `specmetrics/plugins/rule_pack/validator.py`
24. `specmetrics/plugins/calibration/validator.py`
25. `specmetrics/plugins/calibration/loader.py`
26. `specmetrics/plugins/publisher/config.py`
27. `specmetrics/plugins/publisher/orchestrator.py`
28. `specmetrics/plugins/publisher/retry.py`

**50 C-ranked blocks** — enumerated at `research.md` time by radon lines of kind `[CF]` with rank C (see gate output). They concentrate in: kernel (`engine_visitors`, `llm_gateway.complete`, `deterministic_engine` ×5, `engine_patterns.match`, `graph_persistence.load`, `plugin_registry.register`, `plugin_validation.validate`, `csm/builder.build`, `cfm/builder` ×2, `explanation/service.explain`, `evidence_tracer.trace_element`, `explanation/formatters/text._format_metric`, `validation/pipeline.run`, `validation/rules/constitutional.constitution_engaged`), measurement plugins (`fpa/counter`, `snap/rule_applicator`, `cognitive_points` ×2, `storypoints` ×3, `bcp` ×3, `sfp/plugin`, `tshirt/classifier`), adapters (`speckit` + `openspec` `_scan_with_result`), `semantic/llm_provider` ×2, `calibration/loader.merge_calibration_data`, `exporter/xml_exporter.export`, `infrastructure/runs/cleaner.compute_retention`, `cli` (`measure`, `export_commands`, `config_commands` ×2, `commands/validate.validate`), `mcp/server._validate_tool_params`.

**Note**: The live `xenon` count (50) supersedes the plan doc's "48" (the plan table had 44 rows; the live run is authoritative for acceptance).

---

## R-6: Remaining metric thresholds (already correct — ratify, do not change)

**Context**: FR-005..FR-012 mapping to the Makefile.

**Decision**: Confirm the Makefile already enforces: coverage `--cov-fail-under=85` (blocking), mutation ≥ 80% via `scripts/mutatest_gate.py` (blocking), duplication `>10%` blocking / `7–10%` warning (jscpd), security High blocking / Medium warning (semgrep), lint blocking (ruff + flake8 `--max-complexity=10`), Halstead difficulty ≤ 20 / effort ≤ 150k / bugs ≤ 0.5 (warning/informational in `complexity_metrics.py`), lines/function ≤ 80 warning (lizard). No Makefile threshold changes are required except confirming `complexity`'s call to `complexity_metrics.py` no longer permits a blocking MI to pass.

**Rationale**: These match the spec/rules table exactly; churn here is unnecessary and risks regressions.

**Alternatives considered**: Re-deriving thresholds — rejected (already aligned).

---

## Unknowns remaining after research

None. All Technical Context `NEEDS CLARIFICATION` placeholders (block inventory, module-cap strategy, MI severity/exit, threshold wiring) are resolved above. Proceeding to Phase 1 design.