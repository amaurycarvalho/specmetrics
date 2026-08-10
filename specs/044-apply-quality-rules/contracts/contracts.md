# Contracts: Apply Quality Rules and Make the Quality Gate Pass

**Date**: 2026-08-04
**Scope**: Interface contracts introduced or corrected by this feature. Format chosen: Makefile target contracts, gate-script behaviors and metric severity contracts, matching the project type (library/CLI with gate tooling). Contracts that are unchanged from feature 043 (CI/release workflow wiring, `quality_gate.py` JSON report shape) are referenced, not duplicated.

## Contract 1 — `make complexity` threshold & severity contract

`make complexity` MUST pass (exit 0) only when **all** of the following hold; otherwise it MUST exit non-zero (blocking).

| Metric | Source contract | Pass condition | Severity on violation |
|--------|-----------------|----------------|-----------------------|
| Cyclomatic complexity per block | `xenon --max-absolute=B` | every block `grade ≤ B` (CCN ≤ 10) | **Blocking** (exit 1) |
| Module complexity count | `xenon --max-modules=20` | ≤ 20 modules ranked B or worse | **Blocking** (exit 1) |
| Average complexity | `xenon --max-average=B` | average ≤ Grade B | **Blocking** (exit 1) |

Precondition: `$(VENV)` exists with radon/xenon/lizard installed. Tool failure (missing binary, crash) MUST fail the target (fail-loud, FR-014).

## Contract 2 — Maintainability Index severity contract (corrected)

Corrected evaluation inside `scripts/complexity_metrics.py` (R-4) and `make complexity`.

| `worst_mi` | Reported as | `make complexity` exit |
|------------|-------------|------------------------|
| `worst_mi ≥ 70` | pass `Maintainability Index >= 70` | 0 |
| `30 ≤ worst_mi < 70` | `[Warning] Maintainability Index < 70` | 0 |
| `worst_mi < 30` | `[Blocking] Maintainability Index < 30` | **1** |

**Parser contract**: the score is the trailing parenthesized token of each `radon mi -s` line (`... - <grade> (<score>)`). An empty/unparseable score MUST NOT be treated as a pass or a warning; it MUST be reported and, if it cannot be established that `worst_mi ≥ 30`, MUST be treated conservatively (FR-014).

Note: this severity contract **supersedes** the informational/warning-only treatment described in feature 043's rules for MI and adds a blocking tier below 30, per clarification 2026-08-04.

## Contract 3 — Halstead & lines-per-function (ratified, unchanged)

Reported but never failing (FR-008/FR-009).

| Metric | Threshold | Severity |
|--------|-----------|----------|
| Halstead Difficulty | ≤ 20 | Warning (exit 0) |
| Halstead Effort | ≤ 150,000 | Warning (exit 0) |
| Halstead Bugs | ≤ 0.5 | Informational (exit 0) |
| Source lines / function | ≤ 80 | Warning (exit 0) |

## Contract 4 — Other metric thresholds (ratified, unchanged)

| Metric | Tool | Fail condition | Severity |
|--------|------|----------------|----------|
| Code coverage | pytest-cov | < 85% | Blocking |
| Mutation survival | mutatest | < 80% | Blocking |
| Code duplication | jscpd | > 10% | Blocking |
| Code duplication | jscpd | > 7% and ≤ 10% | Warning |
| Security findings | semgrep | High > 0 | Blocking |
| Security findings | semgrep | Medium > 0 | Warning |
| Lint errors | ruff, flake8 | > 0 | Blocking |

## Contract 5 — Refactor safety contract (behavior-preservation)

Every refactoring of a `ComplexityBlock`/`ComplexityModuleRank` MUST satisfy:

- No change to the block's public signature (name, parameters, return type).
- No change to observable output formats (JSON/CSV/XML) or CLI behavior.
- The existing test suite passes (no regressions) — enforced by `make test` (FR-015, SC-006).
- The refactor is validated incrementally: after each change, `make complexity` and targeted tests run green before proceeding (matching the per-block validation loop in `docs/plans/complexity-refactor-plan.md`).

## Wire contract (reused from 043)

- Exit 0 iff no blocking violation and no tool error.
- Any `quality_gate.py` check with `status: fail` and `severity: blocking`, or any tool error, sets `overall_status: fail` and exit ≠ 0 (see `contracts/contracts.md` in 043). This feature confirms the `MI` check uses the Contract 2 severity.