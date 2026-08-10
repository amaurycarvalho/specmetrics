# ADR-002: Quality Gate for AI-Generated Code

**Date:** 2026-08-03

**Status:** Accepted

## Context

AI-generated code can vary significantly in quality, potentially introducing
high cyclomatic complexity, poor test coverage, security vulnerabilities,
excessive code duplication, and unmaintainable structures. Without automated
enforcement these issues accumulate and degrade the codebase. The project needs
a deterministic, reproducible quality gate that runs in CI, fails fast on
blocking violations, and reports non-blocking metrics without failing the
pipeline.

## Decision Drivers

- **Determinism** — the same commit must produce the same gate result regardless of environment
- **Blocking vs Warning separation** — critical quality regressions must fail CI; advisory metrics must never block unreliably
- **Homogeneity with SpecMetrics** — CI must not be the only enforcement point; the gate must be reproducible locally via a single command
- **Generated/build artifact exclusion** — `tests/`, `build/`, `dist/` and `ccache/` must never influence measured complexity
- **Fail-loud tooling** — a tool failure (crash, misconfiguration) must surface as a blocking failure rather than silently passing

## Decision

Adopt a layered quality gate orchestrated by `make quality-gate`, composed of
open-source established tools, with thresholds applied at the correct severity
level per the following rule table:

| Metric                     | Fail Condition    | Tool         | Severity      |
| -------------------------- | ----------------- | ------------ | ------------- |
| Cyclomatic Complexity      | > 10 (Grade B)    | Radon        | Blocking      |
| Code Coverage              | < 85%             | Pytest-cov   | Blocking      |
| Mutation Score             | < 80%             | Mutmut       | Blocking      |
| Maintainability Index      | < 30              | Radon        | Blocking      |
| Maintainability Index      | >= 30 and < 70    | Radon        | Warning       |
| Halstead Difficulty        | > 20              | Radon        | Warning       |
| Halstead Effort            | > 150,000         | Radon        | Warning       |
| Halstead Bugs              | > 0.5             | Radon        | Informational |
| Source Lines of Code       | > 80 per function | Lizard       | Warning       |
| Code Duplication           | > 10%             | jscpd        | Blocking      |
| Code Duplication           | > 7% and <= 10%   | jscpd        | Warning       |
| Security Findings (High)   | > 0               | semgrep      | Blocking      |
| Security Findings (Medium) | > 0               | semgrep      | Warning       |
| Lint Errors                | > 0               | ruff, flake8 | Blocking      |

### Tool Chain and Scope

| Concern                             | Tool        | Gate role                                                         |
| ----------------------------------- | ----------- | ----------------------------------------------------------------- |
| Lint & type hints                   | ruff        | Blocking: `ruff check .`                                          |
| Lint, bugs, annotations, docstrings | flake8      | Blocking: `--select=B,A,D` over `./specmetrics/` only             |
| Cyclomatic complexity               | radon/xenon | Blocking: `xenon --max-absolute=B`, ignores generated dirs        |
| Halstead / Maintainability          | radon       | Warning: parsed by `scripts/complexity_metrics.py`                |
| Function length                     | lizard      | Warning: `--CCN 10 --length 80 --warnings_only`                   |
| Code duplication                    | jscpd       | 7-10% Warning, >10% Blocking via threshold branch in the Makefile |
| Coverage                            | pytest-cov  | Blocking: `--cov-fail-under=85`                                   |
| Mutation survival                   | mutmut      | Blocking: `scripts/check-mutation-score.py`                       |
| Static security                     | semgrep     | ERROR Blocking, WARNING reported non-blocking                     |

### Architecture

```
Makefile (quality-gate target)
├── lint                → ruff check . ; flake8 --select=B,A,D ./specmetrics/
├── complexity          → radon cc + xenon + lizard + scripts/complexity_metrics.py
├── duplication         → jscpd (10% blocking / 7-10% warning)
├── test                → pytest --cov --cov-fail-under=85
├── mutation            → scripts/check-mutation-score.py
└── security            → semgrep

.github/workflows/ci.yml
  ├── lint job
  ├── test job
  └── quality-gate job
```

