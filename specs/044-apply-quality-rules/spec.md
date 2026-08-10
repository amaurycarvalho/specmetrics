# Feature Specification: Apply Quality Rules and Make the Quality Gate Pass

**Feature Branch**: `044-apply-quality-rules`

**Created**: 2026-08-04

**Status**: Draft

**Input**: User description: "leia @docs/plans/complexity-refactor-plan.md e especifique as alterações planejadas, incluindo o que for necessário para aplicar as regras abaixo no projeto [metric table] ... Inclua também a correção dos erros abaixo no escopo: make quality-gate ..."

## Clarifications

### Session 2026-08-04

- Q: Should the xenon module-count ceiling (≤20 modules ranked B) be enforced as blocking, or should gate config be aligned to the rules table (blocking only on per-block complexity > 10)? → A: Keep and enforce `--max-modules=20`; refactor beyond the 48 blocks until ≤20 modules rank B or better (fully honors the existing xenon setting).
- Q: Must the maintainability index reach ≥70 for the gate to be done, or is it warning-only? → A: Warning if MI < 70 and ≥ 30; Blocking if MI < 30.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The Quality Gate Passes End-to-End (Priority: P1)

A maintainer runs `make quality-gate` on a clean checkout. The command installs the quality toolchain once, then runs lint, complexity, duplication, coverage, mutation and security checks in sequence. Every evaluation uses the project-defined thresholds; none of the checks fail; the command exits zero and prints a consolidated pass. The maintainer can ship code, tag a release and build a wheel without any gate being red.

**Why this priority**: This is the core deliverable. The current gate fails (`make quality-gate`: `make complexity` errors out with rank-C blocks and an over-limit maintainability warning). Until the gate is green, the guardrails defined by the previous feature (043) are unusable for PRs and releases. This story delivers a working, authoritative quality gate.

