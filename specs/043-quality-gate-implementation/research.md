# Research: Quality Gate for CI and Release Builds

**Date**: 2026-08-03
**Input**: RFC-043 + `specs/043-quality-gate-implementation/spec.md` (043-quality-gate-implementation)

This research resolves the technical unknowns raised by the feature spec and RFC-043 for the SpecMetrics repo. Findings are recorded as Decision / Rationale / Alternatives.

---

## R-1: How to make `build-wheel.yml` run `ci.yml` before building

**Context**: FR-001 / US1 require the release workflow to depend on the CI workflow's success. GitHub Actions does not allow a `needs:` dependency across two separate top-level workflows.

**Decision**: Convert `ci.yml` into a reusable workflow by adding a `workflow_call:` trigger, and add a holder job in `build-wheel.yml` (`build` has `needs: quality-gate`) that calls the reusable CI (lint + test + quality-gate). The release build job then runs only after the called CI completes successfully.

**Rationale**: A reusable workflow is the standard, supported way to compose workflows; the called workflow's failing job fails the caller job, so a failing check naturally aborts the build before any artifact is produced (FR-Build / SC-001).

**Alternatives considered**:
- `workflow_run` trigger (separate event) — async, does not hard-block and is fragile for manual `workflow_dispatch`.
- Re-implementing gate checks inside `build-wheel.yml` — duplicates logic and violates Rule Externalization / DRY.
- A single merged workflow file — consolidates PR + release triggers, but changes existing behavior and branch logic more than needed.

---

## R-2: Tooling and thresholds (from RFC-043 §3.1)

**Item**: Which quality tools and exact thresholds to enforce, and their severities.

**Decision**: Adopt the RFC-043 toolset and thresholds, externalized as configuration:

| Metric | Tool | Threshold | Severity |
|--------|------|-----------|----------|
| Cyclomatic complexity | xenon (radon cc) (`make complexity`) | `<= 10` (Grade B) | Blocking |
| Maintainability Index | radon | `> 70` | Warning |
| Source lines / function | lizard | `< 80` | Warning |
| Code duplication | jscpd | `> 10%` blocking, `7-10%` warning | Blocking / Warning |
| Test coverage | pytest-cov | `>= 85%` | Blocking |
| Mutation survival | mutatest | `>= 80%` | Blocking |
| Halstead difficulty | radon | `< 20` | Warning |
| Halstead effort | radon | `< 150,000` | Warning |
| Halstead bugs | radon | `< 0.5` | Informational |
| Security findings | semgrep | High `> 0` blocking, Medium `> 0` warning | Blocking / Warning |
| Lint errors | ruff, flake8 | `> 0` | Blocking |

Linters (ruff, flake8 + bugbear/annotations/docstrings) gate linting with `--fail-on-violation` semantics so failures block.

**Rationale**: Matches the RFC metric table and the clarified "both gates blocking from day one" and "security findings block by default" decisions. Thresholds live in config, satisfying Rule Externalization.

**Alternatives considered**: Partial adoption (informational phase) — rejected by clarification Q1/Q2; enabling as warnings — contradicts the "maximum protection" posture.

---

## R-3: Dependency/tool availability and caching

**Item**: How to install quality tooling efficiently in CI without slowing the gate.

**Decision**: Expose a `[project.optional-dependencies].quality` group in `pyproject.toml` and add a `make install-quality-tools` target. Cache the venv in CI keyed on `pyproject.toml` hash.

**Rationale**: Keeps versions reproducible, single source of truth in the manifest, and reuse of the RFC tool list. Caching bounds install time so SC-004 (no check adds more than a few minutes) holds.

**Alternatives considered**: Pinning tools ad hoc in workflow `pip install` lines — less reproducible and noisier.

---

## R-4: Report and telemetry

**Item**: How to satisfy Evidence First + Explainability + Observability for gate results.

**Decision**: A `scripts/quality_gate.py` runner executes each tool, captures metric/value/threshold/status per record, aggregates into a consolidated report (human-readable), and exits nonzero on any blocking failure or tool error (fail-loud, FR-008). Coverage and mutation artifacts upload as CI artifacts per Python version (FR-010, FR-006). A `Release Verification` mapping can be linked in the release body/notes using the successful run ID.

**Rationale**: One script centralizes run/report/evidence logic (single source of truth), keeps tooling external, and produces traceable output without any persistence layer.

**Alternatives considered**: Distributing logic across many workflow steps — harder to trace and no single report entity; a full telemetry publisher — out of scope for v1 per Assumptions (report bots/dashboards deferred).

---

## R-5: Legacy debt and exceptions

**Item**: How to keep gates blocking while avoiding a hard bligh after enforcing rigorous thresholds (FR-011).

**Decision**: Enforce thresholds immediately but provision a documented `Quality Exception` record (scope, duration, rationale, approver) in config. Any exclusion is explicit, reviewed, and audited, never an automatic skip.

**Rationale**: Follows the clarified "blocking from day one" while preserving a legal escape hatch for real legacy debt, matching FR-011 without a silent-disabling path.

---

## Unknowns remaining after research

None. All Technical Context `NEEDS CLARIFICATION` placeholders (primary deps, tooling, thresholds, gating model) are resolved by the decisions above. Proceeding to Phase 1 design.