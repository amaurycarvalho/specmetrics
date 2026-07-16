---
description: "Task list for OpenSpec Specification Adapter implementation"

---

# Tasks: Specification Plugin — OpenSpec

**Input**: Design documents from `specs/019-specification-plugin-openspec/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to verify repository detection, artifact discovery, document normalization, metadata preservation, and error handling.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/adapter/openspec/`, `tests/` at repository root
- Paths below follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the OpenSpec adapter plugin.

- [ ] T001 Create `specmetrics/plugins/adapter/openspec/` package with `__init__.py`
- [ ] T002 [P] Create `tests/unit/adapter/openspec/` directory structure
- [ ] T003 [P] Create `tests/integration/adapter/openspec/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core adapter class, document model integration, and protocol conformance that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Implement `OpenSpecAdapter` skeleton class in `specmetrics/plugins/adapter/openspec/plugin.py` with method stubs for `supports()`, `scan()`, `scan_specs()`, `scan_changes()`, `normalize_document()`, and `build_metadata()` per `data-model.md`
- [ ] T005 [P] Implement `ScanResult`, `ScanError`, and `ScanStats` data classes in `specmetrics/plugins/adapter/openspec/plugin.py` per `data-model.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 4 — Detect OpenSpec Repositories (Priority: P1) 🎯 MVP

**Goal**: The Plugin Registry can evaluate whether a repository uses the OpenSpec convention by calling `supports()`, enabling automatic adapter selection.

**Independent Test**: Point `supports()` at a directory containing `openspec/specs/` → True. Point at a directory without it → False.

### Tests for User Story 4

- [ ] T006 [P] [US4] Unit test for `supports()` returning True when `openspec/specs/` exists in `tests/unit/adapter/openspec/test_plugin.py` — covers FR-001.
- [ ] T007 [P] [US4] Unit test for `supports()` returning False when `openspec/` is missing in `tests/unit/adapter/openspec/test_plugin.py`.
- [ ] T008 [P] [US4] Unit test for `supports()` returning False when only `openspec/` exists but no `openspec/specs/` in `tests/unit/adapter/openspec/test_plugin.py`.
- [ ] T009 [P] [US4] Unit test that `supports()` does not perform a full scan (fast path only) in `tests/unit/adapter/openspec/test_plugin.py` — covers FR-002.

### Implementation for User Story 4

- [ ] T010 [US4] Implement `supports()` in `specmetrics/plugins/adapter/openspec/plugin.py` — check for `openspec/specs/` directory existence using `Path.exists()`. Return False if either `openspec/` or `openspec/specs/` is missing. Covers FR-001, FR-002.
- [ ] T011 [US4] Integration test: repository detection with real filesystem fixtures in `tests/integration/adapter/openspec/test_full_scan.py`.

**Checkpoint**: US4 complete — OpenSpec repositories can be automatically detected.

---

## Phase 4: User Story 1 — Discover Current Specifications (Priority: P1)

**Goal**: The adapter discovers every specification document under `openspec/specs/` and exposes them as normalized Documents to the pipeline.

**Independent Test**: Create an OpenSpec repository with multiple domains under `openspec/specs/`; verify every `spec.md` is returned as a normalized Document with correct domain metadata.

### Tests for User Story 1

- [ ] T012 [P] [US1] Unit test for recursive spec discovery in `tests/unit/adapter/openspec/test_scanner.py` — verify `openspec/specs/**/spec.md` matches all spec files. Covers FR-005.
- [ ] T013 [P] [US1] Unit test for empty `openspec/specs/` returning zero documents in `tests/unit/adapter/openspec/test_scanner.py` — covers Edge Cases: Missing specs/ directory.
- [ ] T014 [P] [US1] Unit test for nested domain discovery (e.g., `specs/auth/api/spec.md`) in `tests/unit/adapter/openspec/test_scanner.py`.
- [ ] T015 [P] [US1] Unit test for domain metadata extraction from parent directory name in `tests/unit/adapter/openspec/test_metadata.py`.

