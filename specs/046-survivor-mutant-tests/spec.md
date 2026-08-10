# Feature Specification: Eliminate Surviving Mutants with Targeted Tests

**Feature Branch**: `046-survivor-mutant-tests`

**Created**: 2026-08-10

**Status**: Draft

**Input**: User description: "Read `mutants/mutmut-cicd-results.log` and create a plan for analyzing the survivors in it, grouped by module. For each survivor found, analyze whether the corresponding test already guarantees the death of that survivor. If it already guarantees it, skip that survivor. If it does not, write additional tests that kill that specific survivor. Do not run mutmut at any time; only run the respective test that was modified or inserted to ensure it works. At the end, run a lint and a complete test run, fixing any failure that is pointed out. Never run mutmut, because the user will do it manually."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze Survivors Grouped by Module (Priority: P1)

The quality gate reports a mutation score below the 80% threshold (`Survived: 8822`). The engineer needs to understand which functions still have unguarded behavior, organized by module, so that effort is directed where it matters most.

**Why this priority**: Without a module-level breakdown, the engineer cannot prioritize which tests to write. This is the foundation of the whole feature.

**Independent Test**: Can be fully tested by reading the mutation results report and producing a grouping by module; delivers the complete list of surviving mutants to be addressed.

**Acceptance Scenarios**:

1. **Given** the mutation results report exists, **When** the report is read, **Then** all surviving mutants are identified and grouped by source module.
2. **Given** a group of survivors for a module, **When** the list is presented, **Then** each survivor references the exact source file, function and mutation.

---

### User Story 2 - Skip Survivors Already Killed by Existing Tests (Priority: P2)

Not every reported survivor is genuinely unprotected; some are already covered by tests written after the last mutation run. The engineer must not waste effort rewriting coverage that exists.

**Why this priority**: Avoids redundant work and keeps the test suite clean; must be done before writing any new test.

**Independent Test**: Can be fully tested by taking a survivor and verifying that the current test suite already exercises the mutated behavior; delivers a shortlist of survivors that truly need new tests.

**Acceptance Scenarios**:

1. **Given** a surviving mutant, **When** its behavior is compared with the existing tests, **Then** if a test already guards that behavior the survivor is skipped.
2. **Given** a skipped survivor, **When** the work is reviewed, **Then** no test file is modified for that survivor.

---

### User Story 3 - Write Targeted Tests for Genuinely Uncovered Survivors (Priority: P1)

For survivors not covered by existing tests, the engineer must add tests that specifically detect the mutated behavior, so the next mutation run kills them.

**Why this priority**: This is the core value delivered: raising the mutation score toward the 80% quality gate.

**Independent Test**: Can be fully tested by adding a test that targets the mutated expression and confirming the targeted test passes against the current source.

**Acceptance Scenarios**:

1. **Given** a survivor without existing coverage, **When** a new test is written, **Then** the test asserts on the exact behavior the mutation would alter.
2. **Given** a written test, **When** the test is executed, **Then** it passes against the current (unmutated) source.
3. **Given** all new tests, **When** the mutation tool is later run manually by the user, **Then** the addressed survivors are reported as killed.

---

### User Story 4 - Verify Lint and Full Test Suite (Priority: P2)

After all test changes, the engineer must ensure no regression: linting rules still pass and the whole test suite is green.

**Why this priority**: The quality gate enforces both code style and test health; failing either blocks delivery.

**Independent Test**: Can be fully tested by running the project lint and the full test suite; delivers a green, regression-free codebase.

**Acceptance Scenarios**:

1. **Given** the completed test changes, **When** the lint is executed, **Then** no new lint findings are reported.
2. **Given** the completed test changes, **When** the full test suite is executed, **Then** all tests pass.
3. **Given** any failure found, **When** the failure is reported, **Then** it is corrected and the lint/test is re-run successfully.

---

### Edge Cases

- A survivor may be an "equivalent mutant" that no behavioral test can kill; the process uses static heuristics to flag known equivalent mutation patterns (e.g., string literal changes in log calls, default-value swaps in unreachable branches, mutations in type annotations) and documents them in the report for human confirmation rather than forcing artificial tests.
- A module may have no dedicated test file; the test must be placed in the closest existing test file covering that module. If no test file exists for the entire source package, a new test file is created at the conventional location (`tests/<package>/test_<module>.py`).
- Mutations of string literals in log messages or dict keys are only killable if a test asserts on the exact emitted value.
- Boundary mutations (e.g., `>` vs `>=`, default `0` vs `1`) require tests at the exact boundary value.
- The mutation report may be stale relative to recently updated tests; survivors must be validated against the current test suite before writing anything.

