# Implementation Plan: Quality Gate for CI and Release Builds

**Branch**: `043-quality-gate-implementation` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/043-quality-gate-implementation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Implement a quality gate for the SpecMetrics CI and release pipelines. Following RFC-043 and the clarified decisions, the existing `ci.yml` workflow is extended with a dedicated quality-gate job that enforces blocking thresholds (complexity, coverage, duplication, mutation, security) for every pull request to `main`, and `build-wheel.yml` gains a hard dependency on `ci.yml` so a wheel is only ever built and published after the full CI (including the quality gate) passes. The gate is blocking from day one for both PRs and releases, and security findings block by default. Configuration lives in `pyproject.toml` so thresholds are external to the tooling (Rule Externalization).

## Technical Context

**Language/Version**: Python 3.12/3.13 (project runtime exercised in CI). The feature itself is CI configuration, Makefile targets and tooling configuration, not new application code.

**Primary Dependencies**: Quality tooling proposed by RFC-043 — ruff, flake8 (+ bugbear, annotations, docstrings), radon, xenon, lizard, jscpd, pytest-cov, mutatest, semgrep. Exact version pins and grouping resolved in `research.md`.

**Storage**: N/A — no persistent store. Reports and artifacts are CI files/artifacts (`coverage.xml`, mutation report, consolidated report).

**Testing**: Existing pytest suite is the subject of the coverage/mutation gates. The gate configuration itself is verified through CI self-checks and the quickstart validation scenarios.

**Target Platform**: GitHub Actions, `ubuntu-latest`, for both pull-request CI and release builds.

**Project Type**: CI/CD infrastructure and build tooling configuration for a Python library/CLI.

**Performance Goals**: Gate completes within the standard CI run; each new check adds at most a few minutes (SC-004). Caching of the tooling venv keeps install time down.

**Constraints**: Release workflow MUST run CI (including quality gate) before any build; fail loudly on tool errors; blocking enforcement from first deployment; security findings block by default.

**Scale/Scope**: Two workflows (`.github/workflows/ci.yml`, `.github/workflows/build-wheel.yml`), Makefile quality targets, tool configuration in `pyproject.toml`, two support scripts under `scripts/`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **Evidence First (V)** — Gate results record metric, value, threshold and affected files.
- **Explainability by Design (VI)** — Consolidated report explains why each check failed.
- **Rule Externalization (IX)** — Thresholds and enabled checks configured in `pyproject.toml`, not hard-coded in scripts.
- **Observability as a Native Capability (XI)** — Gate results are telemetry captured per run and reportable over time.
- **Evolution Without Disruption (XIII)** — New checks added additively without breaking the release path.
- **Fail Fast** (Pipeline invariant) — A failing check interrupts the build before artifact production.
- **Plugin-Oriented (VIII)** — Quality tools are invoked as external CLI tools; no in-repo reimplementation of measurement logic.

**Compliance Verifications**:
- [x] Specification First: Is the primary input a software specification? — Yes, spec.md + RFC-043.
- [x] Evidence First: Does the design preserve traceability to evidence? — Every check emits metric value, threshold, files.
- [ ] Canonical Representation: Does the feature operate on the CFM rather than framework-specific artifacts? — N/A: CI hardening, not measurement.
- [x] Plugin-Oriented: Is the capability implemented as a plugin when it could be external? — Tools run as external CLIs via Makefile targets.
- [x] Rule Externalization: Are organizational policies externalized as Rule Packs? — Thresholds configured in pyproject.toml.
- [ ] Layer Independence: Does the component depend only on stable abstractions of adjacent layers? — N/A: CI tooling, no application layers touched.
- [x] Open by Default: Are interfaces documented and standards-based? — Standard Makefile targets and workflow contracts.

## Project Structure

### Documentation (this feature)

```text
specs/043-quality-gate-implementation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.github/workflows/
├── ci.yml               # extended: + quality-gate job (blocking), + per-version matrix
└── build-wheel.yml      # modified: build job needs: [ci] (hard dependency)

Makefile                 # + quality-gate, complexity, duplication, mutation, security targets

pyproject.toml           # + [project.optional-dependencies].quality and gate configuration

scripts/
├── quality_gate.py      # consolidated gate runner + report generator
└── mutatest_gate.py     # mutation gate runner (fail if survival < threshold)
```

**Structure Decision**: No new application code is produced. The feature lives entirely in the existing workflow files, Makefile, pyproject and a small `scripts/` directory, matching the current single-project layout (no `src/`-tree changes). This keeps the gate additive and non-disruptive per Evolution Without Disruption.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations. All engaged principles are satisfied as documented above; the two N/A verifications are CI-hardening scope, not application-layer rules.