Blocking and informational enforcement is split across two components:

1. **`make` targets** — each metric's actual tool and threshold live here
   (`lint`, `complexity`, `duplication`, `test`, `mutation`, `security`). The
   Makefile is the single source of truth for thresholds.
2. **`scripts/quality_gate.py` — the orchestrator** — invokes each `make`
   target as a child process, records `{name, value, threshold, severity,
status, evidence}`, and produces a consolidated JSON + summary report. Any
   `fail` with `severity == "blocking"` or a tool error sets the overall gate
   to failed (exit non-zero).

`scripts/complexity_metrics.py` runs `radon hal` and `radon mi` and parses the
output against the Halstead/Maintainability thresholds. These are Warning or
Informational severity and never fail the gate (exits 0 always).

`scripts/check-mutation-score.py.py` reads `mutmut-cicd-results.log`.

### Build Artifact Exclusion

All three complexity tools (`radon`, `xenon`, `lizard`) are run over the
repository root but exclude `tests/`, `build/`, `dist/` and `ccache/` so that
test code and generated/build outputs never affect the measured metrics:

- radon/xenon: `--ignore "tests,build,dist,ccache"`
- lizard: `-x "./tests/*" -x "./build/*" -x "./dist/*" -x "./ccache/*"`

`complexity_metrics.py` applies the same `-i tests,build,dist,ccache` exclusion
to its `radon hal`/`radon mi` invocations.

### Configuration Deferred to Makefile

Rather than an external config file, thresholds live in the Makefile and the
tool CLIs. `install-quality-tools` installs the Python quality extras declared
in `pyproject.toml` (`ruff`, `flake8` + plugins, `radon`, `xenon`, `lizard`,
`pytest`, `pytest-cov`, `mutatest`, `semgrep`) plus `jscpd@4.0.1` via npm.

## Alternatives Considered

### Single Script Runs All Checks

Rejected. A single all-in-one script hides individual metric boundaries,
complicates local reuse (e.g., running only coverage), and makes threshold
changes touch code rather than a declarative target.

### XML/CI-Only Enforcement Without Local Replication

Rejected. This would couple enforcement to GitHub Actions and prevent
developers from reproducing the gate before opening a PR. The Makefile keeps
the gate fully local and identical to CI.

### Adopting a `max-complexity` derived from xenon average only

Rejected. Enforcing only the average allows hot spots to exceed the limit.
`xenon --max-absolute=B --max-modules=20 --max-average=B` caps the worst block
independently of the average.

### Treating all findings as blocking

Rejected. Halstead, Maintainability Index, and SLOC-per-function are advisory;
making them blocking produces false failures and churn. They are Warning-level.

## Consequences

- **Positive**
  - CI enforces hard quality thresholds while warning metrics are reported without noise
  - The gate is fully reproducible locally (`make quality-gate`)
  - Tool errors fail loudly rather than silently passing
  - Complexity metrics are immune to test/build/dist/ccache pollution
  - Single Makefile orchestrator (single source of truth) with a separate report orchestrator
- **Negative / Accepted**
  - Requires quality tools installed (`.venv` and global `jscpd` via npm) before running
  - Radon Halstead parsing depends on exact radon output format; format drift requires updating `complexity_metrics.py`
  - The Makefile/quality_gate split adds a thin layer of abstraction over `make`

## Release Verification

`build-wheel.yml` runs the reusable CI quality gate (`uses: ./.github/workflows/ci.yml`)
before building; the `build` job depends on it via `needs: quality-gate`. Every
published artifact therefore traces to a passing quality run. Record the version,
the passing run id and the artifact reference in the release notes so the
verification is auditable.
