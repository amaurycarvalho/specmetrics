# Quickstart: Quality Gate for CI and Release Builds

**Date**: 2026-08-03
**Scope**: Runnable validation scenarios proving the feature works end-to-end. Links to [data-model.md](data-model.md) and [contracts/contracts.md](contracts/contracts.md) for details — this guide does not duplicate them.

## Prerequisites

- Repo cloned at a working state on branch `043-quality-gate-implementation`.
- `python3` ≥ 3.12 and `make` available.
- GitHub Actions enabled for the repo (for workflow-level checks).

## Setup

```bash
make venv
make install-quality-tools
```

## Scenario 1 — Local quality gate passes

```bash
make quality-gate
```

**Expected outcome**: exit code `0`; the consolidated report lists each metric with value/threshold/status and `overall_status: pass`. Produces `coverage.xml` and the mutation report artifact.

## Scenario 2 — Local gate blocks on a violation

1. Temporarily add a line that drops coverage below 85% (or add a security-prone pattern matched by the configured scan).
2. `make quality-gate`
3. **Expected outcome**: exit code non-zero; the failing check is reported with its metric value, threshold and affected files (Evidence First, FR-007). No wheel produced (`make build` not reached).
4. Revert the change; gate returns to pass.

## Scenario 3 — Pull-request gate blocks a bad PR

1. Push a branch to a PR against `main` that lowers coverage below 85%.
2. **Expected outcome**: the `quality-gate` job in `ci.yml` fails and the PR is blocked from merging; the failing metric is highlighted.
3. Fix coverage; the PR passes and can merge.

## Scenario 4 — Release requires CI before build

1. Ensure a failing state (e.g., reintroduce the Scenario 2 violation) and trigger the release workflow (tag `v*` or `workflow_dispatch` with a version).
2. **Expected outcome**: the `quality-gate` job (calling reusable `ci.yml`) fails; the `build` job is skipped; no release/artifact is created (SC-001/SC-005).
3. With everything passing, trigger again. **Expected outcome**: the gate job passes, `build` runs, `make build` produces `dist/*.whl`, and the release is published under the validated version (FR-009).

## Scenario 5 — Report per Python version

Trigger CI (Scenario 3) and open the artifacts/`quality-gate` output for the 3.12 and 3.13 matrix entries.

**Expected outcome**: each version produced its own report with distinguishable `python_version`, and both must pass for the job to be green (FR-010).

## What success looks like

- SC-001: every published release in the last 3 months traces to a passing gate run.
- SC-004: `make quality-gate` completes within the standard CI duration; cached tooling keeps installs fast.
- SC-006: gates are blocking from first deployment, no informational phase.