### Implementation for User Story 1

- [ ] T016 [US1] Implement `scan_specs()` in `specmetrics/plugins/adapter/openspec/scanner.py` — use `path.glob("openspec/specs/**/spec.md")` to discover all specification documents. Covers FR-005.
- [ ] T017 [US1] Implement `normalize_document()` in `specmetrics/plugins/adapter/openspec/normalizer.py` — read file content as UTF-8 text, parse ATX headings (`#` through `######`) to build `DocumentSection` hierarchy, construct canonical `Document` with raw Markdown content and section list. Covers FR-008, FR-009, FR-010.
- [ ] T018 [US1] Implement `build_metadata()` for specs in `specmetrics/plugins/adapter/openspec/metadata.py` — derive domain from parent directory name under `specs/`, set `kind: current-spec`, `status: active`, `artifact_type: specification`. Covers FR-012, FR-013.
- [ ] T019 [US1] Wire `scan()` method in `plugin.py` — call `scan_specs()`, normalize each discovered file, collect results into `ScanResult`, handle empty result gracefully. Covers FR-003 (current specifications).
- [ ] T020 [US1] Integration test: full spec scan with multiple domains in `tests/integration/adapter/openspec/test_full_scan.py`.

**Checkpoint**: US1 complete — current specification baseline is discovered and normalized.

---

## Phase 5: User Story 2 — Discover Active Changes (Priority: P1)

**Goal**: The adapter discovers all active and archived change artifacts, including proposal, design, tasks, and delta specification documents.

**Independent Test**: Create two active changes and one archived change; verify all artifacts are returned with correct metadata (change ID, active/archived status).

### Tests for User Story 2

- [ ] T021 [P] [US2] Unit test for active change directory enumeration in `tests/unit/adapter/openspec/test_scanner.py` — verify `openspec/changes/*/` lists all active changes. Covers FR-006.
- [ ] T022 [P] [US2] Unit test for archived change discovery under `openspec/changes/archive/` in `tests/unit/adapter/openspec/test_scanner.py` — covers FR-007.
- [ ] T023 [P] [US2] Unit test for temp folder exclusion in change directories in `tests/unit/adapter/openspec/test_scanner.py` — verify `.git`, `__pycache__`, `.venv`, `node_modules`, `.specify`, and `_`-prefixed folders are excluded. Covers FR-006.
- [ ] T024 [P] [US2] Unit test for missing optional artifacts (`design.md`, `tasks.md`) in `tests/unit/adapter/openspec/test_scanner.py` — covers Edge Cases.
- [ ] T025 [P] [US2] Unit test for delta spec discovery under `changes/<change>/specs/**/spec.md` in `tests/unit/adapter/openspec/test_scanner.py` — covers clarify session decision on delta spec path pattern.
- [ ] T026 [P] [US2] Unit test for archived status metadata in `tests/unit/adapter/openspec/test_metadata.py` — verify changes under `archive/` have `status: archived`. Covers FR-018.
- [ ] T027 [P] [US2] Unit test for empty change folders returning no artifacts in `tests/unit/adapter/openspec/test_scanner.py` — covers Edge Cases.

### Implementation for User Story 2

- [ ] T028 [US2] Implement `scan_changes()` in `specmetrics/plugins/adapter/openspec/scanner.py` — list directories under `openspec/changes/*/` excluding temp folders, then under `openspec/changes/archive/*/` for archived changes. For each change directory, discover proposal.md, design.md, tasks.md, and `specs/**/spec.md`. Covers FR-006, FR-007.
- [ ] T029 [US2] Implement `build_metadata()` for change artifacts in `specmetrics/plugins/adapter/openspec/metadata.py` — derive `change` from change directory name, `kind` from artifact type (proposal, design, tasks, delta-spec), `status` from `archive/` path presence, `domain` from delta spec's parent domain directory. Covers FR-014, FR-015, FR-016, FR-017, FR-018.
- [ ] T030 [US2] Wire change discovery into `scan()` in `plugin.py` — call `scan_changes()`, normalize artifacts, merge with spec results. Handle missing `changes/` directory gracefully. Covers FR-003 (active + archived changes).
- [ ] T031 [US2] Integration test: full scan with active and archived changes in `tests/integration/adapter/openspec/test_full_scan.py`.

