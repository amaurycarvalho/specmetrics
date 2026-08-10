# Implementation Plan: Apply Quality Rules and Make the Quality Gate Pass

**Branch**: `044-apply-quality-rules` | **Date**: 2026-08-04 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/044-apply-quality-rules/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Make `make quality-gate` pass end-to-end by (1) bringing the codebase under the documented quality thresholds and (2) fixing gate tooling so every metric is enforced with the correct severity. The gate currently fails on **50 rank-C blocks** (cyclomatic complexity > 10) in the `./specmetrics/` and `./scripts/` trees, and on **28 modules ranked Grade B or worse**, exceeding the enforced `--max-modules=20` ceiling (clarification 2026-08-04). Both must be reduced with behavior-preserving refactors (Extract Method, dispatch tables, guard clauses) so no block exceeds CCN 10, the average stays ≤ Grade B, and no more than 20 modules rank B or worse. Separately, the `scripts/complexity_metrics.py` MI evaluation is parsed incorrectly (reports a spurious 0); it must be fixed and aligned so MI < 30 is blocking, 30 ≤ MI < 70 is a warning, and MI ≥ 70 passes (clarification 2026-08-04). Coverage (≥85%), mutation (≥80%), duplication (≤7% pass / 7–10% warn / >10% block), security (High block / Medium warn) and lint (block) thresholds are already correctly wired in the Makefile and remain as the enforcement baseline.

## Technical Context

**Language/Version**: Python 3.12/3.13 (project runtime exercised in CI). The feature is behavior-preserving refactoring of existing Python modules plus correction of two gate scripts — no new runtime feature.

**Primary Dependencies**: Existing quality tooling already present in the `quality` extra and the venv — radon (cc/hal/mi), xenon, lizard, jscpd (global npm), pytest-cov, mutatest, semgrep, ruff, flake8. No new dependencies required.

**Storage**: N/A — no persistent store. Gate artifacts (`coverage.xml`, reports, mutation reports) are CI files.

**Testing**: Existing pytest suite (~1219 tests) is the regression oracle for every behavior-preserving refactor; coverage/mutation gates validate well-testedness of refactored code.

**Target Platform**: Linux (local `make quality-gate`) and GitHub Actions `ubuntu-latest` (PR + release, via feature 043 wiring).

**Project Type**: Existing Python library/CLI; this feature is a hygiene/refactoring + tooling pass rather than new external capability.

**Performance Goals**: Refactors must not change runtime behavior or performance characteristics (pure restructuring); the gate completes within the standard CI duration (SC-004).

**Constraints**: No public signature or output-format changes (JSON/CSV/XML); no breaking changes; existing tests stay green after every increment (FR-015, SC-006); `--max-modules=20` is enforced (clarification).

**Scale/Scope**: ~50 C-ranked blocks across the `specmetrics/` and `scripts/` trees; 28 B-ranked modules to reduce to ≤ 20; 2 gate scripts (`scripts/complexity_metrics.py`, and gate-wiring confirmation in `scripts/quality_gate.py`) corrected; Makefile thresholds ratified. Full enumeration is captured in `research.md` and `tasks.md`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **Evidence First (V)** — Every refactor preserves behavior; the existing test suite + gate metrics are the evidence that behavior did not change.
- **Explainability by Design (VI)** — Corrected MI/Halstead evaluation gives accurate, explainable maintainability reporting.
- **Rule Externalization (IX)** — Thresholds and severities remain configured (Makefile + scripts), matching the documented rules table.
- **Evolution Without Disruption (XIII)** — Behavior-preserving refactors and additive metric fixes do not invalidate prior outputs.
- **Layer Independence (XIV)** — Refactors respect existing layer boundaries; no cross-layer coupling introduced.
- **Fail Fast** (Pipeline invariant) — A blocking metric violation (complexity > 10, module cap, MI < 30) interrupts the gate before a build/merge.

**Compliance Verifications**:
- [x] Specification First: Is the primary input a software specification? — Yes, spec.md (044).
- [x] Evidence First: Does the design preserve traceability to evidence? — Refactors keep the test suite green; gate metrics record value/threshold/files.
- [ ] Canonical Representation: Does the feature operate on the CFM rather than framework-specific artifacts? — N/A: this is refactoring within existing component internals, not measurement logic.
- [ ] Plugin-Oriented: Is the capability implemented as a plugin when it could be external? — N/A: refinement of existing modules, no new extension point.
- [x] Rule Externalization: Are organizational policies externalized as Rule Packs? — Thresholds live in Makefile + scripts, external to measurement logic.
- [x] Layer Independence: Does the component depend only on stable abstractions of adjacent layers? — Refactors are local and behavior-preserving; no new cross-layer deps.
- [x] Open by Default: Are interfaces documented and standards-based? — No public contract changes; contracts remain stable.

## Project Structure

### Documentation (this feature)

```text
specs/044-apply-quality-rules/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
scripts/
├── complexity_metrics.py   # FIX: correct MI parsing + enforce MI<30 blocking, 30-69 warning
└── quality_gate.py         # VERIFY: MI threshold logic aligned with complexity_metrics.py

Makefile                     # RATIFY: thresholds already wired (duplication, coverage, mutation, security, lint)

specmetrics/
├── kernel/                  # 15 B-ranked / many C: engine_visitors, llm_gateway, deterministic_engine,
│                            #   engine_patterns, csm/builder, cfm/builder, graph_persistence,
│                            #   plugin_registry, plugin_validation, validation/pipeline, ...
├── plugins/measurement/*/  # fpa, snap, cognitive_points, storypoints, bcp, sfp, tshirt counters/assessors
├── plugins/adapter/*/      # speckit + openspec _scan_with_result
├── plugins/semantic/       # llm_provider (__init__, extract)
├── plugins/publisher/*, calibration/*, exporter/*, rule_pack/*
├── cli/                    # measure, export_commands, config_commands, commands/validate
├── mcp/                    # server _validate_tool_params
├── infrastructure/runs/    # cleaner (compute_retention C14)
└── application/            # orchestrator (already B, confirm no module-cap regression)
```

**Structure Decision**: No `src/`-tree changes and no new modules. Refactors happen in place within the existing single-project layout, one function/method/class at a time, preserving signatures. Enumeration and per-file scope live in `research.md`; the sequential order (kernel → measurement plugins → CLI/MCP → adapters) matches the plan's recommended execution order in `docs/plans/complexity-refactor-plan.md`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. The refactoring effort itself is high (50 blocks + module-cap reduction) but it is the explicit, clarified scope of this feature (SC-002) and is justified by enforcing the documented quality rules; it introduces no new architectural complexity.