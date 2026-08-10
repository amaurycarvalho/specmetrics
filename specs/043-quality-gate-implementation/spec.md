# Feature Specification: Quality Gate for CI and Release Builds

**Feature Branch**: `043-quality-gate-implementation`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "leia a RFC-043, proponha as mudanças necessárias adicionando tambem a tarefa que @.github/workflows/build-wheel.yml deve rodar o @.github/workflows/ci.yml antes da build"

## Clarifications

### Session 2026-08-03

- Q: Release gate enforcement at launch? → A: Both release and PR gates blocking from day one (maximum protection).
- Q: Default severity of security scan findings? → A: Security findings are blocking by default (fail the run).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Release Build Only Happens on Verified Code (Priority: P1)

A maintainer triggers a release (by tagging a version or dispatching the release workflow). Before any distributable artifact is produced and published, the system automatically runs the full set of quality checks defined in the CI pipeline. If any check fails, no artifact is produced and the release is aborted with a clear failure. If all checks pass, the artifact is built and published as before.

**Why this priority**: This is the primary safety net of the feature. It guarantees that nothing broken, under-tested or poorly maintained ever reaches end users, making the existing release workflow trustworthy. Without it, quality gates on PRs alone would not protect released artifacts.

**Independent Test**: Can be fully tested by triggering a release while a deliberate quality violation exists (e.g., low test coverage) and confirming the release is blocked; then fixing the violation and confirming the release completes. Delivers protection of published artifacts.

**Acceptance Scenarios**:

1. **Given** a codebase with at least one failing quality check, **When** a release is triggered, **Then** the release is aborted, no artifact is published, and the failure reason is clearly reported.
2. **Given** a codebase where all quality checks pass, **When** a release is triggered, **Then** the artifact is built and published, and the CI check results are recorded for the release.
3. **Given** a release triggered manually with a version, **When** quality checks pass, **Then** the artifact is published under exactly that version.

---

### User Story 2 - Pull Requests Are Gated by Quality (Priority: P2)

A contributor opens or updates a pull request targeting the main branch. The system automatically runs the quality checks against the proposed changes. The PR is blocked from merging if the checks fall below the established thresholds, and the contributor receives clear feedback on which metric failed and why.

**Why this priority**: Catching quality regressions before merge keeps the main branch healthy and prevents bad code from ever reaching the release gate. It can be delivered and used independently from release gating.

**Independent Test**: Can be fully tested by opening a PR with a code change that drops coverage or adds complexity and confirming the PR is blocked; then improving the code and confirming the PR passes.

**Acceptance Scenarios**:

1. **Given** a pull request whose changes violate at least one quality threshold, **When** the CI workflow runs, **Then** the PR is reported as failing and merging is blocked.
2. **Given** a pull request whose changes meet all quality thresholds, **When** the CI workflow runs, **Then** the PR is reported as passing and can be merged.
3. **Given** a pull request that adds no functional code changes, **When** the CI workflow runs, **Then** the existing checks still pass without requiring new coverage.

---

### User Story 3 - Maintainers Get a Readable Quality Report (Priority: P3)

After each run of the quality checks, maintainers and contributors can view a single consolidated summary showing every metric, its measured value, its threshold, and pass/fail status for each supported Python version.

**Why this priority**: Without a clear report, a failing gate is frustrating and hard to act on. This story makes the other two usable by turning a binary pass/fail into actionable feedback. It is independently valuable and can be added after the gating mechanics work.

**Independent Test**: Can be fully tested by running the quality checks once and confirming a single report lists all metrics with values, thresholds and statuses.

**Acceptance Scenarios**:

1. **Given** a completed run of the quality checks, **When** the report is viewed, **Then** every evaluated metric is listed with its measured value, its threshold and a pass/fail status.
2. **Given** a run with one or more failing metrics, **When** the report is viewed, **Then** the failing metrics and their violations are clearly highlighted.
3. **Given** a run across multiple Python versions, **When** the report is viewed, **Then** results are distinguishable per version.

---

### Edge Cases

- A quality tool is unavailable or fails to run (e.g., network outage, missing dependency): the run must fail loudly rather than silently pass or skip the check.
- A release is triggered while the codebase has existing quality debt: the gate applies to the current state, and legacy debt must be handled via the documented exception process rather than disabling the gate.
- Zero tests exist for a new module: coverage and mutation thresholds must not be bypassed by excluding untested paths.
- A manual release dispatch supplies an invalid or missing version: the workflow must not publish an unversioned artifact.
- Multiple releases triggered concurrently: each release runs its own independent quality check against the code at that moment.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **Specification First (I)** — Not directly engaged: this feature hardens delivery of code, not functional measurement.
- **Evidence First (V)** — Engaged: every gate result must preserve evidence of which metric failed, on which version, and why.
- **Explainability by Design (VI)** — Engaged: the quality report must explain why a check failed with measured values and thresholds.
- **Rule Externalization (IX)** — Engaged: quality thresholds are organizational policy and must be configurable (Rule Pack style) rather than hard-coded in tooling.
- **Observability as a Native Capability (XI)** — Engaged: gate results are engineering telemetry and must be captured and reportable over time.
- **Evolution Without Disruption (XIII)** — Engaged: adding new quality checks must not break existing release workflows; the gate must be additive.
- **Fail Fast** (Pipeline invariant) — Engaged: a failing quality check must interrupt the build before an artifact is produced.