**Checkpoint**: US2 complete — all OpenSpec change artifacts are discovered and normalized.

---

## Phase 6: User Story 3 — Preserve OpenSpec Metadata (Priority: P1)

**Goal**: Every normalized document preserves OpenSpec-specific metadata (domain, change, status, artifact type) without semantic interpretation, enabling downstream traceability.

**Independent Test**: Verify every normalized Document contains the full metadata set: framework, repository_root, artifact_type, domain, change, status, relative_path. Verify metadata values match the repository structure.

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for minimum metadata completeness in `tests/unit/adapter/openspec/test_metadata.py` — verify every Document has `framework`, `repository_root`, `artifact_type`, `domain`, `change`, `status`, `relative_path`. Covers FR-012.
- [ ] T033 [P] [US3] Unit test for spec domain metadata extraction in `tests/unit/adapter/openspec/test_metadata.py` — verify `domain` is the parent directory name under `specs/`.
- [ ] T034 [P] [US3] Unit test for change identifier metadata in `tests/unit/adapter/openspec/test_metadata.py` — verify `change` is the change directory name.
- [ ] T035 [P] [US3] Unit test for artifact type mapping — verify each filename maps to correct `artifact_type` per FR-004 table. Covers FR-004.
- [ ] T036 [P] [US3] Unit test for unknown file handling in `tests/unit/adapter/openspec/test_metadata.py` — verify unrecognized `.md` files get `artifact_type: unknown` and `kind: unknown`. Covers clarify session decision.

### Implementation for User Story 3

- [ ] T037 [US3] Implement artifact type resolution in `specmetrics/plugins/adapter/openspec/metadata.py` — build filename→type mapping from FR-004 table. Unrecognized filenames map to `unknown`. Covers FR-004.
- [ ] T038 [US3] Implement `build_metadata()` full logic in `specmetrics/plugins/adapter/openspec/metadata.py` — integrate all metadata rules: framework (always `openspec`), repository_root (absolute path), artifact_type (from filename mapping), domain (from parent dir under `specs/`), change (from change dir name), status (`archived` if path contains `archive/`, else `active`), relative_path (relative to repo root). Covers FR-012–FR-018.
- [ ] T039 [US3] Implement section hierarchy preservation in `specmetrics/plugins/adapter/openspec/normalizer.py` — parse Markdown ATX headings (`#` through `######`) into `DocumentSection` tree; attach non-heading content to preceding section. Covers FR-010.
- [ ] T040 [US3] Integration test: metadata preservation end-to-end in `tests/integration/adapter/openspec/test_full_scan.py`.

**Checkpoint**: US3 complete — all documents carry complete, traceable OpenSpec metadata.

---

## Phase 7: Error Handling & Edge Cases

**Purpose**: Error isolation, malformed file handling, and robustness for production use.

- [ ] T041 [P] Implement per-file try/except in `scanner.py` — wrap each file read in try/except; unreadable files produce `ScanError` with `UNREADABLE` code; scan continues to next file. Covers FR-021, FR-023.
- [ ] T042 [P] Implement malformed Markdown handling in `normalizer.py` — if heading parsing fails, return document with raw content and empty sections list; do not raise. Covers FR-022.
- [ ] T043 [P] Implement corrupted UTF-8 handling in `normalizer.py` — catch `UnicodeDecodeError`, produce `ScanError` with `ENCODING_ERROR` code, continue scan. Covers Edge Cases: Corrupted UTF-8 files.
- [ ] T044 [P] Implement symbolic link resolution in `scanner.py` — follow symlinks during glob discovery; if a symlink is broken, log warning and skip. Covers Edge Cases: Symbolic links.
- [ ] T045 [P] Unit test for per-file error isolation in `tests/unit/adapter/openspec/test_scanner.py` — verify one unreadable file does not block other files. Covers SC-003.
- [ ] T046 [P] Unit test for duplicate domain name handling in `tests/unit/adapter/openspec/test_scanner.py` — two domains with same name under different paths produce separate Documents. Covers Edge Cases.

