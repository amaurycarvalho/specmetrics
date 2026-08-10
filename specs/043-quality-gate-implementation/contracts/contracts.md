# Contracts: Quality Gate for CI and Release Builds

**Date**: 2026-08-03
**Scope**: Interface contracts for the quality gate. Format chosen: CLI command contracts and CI workflow contracts, matching the project type (library/CLI with GitHub Actions).

## Contract 1 — Makefile quality targets

The gate is exposed through standard Makefile targets (the "CLI" of the gate). Each returns a successful exit code (0) on pass and non-zero on blocking failure.

| Target | Input | Output | Exit code |
|--------|-------|--------|-----------|
| `make quality-gate` | source tree, tests, venv | consolidated gate pass/fail | 0 if all blocking checks pass, 1 otherwise |
| `make lint` | source tree | lint pass/fail | 0 on clean, non-zero on violation |
| `make complexity` | source tree | metrics (radon/xenon/lizard) | 0 within thresholds, non-zero on violation |
| `make duplication` | source tree | jscpd duplication | 0 under 5%, non-zero otherwise |
| `make test` | source tree | pytest + coverage.xml | 0 over 85% coverage, non-zero otherwise |
| `make mutation` | source tree, coverage.xml | mutatest report | 0 over 80% survival, non-zero otherwise |
| `make security` | source tree | semgrep scan | 0 with no ERROR findings, non-zero otherwise |
| `make install-quality-tools` | venv | quality tooling installed | 0 on success |

Precondition: a `$(VENV)` exists (each target depends on `$(VENV)`).

## Contract 2 — CI workflow (`.github/workflows/ci.yml`)

Extended to include a **reusable** quality-gate callable workflow plus a quality-gate job.

```yaml
# contract
name: CI
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  workflow_call: {}          # reusable: consumed by build-wheel.yml
jobs:
  lint:    # existing
  test:    # existing matrix 3.12, 3.13
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      # checkout, setup-python (matrix 3.12/3.13), cache venv
      - run: make install-quality-tools
      - run: make quality-gate
      - upload coverage.xml (codecov or artifact)
      - upload mutation_report.html (artifact per version)
```

Behavior contract:
- PRs to `main` are blocked when `quality-gate` fails.
- The workflow is callable by `workflow_call` so the release path can compose it.
- Runs on both supported Python versions (3.12, 3.13); each produces its own report.

## Contract 3 — Release workflow (`.github/workflows/build-wheel.yml`)

```yaml
name: Build Wheel
on:
  push: { tags: ["v*"] }
  workflow_dispatch: { inputs: { version: { required: true } } }
jobs:
  quality-gate: { uses: ./.github/workflows/ci.yml }   # runs lint+test+quality-gate
  build:
    needs: quality-gate
    runs-on: ubuntu-latest
    steps:
      - checkout, setup-python 3.12
      - run: make build
      - use: softprops/action-gh-release (tag/files dist/*.whl, body CHANGELOG.md)
```

Behavior contract:
- `build` job depends on `quality-gate`; if the gate fails, `build` is skipped and no artifact is published (SC-001/SC-005).
- Manual `workflow_dispatch` still validates the supplied `version` (FR-009) by tag/version handling in the release step.
- Permissions: gate job read-only; build job `contents: write` to publish the release.

## Contract 4 — Quality report format (produced by `scripts/quality_gate.py`)

Machine-readable part of output (JSON on stdout/stderr), human-readable on the terminal:

```json
{
  "run_id": "<github.run_id>",
  "python_version": "3.12",
  "overall_status": "pass",
  "timestamp": "2026-08-03T12:00:00Z",
  "checks": [
    {"name": "coverage", "value": 92.0, "threshold": 85.0, "severity": "blocking", "status": "pass", "evidence": []},
    {"name": "security", "value": 0, "threshold": 0, "severity": "blocking", "status": "pass", "evidence": []}
  ]
}
```

Wire contract:
- Exit 0 iff `overall_status == "pass"`.
- Any check with `status: fail` and `severity: blocking`, or any tool error, sets `overall_status: fail` and exit ≠ 0.