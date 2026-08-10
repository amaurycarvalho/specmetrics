# Tasks: Quality Gate for CI and Release Builds

**Input**: Design documents from `/specs/043-quality-gate-implementation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: No formal test tasks are generated — the feature specification does not request TDD/unit tests. Each user story includes its independent validation scenario from `quickstart.md` instead.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **This feature (CI/tooling)**: `.github/workflows/ci.yml`, `.github/workflows/build-wheel.yml`, `Makefile`, `pyproject.toml`, `scripts/` at repository root
- No changes to `specmetrics/` application code — the gate operates on the repo as-is
- Thresholds reference `research.md` (R-2) and `contracts/contracts.md`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Declare the quality tooling so all later phases can install and run it reproducibly.

- [X] T001 Add `[project.optional-dependencies].quality` group to `pyproject.toml` with pinned tool versions from research.md R-2 (ruff, flake8, flake8-bugbear, flake8-annotations, flake8-docstrings, radon, xenon, lizard, jscpd, pytest, pytest-cov, mutatest, semgrep)
- [X] T002 Add `make install-quality-tools` target to `Makefile` that installs the `.quality` extra into `$(VENV)`
- [X] T003 [P] Add `.quality` extra to `Makefile` `.PHONY` declaration (venv, install, test, build, lint, install-quality-tools)

**Checkpoint**: `make install-quality-tools` succeeds and all quality tools are available in `.venv`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The local quality gate commands MUST exist before ANY user story can be implemented — both the PR gate (US2) and release gate (US1) consume them.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `make test` coverage enforcement to `Makefile`: run pytest with `--cov=.`, `--cov-report=xml:coverage.xml`, `--cov-report=term-missing`, `--cov-fail-under=85` (FR-004)
- [X] T005 Add `make complexity` target to `Makefile`: radon cc, radon mi, xenon and lizard with thresholds from research.md R-2 (complexity < 10 blocking, SLOC < 100 warning)
- [X] T006 Add `make duplication` target to `Makefile`: jscpd with `--threshold 5`, ignoring `**/tests/**` and `**/venv/**` (FR-004)
- [X] T007 Add `make mutation` target to `Makefile`: mutatest using `coverage.xml` with `--fail-under 80` (FR-004)
- [X] T008 Add `make security` target to `Makefile`: semgrep with ERROR-severity findings blocking (clarified: security blocking by default; FR-004)
- [X] T009 [P] Create `scripts/quality_gate.py` — runner that executes each check via subprocess, captures metric value, threshold, severity, status and evidence (affected files) per QualityCheck (data-model.md; FR-003, FR-007)
- [X] T010 Implement fail-loud behavior in `scripts/quality_gate.py`: a tool that errors or cannot execute marks the check `fail` (status `fail`, severity `blocking`) and exits non-zero (FR-008)
- [X] T011 Create `scripts/mutatest_gate.py` — mutation runner invoking mutatest and failing when survival is below 80% (FR-004, research.md R-2)
- [X] T012 Add `make quality-gate` target to `Makefile` composing: install-quality-tools → lint → complexity → duplication → test → mutation → security, exiting non-zero if any blocking check fails (FR-001, FR-005)

**Checkpoint**: `make quality-gate` runs locally on a clean tree and exits 0 (or reports the current failing metrics with evidence).

---

## Phase 3: User Story 1 - Release Build Only Happens on Verified Code (Priority: P1) 🎯 MVP

**Goal**: `build-wheel.yml` runs the full CI quality gate before building; a failed gate aborts the release.

**Independent Test** (quickstart Scenario 4): With a deliberate violation present, triggering a release skips `build` and publishes nothing; with all checks passing, the release builds and publishes.

### Implementation for User Story 1

- [X] T013 [P] [US1] Add `workflow_call:` trigger to `.github/workflows/ci.yml` so the CI (lint, test, quality-gate) is reusable by the release workflow (research.md R-1)
- [X] T014 [US1] Add a `quality-gate` job to `.github/workflows/build-wheel.yml` that calls the reusable CI via `uses: ./.github/workflows/ci.yml` (research.md R-1)
- [X] T015 [US1] Add `needs: quality-gate` to the `build` job in `.github/workflows/build-wheel.yml` so the build is skipped when the gate fails (FR-001, SC-001)
- [X] T016 [US1] Validate the manual release version in `.github/workflows/build-wheel.yml` (workflow_dispatch `inputs.version`): abort with a clear error if missing/invalid before publishing (FR-009)

**Checkpoint**: A release with a failing gate produces no artifact; a passing gate builds and publishes `dist/*.whl` under the validated version.

---

## Phase 4: User Story 2 - Pull Requests Are Gated by Quality (Priority: P2)

**Goal**: `ci.yml` runs the quality gate on every PR to `main`; violating PRs are blocked from merging.

**Independent Test** (quickstart Scenario 3): A PR that drops coverage below 85% fails the `quality-gate` job and cannot merge; fixing it turns the PR green.

### Implementation for User Story 2

- [X] T017 [P] [US2] Add `quality-gate` job to `.github/workflows/ci.yml` running `make install-quality-tools` and `make quality-gate` (FR-002)
- [X] T018 [P] [US2] Run the `quality-gate` job on the Python 3.12/3.13 matrix with venv caching keyed on `pyproject.toml` hash (FR-010, research.md R-3)
- [X] T019 [US2] Upload `coverage.xml` and the mutation report as CI artifacts per Python version in the `quality-gate` job (FR-010)

**Checkpoint**: A PR violating any blocking threshold is reported failing; a clean PR passes the gate on all Python versions.

---

## Phase 5: User Story 3 - Maintainers Get a Readable Quality Report (Priority: P3)

**Goal**: Every gate run produces a single consolidated report listing every metric, its value, threshold and pass/warn/fail status per Python version.

**Independent Test** (quickstart Scenario 5): After one CI run, the report lists all metrics with values, thresholds and statuses, distinguishable per Python version.

### Implementation for User Story 3

- [X] T020 [P] [US3] Implement consolidated report generation in `scripts/quality_gate.py`: emit a JSON report (run_id, python_version, timestamp, checks with name/value/threshold/severity/status/evidence, overall_status) per contract 4 in `contracts/contracts.md` (FR-006)
- [X] T021 [US3] Derive `overall_status` in `scripts/quality_gate.py`: `pass` iff no blocking check is `fail` and no tool errored (data-model.md; FR-005)
- [X] T022 [US3] Print a human-readable summary from `scripts/quality_gate.py` highlighting failing checks with their evidence (affected files) (FR-007, SC-003)

**Checkpoint**: `make quality-gate` produces both a readable summary and a machine-readable JSON report with traceable evidence for any failure.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Hardening, exceptions process, and release traceability.

- [X] T023 [P] Document the quality exception process (scope, duration, rationale, approver) as a `QualityException` record following data-model.md, published in `docs/` (FR-011)
- [X] T024 [P] Record `ReleaseVerification` (version, passing run_id, artifact) in the release body/notes so every artifact traces to a passing gate run (SC-001, SC-005)
- [X] T025 Update `README.md` with the new quality commands (`make quality-gate`, individual check targets) and the RFC-043 metric table
- [X] T026 [P] Add `.gitignore` entries for gate artifacts if not already present (`coverage.xml`, mutation report)
- [X] T027 Run `quickstart.md` end-to-end and confirm all five scenarios pass on a clean checkout

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) depend on the reusable `quality-gate` job in `ci.yml` (T013); they can proceed in parallel once T013 lands
  - US3 (Phase 5) depends on the check execution from Phase 2 and can proceed independently of US1/US2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — depends on T013 (`workflow_call` in ci.yml), which is also the base for US2
- **User Story 2 (P2)**: Can start after Foundational — shares T013 and the Phase 2 gate targets with US1, but is independently testable
- **User Story 3 (P3)**: Can start after Foundational — no dependency on US1/US2

### Within Each User Story

- Phase 2 gate commands must exist and pass before story work
- ci.yml reusable changes (T013) before release wiring (T014/T015)
- Validation scenario from quickstart.md is the completion gate for each story

### Parallel Opportunities

- All Phase 1 Setup tasks marked [P] can run in parallel
- Phase 2 script tasks (T009-T011) can run in parallel; Makefile targets depend on them
- Once T013 lands, US1 (T014-T016) and US2 (T017-T019) can proceed in parallel
- US3 (T020-T022) is fully parallel to US1/US2
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# T013 must land first (reusable CI), then:
Task: "Add quality-gate job calling reusable CI in .github/workflows/build-wheel.yml"
Task: "Wire needs: quality-gate on build job in .github/workflows/build-wheel.yml"
```

## Parallel Example: User Story 2

```bash
Task: "Add quality-gate job in .github/workflows/ci.yml"
Task: "Matrix + venv caching for quality-gate job in .github/workflows/ci.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (pyproject deps, install-quality-tools)
2. Complete Phase 2: Foundational (all gate targets + scripts — CRITICAL, blocks everything)
3. Complete Phase 3: User Story 1 (reusable CI + release wiring)
4. **STOP and VALIDATE**: Run quickstart Scenario 4 — release gating works end-to-end
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → local `make quality-gate` works
2. Add User Story 1 → releases are protected (MVP!)
3. Add User Story 2 → PRs are gated → main stays healthy
4. Add User Story 3 → actionable reports for failures
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once T013 (reusable CI) is done:
   - Developer A: User Story 1 (release wiring)
   - Developer B: User Story 2 (PR gating)
   - Developer C: User Story 3 (reporting)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable via its quickstart scenario
- Verify the gate fails on a seeded violation before celebrating a pass
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
