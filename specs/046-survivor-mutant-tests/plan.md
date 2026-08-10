# Implementation Plan: Eliminate Surviving Mutants with Targeted Tests

**Branch**: `046-survivor-mutant-tests` | **Date**: 2026-08-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/046-survivor-mutant-tests/spec.md`

## Summary

Execute an automated, single-pass analysis of 8,822 surviving mutants from `mutants/mutmut-cicd-results.log` (157 source modules). For each survivor, apply static diff-based analysis to determine whether existing tests already guard the mutation. Generate targeted pytest tests for unguarded survivors, flag likely equivalent mutants via static heuristics, and produce a standalone Markdown classification report (`mutants/survivor-analysis.md`). Validate all changes with individual test runs, a full test suite pass, and `ruff` lint. Never execute `mutmut`.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: pytest, ruff, structlog (project defaults; no new dependencies)

**Storage**: Input: `mutants/mutmut-cicd-results.log` (102,735 lines, unified diff format). Output: Markdown report + test file modifications.

**Testing**: pytest (individual test runs per FR-007, full suite per FR-009)

**Target Platform**: Linux (local CLI execution)

**Project Type**: AI-assisted development workflow (test hardening campaign)

**Performance Goals**: Reasonable human-scale execution — the workflow processes 8,822 survivors sequentially; no strict latency target but should complete in a single session.

**Constraints**: `mutmut` MUST NOT be executed (FR-006). All guard detection is static (no dynamic mutation application). Test placement follows existing `tests/` directory conventions.

**Scale/Scope**: 8,822 survivors across 157 source files, grouped into approximately 50–60 modules (by source package).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**:
- **Evidence First (V)**: Each added test carries a comment referencing the mutant it kills; the Markdown report provides a full audit trail.
- **Layer Independence (XIV)**: Tests are written per module without coupling layers; test files mirror source module structure.
- **Observability as a Native Capability (XI)**: Log-statement mutations are guarded by tests asserting on structured log output.
- **Quality & Governance**: Work directly serves the project's mutation score quality gate.

**Compliance Verifications**:
- [x] Specification First: The primary input is the feature specification; mutation report is data, not the spec itself.
- [x] Evidence First: Mutant-to-test traceability is preserved in the report and test comments.
- [x] Canonical Representation: Not applicable — this workflow does not operate on the CFM pipeline.
- [x] Plugin-Oriented: Not applicable — this is a one-shot development task, not a platform plugin.
- [x] Rule Externalization: Not applicable — no organization-specific policies are encoded.
- [x] Layer Independence: Tests are organized per module matching the architectural layers.
- [x] Open by Default: Results are published as a plain Markdown report alongside the test suite.

**Gate Result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/046-survivor-mutant-tests/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A — no external interfaces)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

This feature does not introduce new source code modules. It produces:

```text
mutants/
└── survivor-analysis.md          # Classification report (FR-010)

tests/                            # Existing test tree, modified with new tests
├── unit/                         # New tests for uncovered source modules
├── integration/                  # New tests where appropriate
└── plugins/                      # New tests for plugin modules lacking coverage
```

**Structure Decision**: All work is confined to `tests/` (test additions) and `mutants/` (report). No changes to application source code.

## Complexity Tracking

> No constitution violations to justify.