**Independent Test**: Run `make quality-gate` on the current codebase after the refactoring and confirm all checks pass and the command exits zero; introduce a deliberate violation (e.g., raise a function's cyclomatic complexity above the limit or drop coverage) and confirm the corresponding check fails with the correct severity and blocks.

**Acceptance Scenarios**:

1. **Given** a clean checkout on the current working tree, **When** `make quality-gate` is run, **Then** all checks (lint, complexity, duplication, coverage, mutation, security) pass and the command exits with code 0.
2. **Given** the current source, **When** the cyclomatic-complexity check runs, **Then** no function, method or class exceeds Grade B (complexity ≤ 10), the average complexity is lower than Grade A/B, and the maintainability index is at least 30 (a value below 30 would be blocking; 30–69 is a non-blocking warning).
3. **Given** the current source, **When** the coverage check runs, **Then** the test suite covers at least 85% of the codebase.
4. **Given** the current source, **When** the mutation check runs, **Then** the mutation survival rate is at least 80%.
5. **Given** the current source, **When** the duplication check runs, **Then** duplication is at or below 7% (no warning) and always below 10% (never blocking).
6. **Given** a change that introduces a complexity > 10, **When** `make quality-gate` runs, **Then** the complexity check reports a blocking failure and the command exits non-zero.

---

### User Story 2 - Each Metric Enforces Its Documented Threshold and Severity (Priority: P2)

A developer or reviewer reviews a code change against the project's documented quality rules. Every metric defined by the rules table is evaluated by the designated tool with the documented fail condition and severity. Blocking metrics fail the gate; warnings are reported but do not fail the run; informational metrics are recorded only. A single consolidated report lists each metric, its measured value, its threshold, its severity and its pass/warn/fail status.

**Why this priority**: The rules table is only meaningful if it is actually enforced. This story guarantees the documented thresholds (complexity, coverage, mutation, maintainability, Halstead, lines per function, duplication, security findings, lint) map one-to-one to the tools and severities in the gate, and that blocking vs. warning behavior is applied correctly. It is independently testable and makes the gate output explainable.

**Independent Test**: Inspect the quality gate script and the CI workflow, and confirm each metric in the rules table maps to its tool, fail condition and severity; run individual checks and confirm warnings do not fail the run while blocking items do.

**Acceptance Scenarios**:

1. **Given** the project quality configuration, **When** the metrics are enumerated, **Then** every metric in the rules table (cyclomatic complexity, coverage, mutation score, maintainability index, Halstead difficulty/effort/bugs, source lines per function, duplication, security high/medium findings, lint errors) is represented with its tool, fail condition and severity.
2. **Given** a blocking threshold violation (e.g., security high finding, duplication > 10%, coverage < 85%, lint error, complexity > 10), **When** the gate runs, **Then** the run fails (non-zero exit).
3. **Given** a warning-only violation (e.g., maintainability index < 70, Halstead difficulty > 20, duplication between 7% and 10%, medium security finding, lines per function > 80), **When** the gate runs, **Then** the metric is reported as a warning but the run still passes.
4. **Given** a completed gate run, **When** the consolidated report is viewed, **Then** each metric shows its measured value, threshold, severity, status and supporting evidence.

---

### User Story 3 - Release and PR Gates Consume the Same Quality Result (Priority: P3)

A maintainer triggers a release and a contributor opens a pull request. Both pipelines invoke the same single quality gate (via `make quality-gate`/CI) rather than each re-implementing checks. When the gate is green, both the PR can merge and the release can build; when it is red, both are blocked with the same evidence. No duplicate, divergent or skipped evaluation occurs between PR and release paths.

**Why this priority**: This closes the loop started by feature 043 and guarantees consistency between merge and release quality. It is independently valuable once the gate is green, and confirms there is a single source of truth for quality.

**Independent Test**: Trigger a PR and a release against the same codebase and confirm both surface identical pass/fail outcomes derived from one gate invocation.

**Acceptance Scenarios**:

1. **Given** a green quality gate, **When** a PR targets the main branch, **Then** the PR passes its quality checks and is mergeable.
2. **Given** a green quality gate, **When** a release is triggered, **Then** the release is allowed to build and publish.
3. **Given** a red quality gate, **When** both a PR and a release are triggered, **Then** both are blocked, and each reports the same failing metric, threshold and evidence.

---

### Edge Cases

- A quality tool is not installed or fails to execute: the run must fail loudly rather than silently skip the check.
- The maintainability index is computed as a low value (e.g., cached at 0) on first run: once real computation lands, a value below 30 must be treated as a blocking failure, while 30–69 remains a warning; the check must not silently pass a genuinely blocking MI.
- A borderline complexity value (exactly 10): treated as Grade B and therefore passing (fail condition is strictly greater than 10).
- Duplication between 7% and 10% inclusive behavior: 10% or less is a warning, strictly greater than 10% is blocking.
- Rules to be enforced are organizational policy: thresholds and enabled metrics should live in configuration (Rule Pack style) rather than hard-coded solely in the Makefile.
- The refactors must not change observable behavior: the full existing test suite must remain green after each refactoring step.

## Constitution Check *(mandatory)*

**Engaged Principles**:

- **Specification First (I)** — Not directly engaged: this hardens delivery tooling, not functional measurement.
- **Evidence First (V)** — Engaged: each gate result (and each fail/warn) must preserve the metric value, threshold and affected files as evidence.
- **Explainability by Design (VI)** — Engaged: the consolidated report explains why each check passed, warned or failed.
- **Rule Externalization (IX)** — Engaged: quality thresholds and severities are organizational policy and should be externalized as configuration rather than embedded only in the Makefile.
- **Observability as a Native Capability (XI)** — Engaged: gate results are engineering telemetry and must be captured and reportable.
- **Evolution Without Disruption (XIII)** — Engaged: refactoring existing code to reduce complexity must preserve behavior and not invalidate previously generated measurements or outputs.
- **Layer Independence (XIV)** — Engaged: refactors respect the existing layered architecture; no cross-layer coupling is introduced.
- **Fail Fast** (Pipeline invariant) — Engaged: a failing blocking check interrupts the run before a build or merge.

**Compliance Notes**: Refactoring for cyclomatic complexity is pure behavior-preserving restructuring (Extract Method, dispatch tables, guard clauses) validated by the existing 1219-test suite remaining green. Every gate result and every complexity refactor keeps its audit trail. Thresholds and severities follow the documented rules table and are surfaced in a single consolidated report, satisfying Evidence First, Explainability and Rule Externalization.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST run `make quality-gate` successfully (exit code 0) against the current codebase, covering lint, complexity, duplication, coverage, mutation and security checks.
- **FR-002**: System MUST ensure no function, method or class has a cyclomatic complexity greater than 10 (Grade B), and MUST fail the gate if any does (blocking severity).
- **FR-003**: System MUST ensure the average cyclomatic complexity of the codebase is at or below Grade B, per the xenon `--max-average=B` setting.
- **FR-004**: System MUST ensure no more than 20 modules are ranked Grade B or worse by xenon (`--max-modules=20`); exceeding that limit MUST fail the gate. This is a blocking rule and REQUIRES refactoring beyond the 48 rank-C blocks to bring the module count under the ceiling.
- **FR-005**: System MUST ensure test coverage is at least 85%; below this the gate MUST fail (blocking severity).
- **FR-006**: System MUST ensure the mutation survival rate is at least 80%; below this the gate MUST fail (blocking severity).
- **FR-007**: System MUST evaluate and report the maintainability index (MI): MI ≥ 70 MUST pass; 30 ≤ MI < 70 MUST be reported as a warning and MUST NOT fail the gate; MI < 30 MUST be reported as a blocking failure (fails the gate).
- **FR-008**: System MUST evaluate and report Halstead difficulty (threshold 20, warning), Halstead effort (threshold 150,000, warning) and Halstead bugs (threshold 0.5, informational); violations MUST NOT fail the gate.
- **FR-009**: System MUST evaluate source lines of code per function (threshold 80, warning); violations MUST be reported but MUST NOT fail the gate.
- **FR-010**: System MUST evaluate code duplication: greater than 10% MUST be blocking; greater than 7% and up to 10% MUST be a warning; 7% or below MUST pass.
- **FR-011**: System MUST evaluate security findings: any High-severity finding MUST be blocking; Medium-severity findings MUST be warnings and MUST NOT fail the gate.
- **FR-012**: System MUST evaluate lint errors with ruff and flake8; any lint error MUST be blocking.
- **FR-013**: System MUST produce a consolidated report for each gate run that lists every metric with its measured value, threshold, severity, status and supporting evidence.
- **FR-014**: System MUST fail the run loudly when a quality tool is missing or errors, rather than silently skipping the check.
- **FR-015**: System MUST keep the full existing test suite passing (no regressions) after every complexity refactor as part of the gate.
- **FR-016**: System MUST define the enabled metrics, thresholds and severities in configuration external to the pipeline code wherever practical (Rule Externalization), with the documented rules table as the canonical contract.
- **FR-017**: System MUST apply the same quality gate outcome to both pull-request and release workflows, without duplicating or skipping a check between them.

### Key Entities

- **Quality Report**: Consolidated record of one gate run; captures metric name, measured value, threshold, severity, status (pass/warn/fail) and evidence.
- **Block Grade Map**: Mapping of cyclomatic complexity grades (A–F) to thresholds used by the gate (Grade B ≤ 10) to classify permissible vs. blocking complexity.
- **Quality Threshold Config**: Externalized definition of enabled metrics, tools, fail conditions and severities (the rules table) consumed by the gate scripts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `make quality-gate` exits with code 0 when run against the current working tree on a clean environment.
- **SC-002**: 100% of blocks (functions, methods, classes) have cyclomatic complexity ≤ 10 (Grade B or better), the average complexity is at or below Grade B, and no more than 20 modules rank Grade B or worse.
- **SC-003**: Test coverage is 85% or higher and mutation survival is at least 80%, verified on every gate run.
- **SC-004**: Every gate run produces a report where each of the metrics is shown with value, threshold, severity and status — 100% of metrics accounted for with no silent skips.
- **SC-005**: Blocking violations (complexity > 10, coverage < 85%, mutation < 80%, duplication > 10%, security High, lint errors, MI < 30) always fail the gate, while warning/informational ones (MI 30–69, Halstead, duplication 7–10%, security Medium, lines > 80) never fail it.
- **SC-006**: The existing full test suite passes with no regressions after the refactoring (0 failures).
- **SC-007**: A single gate invocation is shared by both PR and release workflows, with no metric evaluated twice or skipped by either.

## Assumptions

- The forty-eight Phase-3 rank-C blocks reported by the gate (and listed in `docs/plans/complexity-refactor-plan.md`) are in scope and will be reduced to Grade B or better using behavior-preserving refactors taught in the plan (Extract Method, dispatch tables, guard clauses). Because the `--max-modules=20` ceiling is enforced, additional module-level Grade-B reductions beyond the 48 blocks are also in scope so that no more than 20 modules rank B or worse (per clarification 2026-08-04).
- The maintainability-index value (currently reported at 0) must be recomputed accurately; per clarification 2026-08-04 it is a warning when 30 ≤ MI < 70 and a blocking failure when MI < 30.
- Quality tools (radon, xenon, lizard, jscpd, mutatest, pytest-cov, semgrep, ruff, flake8) are available via the existing `quality` extra and global npm `jscpd`; installation is part of `make install-quality-tools`.
- Behavior of external tools is the single source of truth for measured values; the rules table documents thresholds/severities, and the Makefile/gate scripts map metric → tool → condition → severity.
- Refactoring must not change public signatures or output formats (JSON/CSV/XML) and must not break backward compatibility.
- `/speckit.clarify` and `/speckit.plan` will follow to break the work into phases and tasks; this spec captures the full scope and acceptance of the gate.