**Compliance Notes**: Threshold values and enabled checks will be defined in configuration external to the pipeline code, satisfying Rule Externalization. Each check records the evidence (metric value, threshold, file/section) behind a pass or fail, satisfying Evidence First and Explainability. The release workflow consumes the CI workflow's outcome as a dependency rather than reimplementing checks, so adding new checks is additive and non-disruptive.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run the complete set of quality checks defined in the CI pipeline before any release artifact is built, and MUST abort the release if any blocking check fails.
- **FR-002**: System MUST enforce that every pull request targeting the main branch runs the quality checks and MUST block merging when any blocking threshold is violated.
- **FR-003**: System MUST evaluate and enforce all quality metrics defined by the project, including at minimum: cyclomatic complexity, test coverage, code duplication, mutation survival, source line length per function, and security scan findings.
- **FR-004**: System MUST apply metric thresholds as defined in configuration, with at least: complexity below the blocking grade (Grade B), coverage at or above 85%, duplication above 10% blocking and 7-10% warning, mutation survival at or above 80%, Halstead and maintainability metrics as warnings, security High findings blocking and Medium findings as warnings, and lint errors blocking.
- **FR-005**: System MUST classify each check as blocking (fails the run) or warning (reported but does not fail the run), per the configured severity.
- **FR-006**: System MUST produce, for every run, a consolidated quality report listing each metric, its measured value, its threshold and its pass/warn/fail status.
- **FR-007**: System MUST record and preserve the evidence for every failing check (metric, measured value, threshold, and affected files) so failures are traceable.
- **FR-008**: System MUST fail the run loudly whenever a quality tool itself errors or cannot execute, rather than silently skipping the check.
- **FR-009**: System MUST verify the release version provided for a manual release is present and valid before publishing an artifact.
- **FR-010**: System MUST run the quality checks on all supported Python versions and report results per version.
- **FR-011**: System MUST NOT disable or bypass a quality check when the codebase carries pre-existing quality debt; exceptions MUST follow a documented, reviewed process.
- **FR-012**: System MUST enforce blocking thresholds for both pull requests and release builds from first deployment; informational (warnings-only) operation MAY exist as an opt-in diagnostic mode but MUST NOT be used as the rollout path.

### Key Entities

- **Quality Report**: Consolidated record of one gate run; captures metric name, measured value, threshold, severity, status (pass/warn/fail), Python version, and timestamp.
- **Quality Exception**: Documented, approved waiver allowing a specific check to be skipped for a defined scope and duration; includes rationale and reviewer approval.
- **Release Verification**: Record linking a published artifact to the passing quality run that authorized its release, preserving auditability.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of release workflows published in the last 3 months were preceded by a fully passing quality gate run, verified by audit records.
- **SC-002**: 90%+ of pull requests to the main branch pass the quality gate on the first CI run within 90 days of enforcement.
- **SC-003**: A failing check is reported with metric value, threshold and affected files in every run (0% of failures reported without evidence).
- **SC-004**: The quality gate blocks a release or merge within the standard CI run duration, with no single check adding more than a few minutes of overhead.
- **SC-005**: No published artifact is traced to a failed or skipped quality run.
- **SC-006**: Both pull request and release gates enforce blocking thresholds from the first deployment, with no informational phase required.

## Assumptions

- The project uses GitHub-hosted continuous integration for both pull requests and releases, and the existing CI workflow is the single source of truth for lint and test checks.
- Quality thresholds, enabled tools and severities are organizational policy and will live in configuration (per the Rule Externalization principle), following the metric values proposed in RFC-043.
- The release workflow will depend on the CI workflow's completion and success rather than re-running the checks itself; duplicate execution is to be avoided.
- The toolset proposed in RFC-043 (linting, complexity, duplication, mutation, security scanners) is available to the project; the exact tools are an implementation detail for the planning phase.
- Existing quality debt is handled through the documented exception process, not through an informational rollout phase or by disabling the gate.
- A single shared quality report per run is sufficient for v1; per-PR comment bots and dashboards are follow-up enhancements, not part of this feature.