## Constitution Check *(mandatory)*

**Engaged Principles**:
- **Evidence First (V)**: the feature preserves traceability — each new test documents which mutant it kills.
- **Layer Independence (XIV)**: tests are written per module/plugin without coupling layers.
- **Observability as a Native Capability (XI)**: several survivors are log-statement mutations; the tests guard observable output.
- **Quality & Governance**: the work directly serves the project's quality gate and governance rules.

**Compliance Notes**:
- The feature does not alter runtime behavior; it only strengthens the test suite, which is permitted and encouraged by the governance model.
- No `mutmut` execution is performed by the automated workflow; the user runs it manually, respecting the constraint in the description.
- Tests are written in the existing test layout (`tests/...`) mirroring module structure, respecting architectural layer boundaries.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The process MUST read `mutants/mutmut-cicd-results.log` and identify every surviving mutant.
- **FR-002**: The survivors MUST be grouped by source module, with each entry identifying file, function and mutation type.
- **FR-002a**: The classification and test-writing process MUST operate in a single automated pass over all modules, without requiring per-module human confirmation.
- **FR-003**: For each survivor, the process MUST determine whether the current test suite already guarantees its death by statically analyzing the mutation diff to check if existing tests exercise the mutated code path.
- **FR-004**: Survivors already guarded by existing tests MUST be skipped without modifying any test file.
- **FR-005**: For each unguarded survivor, the process MUST add one or more tests that specifically assert on the behavior the mutation alters.
- **FR-006**: The `mutmut` tool MUST NOT be executed at any point during this work; the user runs it manually.
- **FR-007**: Each modified or inserted test MUST be executed individually to confirm it passes against the current source.
- **FR-008**: At the end, the project lint MUST be executed and any reported failure MUST be fixed.
- **FR-009**: At the end, the complete test suite MUST be executed and any reported failure MUST be fixed.
- **FR-010**: The process MUST produce a standalone Markdown report (e.g., `mutants/survivor-analysis.md`) classifying every survivor as *already guarded* or *needs new test* with rationale.
- **FR-011**: The process MUST apply static heuristics to flag likely equivalent mutants (e.g., string literal mutations in log calls, type annotation mutations, unreachable-branch mutations) and classify them in the report for human review rather than writing tests for them.

### Key Entities

- **Surviving Mutant**: a record in the report with source module, function, mutation id, original token and mutated token.
- **Source Module**: the unit of grouping (e.g., `specmetrics.plugins.rule_pack._handlers`).
- **Guard Test**: a test whose assertions change their outcome when the target mutation is applied.

## Clarifications

### Session 2026-08-10

- Q: What form does the "documented rationale" for survivor classification take? → A: A standalone Markdown report file (e.g., `mutants/survivor-analysis.md`) generated alongside test changes.
- Q: What processing strategy should handle the 8,822 survivors — interactive per module or fully automated? → A: Process all modules in a single automated pass (no per-module human confirmation).
- Q: How should equivalent mutants be identified — manual review, automated heuristic, or treat none as equivalent? → A: Static heuristic flagging known equivalent mutation patterns (e.g., string literal changes in logging, default-value swaps in unreachable branches), documented in the report for human confirmation.
- Q: How should the process detect whether an existing test already guards a mutant? → A: Static analysis — inspect the mutation's affected source lines from the diff and check whether existing test coverage already exercises the mutated code path.
- Q: What should happen when no test file exists for an entire source package? → A: Create a new test file at the conventional location (`tests/<package>/test_<module>.py`) for each module lacking one.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every survivor in the report is classified as either *already guarded* or *needs new test* with a documented rationale in a standalone Markdown report file (e.g., `mutants/survivor-analysis.md`).
- **SC-002**: Every survivor classified as *needs new test* has at least one added test targeting its mutated expression.
- **SC-003**: 100% of the added/modified tests pass when run against the current source.
- **SC-004**: The lint step completes with zero new findings after the changes.
- **SC-005**: The complete test suite runs green after the changes.
- **SC-006**: The mutation tool is never invoked during the automated workflow (verified by the absence of any mutation run in the process).

## Assumptions

- The mutation report reflects the state at the time it was generated; survivors are validated against the current source and tests before action.
- Survivors that are semantically equivalent (no behavioral test can distinguish them) are documented and skipped rather than forcing artificial tests.
- Test files follow the existing layout under `tests/`, mirroring the source module structure.
- The user will run `mutmut` manually after this work to confirm the addressed survivors are killed.
- The lint and test commands used are the ones defined in the project's quality tooling (ruff/flake8 for lint; pytest for tests).