---

## Phase 8: Observability & Polish

- [ ] T047 [P] Implement structured INFO/ERROR logging in `plugin.py` — log scan start, completion, per-file errors, and artifact count summary via structlog. Covers FR-024.
- [ ] T048 [P] Performance benchmark test in `tests/unit/adapter/openspec/test_scanner.py` — verify 500 artifacts scanned in under 5 seconds. Covers SC-001.
- [ ] T049 [P] Register plugin entry point in `pyproject.toml` — add `[project.entry-points."specmetrics.plugins.adapter"] openspec = "specmetrics.plugins.adapter.openspec:OpenSpecAdapter"`. Covers FR-019.
- [ ] T050 [P] Implement plugin metadata in `plugin.py` — expose `plugin_id`, `plugin_version`, `supported_framework`, `supported_artifact_types`. Covers FR-020.

---

## Dependencies

```text
Phase 1 (Setup)
  └─► Phase 2 (Foundational: adapter skeleton + data classes)
        ├─► Phase 3 (US4: Repository Detection) ◄── MVP
        │     ├─► Phase 4 (US1: Current Specs)
        │     │     ├─► Phase 5 (US2: Active Changes)
        │     │     └─► Phase 6 (US3: Metadata)
        │     └─► Phase 7 (Error Handling)
        └─► Phase 8 (Observability & Polish)
```

## Parallel Execution Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003 (directory creation) |
| Phase 2 | T004, T005 (skeleton + data classes) |
| Phase 3 (US4) | T006–T009 (all tests); T010 (implementation) |
| Phase 4 (US1) | T012–T015 (tests); T016 (scanner), T017 (normalizer), T018 (metadata) are independent |
| Phase 5 (US2) | T021–T027 (tests); T028 (change scanner), T029 (metadata) |
| Phase 6 (US3) | T032–T036 (tests); T037, T038, T039 (each module) |
| Phase 7 | T041–T046 (all independent) |
| Phase 8 | T047–T050 (all independent) |

## Implementation Strategy

### MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US4)** — Repository detection is the lightest MVP increment:
- Directory structure, adapter skeleton, data classes
- `supports()` implementation with path existence check
- Fast repository detection without scanning

**Value at MVP**: The Plugin Registry can automatically select the OpenSpec adapter when a repository follows the OpenSpec convention.

### Incremental Delivery

1. **MVP** (Phase 1–3): Repository detection only
2. **US1** (Phase 4): Discover and normalize current specifications
3. **US2** (Phase 5): Add active and archived change discovery
4. **US3** (Phase 6): Full metadata preservation and section hierarchy
5. **Error handling** (Phase 7): Robustness for production use
6. **Polish** (Phase 8): Observability, benchmarks, entry point registration

Each phase is independently testable and adds production value without breaking previous phases.

---

## Summary

| Phase | User Story | Tasks | Priority |
|-------|-----------|-------|----------|
| 1 | Setup | 3 | Required |
| 2 | Foundational | 2 | Required |
| 3 | US4: Detect OpenSpec Repositories | 6 | P1 🎯 MVP |
| 4 | US1: Discover Current Specs | 9 | P1 |
| 5 | US2: Discover Active Changes | 11 | P1 |
| 6 | US3: Preserve OpenSpec Metadata | 9 | P1 |
| 7 | Error Handling & Edge Cases | 6 | Cross-cutting |
| 8 | Observability & Polish | 4 | Cross-cutting |
| **Total** | | **50** | |
