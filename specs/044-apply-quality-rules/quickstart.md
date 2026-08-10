# Quickstart: Apply Quality Rules and Make the Quality Gate Pass

**Date**: 2026-08-04
**Scope**: Runnable validation scenarios proving the gate passes and the quality rules are enforced. References [data-model.md](data-model.md) and [contracts/contracts.md](contracts/contracts.md) for details; does not duplicate them.

## Prerequisites

- Repo cloned on branch `044-apply-quality-rules` from a clean state.
- `python3` ≥ 3.12, `make`, and `node`/`npm` (for global `jscpd@4.0.1`) available.
- Existing `.venv` with the `quality` extra installed (or install via `make install-quality-tools`).

## Setup

```bash
make venv
make install-quality-tools
```

## Scenario 1 — The quality gate passes end-to-end

```bash
make quality-gate
```

**Expected outcome**: exit code `0`. The gate installs tooling, then runs lint, complexity, duplication, test (coverage), mutation and security in sequence; the consolidated report lists each metric with value/threshold/severity/status and `overall_status: pass`. Produces `coverage.xml`.

This is the primary acceptance check (SC-001). It exercises Contracts 1–4 and confirms:
- No block with CCN > 10 (Contract 1/FR-002).
- ≤ 20 modules ranked B or worse (Contract 1/FR-004; research R-3).
- Average complexity ≤ Grade B.
- Maintainability Index classification per Contract 2 (FR-007).

## Scenario 2 — Complexity still blocks when a violation is introduced

1. Temporarily raise a function's cyclomatic complexity above 10 (e.g., add a large `if/elif` chain to a small helper in a kernel module).
2. `make complexity`
3. **Expected outcome**: exit code non-zero; xenon reports the block as rank C, and `make quality-gate` fails (blocking). Revert the change.

## Scenario 3 — Maintainability Index severity tiers are enforced

1. `python3 scripts/complexity_metrics.py`
2. **Expected outcome (after the R-4 fix)**: prints a correct MI line from real `radon mi` scores — `Maintainability Index worst <NN> >= 70` (pass), `[Warning] ... < 70` (30–69), or `[Blocking] Maintainability Index < 30` (if any module scores below 30). Exit code `1` iff any module's MI is below 30 (Contract 2/FR-007). The previously spurious `Maintainability Index 0 < 70` must no longer appear.

## Scenario 4 — Module cap enforced (`--max-modules=20`)

`make complexity` parses xenon output. Check the module count:

```bash
make complexity >/dev/null 2>&1 && echo "complexity PASS" || echo "complexity FAIL"
```

**Expected outcome**: `complexity PASS` only when ≤ 20 modules rank B or worse (FR-004). When the count exceeds 20, the target fails. This is the acceptance for clarification 2026-08-04 (enforce the ceiling).

## Scenario 5 — No regressions after refactors

After each refactor increment (kernel → measurement plugins → CLI/MCP → adapters):

```bash
make test
make lint
```

**Expected outcome**: full suite passes (0 failures, ≥ 85% coverage) and lint is clean — proving behavior preservation (FR-015/SC-006) per the refactor safety contract (Contract 5).

## Scenario 6 — PR and release gates share the same result

Two identical-quality states:

1. Push a branch with a quality violation to a PR against `main`.
2. Trigger the release workflow at the same state.

**Expected outcome**: both the PR (via `ci.yml`) and the release (via `build-wheel.yml` depending on CI) are blocked and report the same failing metric/threshold/evidence (FR-017/SC-007, wiring from feature 043). With everything green, both pass and the release publishes from `dist/*.whl`.

## What success looks like

- SC-001: `make quality-gate` exits 0 on a clean run.
- SC-002: no block exceeds CCN 10, average ≤ Grade B, ≤ 20 modules ranked B-or-worse.
- SC-003: coverage ≥ 85% and mutation ≥ 80% on every run.
- SC-004: every metric appears with value/threshold/severity/status; no silent skips.
- SC-005: blocking violations always fail; warning/informational never fail.
- SC-006: full test suite green, 0 regressions.