---
description: "Task list for SpecKit Specification Adapter implementation"

---

# Tasks: Specification Plugin — SpecKit

**Input**: Design documents from `specs/020-specification-plugin-speckit/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to verify repository detection, governance discovery, feature workspace scanning, document normalization, metadata preservation, and error handling.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/plugins/adapter/speckit/`, `tests/` at repository root
- Paths below follow the structure defined in plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the SpecKit adapter plugin.

- [ ] T001 Create `specmetrics/plugins/adapter/speckit/` package with `__init__.py`
- [ ] T002 [P] Create `tests/unit/adapter/speckit/` directory structure
- [ ] T003 [P] Create `tests/integration/adapter/speckit/` directory structure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core adapter class, document model integration, and protocol conformance that MUST be complete before any user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 [P] Implement `SpecKitAdapter` skeleton class in `specmetrics/plugins/adapter/speckit/plugin.py` with method stubs for `supports()`, `scan()`, `scan_memory()`, `scan_features()`, `normalize_document()`, and `build_metadata()` per `data-model.md`
- [ ] T005 [P] Implement `ScanResult`, `ScanError`, and `ScanStats` data classes in `specmetrics/plugins/adapter/speckit/plugin.py` per `data-model.md`

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 4 — Detect SpecKit Repositories (Priority: P1) 🎯 MVP

**Goal**: The Plugin Registry can evaluate whether a repository uses the SpecKit convention by calling `supports()`, enabling automatic adapter selection.

**Independent Test**: Point `supports()` at a directory containing `.specify/` → True. Point at a directory containing `specs/` → True. Point at a directory with none → False.

### Tests for User Story 4

- [ ] T006 [P] [US4] Unit test for `supports()` returning True when `.specify/` exists in `tests/unit/adapter/speckit/test_plugin.py` — covers FR-001 marker 1.
- [ ] T007 [P] [US4] Unit test for `supports()` returning True when `.specify/memory/constitution.md` exists in `tests/unit/adapter/speckit/test_plugin.py` — covers FR-001 marker 2.
- [ ] T008 [P] [US4] Unit test for `supports()` returning True when `specs/` exists in `tests/unit/adapter/speckit/test_plugin.py` — covers FR-001 marker 3.
- [ ] T009 [P] [US4] Unit test for `supports()` returning False when no SpecKit markers exist in `tests/unit/adapter/speckit/test_plugin.py`.
- [ ] T010 [P] [US4] Unit test that `supports()` does not perform a full scan (fast path only) in `tests/unit/adapter/speckit/test_plugin.py` — covers FR-002.

### Implementation for User Story 4

- [ ] T011 [US4] Implement `supports()` in `specmetrics/plugins/adapter/speckit/plugin.py` — check for `.specify/`, `.specify/memory/constitution.md`, or `specs/` existence using `Path.exists()`. Return True if any marker is present. Covers FR-001, FR-002.
- [ ] T012 [US4] Integration test: repository detection with real filesystem fixtures in `tests/integration/adapter/speckit/test_full_scan.py`.

**Checkpoint**: US4 complete — SpecKit repositories can be automatically detected.

---

## Phase 4: User Story 1 — Discover Governance Documents (Priority: P1)

**Goal**: The adapter discovers all governance artifacts under `.specify/memory/` and exposes them as normalized Documents to the pipeline.

**Independent Test**: Create a repository containing `.specify/memory/constitution.md`; verify it is returned as a normalized Document with `kind: governance` and `feature: null`.

### Tests for User Story 1

- [ ] T013 [P] [US1] Unit test for governance document discovery from `.specify/memory/` in `tests/unit/adapter/speckit/test_scanner.py` — covers FR-003.
- [ ] T014 [P] [US1] Unit test for missing `.specify/memory/` returning zero governance documents in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.
- [ ] T015 [P] [US1] Unit test for governance metadata in `tests/unit/adapter/speckit/test_metadata.py` — verify `feature: null`, `workspace: .specify/memory`, `kind: governance`. Covers FR-013.
- [ ] T016 [P] [US1] Unit test that only `.md` files under `.specify/memory/` are included (FR-006) in `tests/unit/adapter/speckit/test_scanner.py` — verify `.py`, `.yml`, `.sh` files under `.specify/` are excluded.

### Implementation for User Story 1

- [ ] T017 [US1] Implement `scan_memory()` in `specmetrics/plugins/adapter/speckit/scanner.py` — glob for `.specify/memory/**/*.md` to discover all governance documents. Covers FR-003, FR-006.
- [ ] T018 [US1] Implement `normalize_document()` in `specmetrics/plugins/adapter/speckit/normalizer.py` — read file content as UTF-8 text, parse ATX headings (`#` through `######`) to build `DocumentSection` hierarchy, construct canonical `Document` with raw Markdown content and section list. Covers FR-008, FR-009, FR-010.
- [ ] T019 [US1] Implement `build_metadata()` for governance documents in `specmetrics/plugins/adapter/speckit/metadata.py` — set `framework: speckit`, `artifact_type: constitution`, `kind: governance`, `feature: null`, `workspace: .specify/memory`. Covers FR-012, FR-013.
- [ ] T020 [US1] Wire `scan()` method in `plugin.py` — call `scan_memory()`, normalize each file, collect into `ScanResult`, handle empty `.specify/memory/` gracefully.
- [ ] T021 [US1] Integration test: governance scan with constitution.md in `tests/integration/adapter/speckit/test_full_scan.py`.

**Checkpoint**: US1 complete — governance documents are discovered and normalized.

---

## Phase 5: User Story 2 — Discover Feature Workspaces (Priority: P1)

**Goal**: The adapter discovers all feature artifacts under `specs/` including spec.md, plan.md, tasks.md, research.md, data-model.md, and checklists — with graceful handling of optional artifacts.

**Independent Test**: Create multiple feature directories under `specs/`; verify every artifact file is discovered and normalized. A feature containing only `spec.md` returns exactly one document.

### Tests for User Story 2

- [ ] T022 [P] [US2] Unit test for feature workspace discovery in `tests/unit/adapter/speckit/test_scanner.py` — verify `specs/<feature>/*.md` discovers all artifacts. Covers FR-004.
- [ ] T023 [P] [US2] Unit test for recursive checklist discovery `checklists/**/*.md` in `tests/unit/adapter/speckit/test_scanner.py` — covers clarify session decision.
- [ ] T024 [P] [US2] Unit test for feature containing only `spec.md` returning exactly one document in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.
- [ ] T025 [P] [US2] Unit test for missing optional artifacts (no plan.md, no tasks.md) in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.
- [ ] T026 [P] [US2] Unit test for empty `specs/` returning zero feature documents in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.
- [ ] T027 [P] [US2] Unit test for duplicate feature identifier detection in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.

### Implementation for User Story 2

- [ ] T028 [US2] Implement `scan_features()` in `specmetrics/plugins/adapter/speckit/scanner.py` — list directories under `specs/*/`, discover all `.md` files within each feature directory. Map recognized filenames to artifact types per FR-005 table. Use `checklists/**/*.md` for checklist discovery. Covers FR-004, FR-005.
- [ ] T029 [US2] Implement `build_metadata()` for feature artifacts in `specmetrics/plugins/adapter/speckit/metadata.py` — derive `feature` from parent directory name, `workspace` from `specs/<feature>`, `kind` from artifact type mapping (specification, architecture, implementation, research, data-model, checklist). Covers FR-014, FR-015, FR-016, FR-017, FR-018, FR-019.
- [ ] T030 [US2] Wire feature discovery into `scan()` in `plugin.py` — call `scan_features()`, normalize artifacts, merge with governance results into `ScanResult`. Covers FR-003, FR-004.
- [ ] T031 [US2] Integration test: full scan with multiple features and varied artifacts in `tests/integration/adapter/speckit/test_full_scan.py`.

**Checkpoint**: US2 complete — all feature workspace artifacts are discovered and normalized.

---

## Phase 6: User Story 3 — Preserve Feature Metadata (Priority: P1)

**Goal**: Every normalized document preserves SpecKit-specific metadata (feature identifier, workspace path, artifact type, kind) without semantic interpretation, enabling downstream traceability.

**Independent Test**: Verify every normalized Document contains the full metadata set: `framework`, `artifact_type`, `kind`, `feature`, `workspace`, `relative_path`. Governance docs have `feature: null`; feature artifacts have the correct feature identifier.

### Tests for User Story 3

- [ ] T032 [P] [US3] Unit test for minimum metadata completeness in `tests/unit/adapter/speckit/test_metadata.py` — verify every Document has `framework`, `artifact_type`, `kind`, `feature`, `workspace`, `relative_path`. Covers FR-012.
- [ ] T033 [P] [US3] Unit test for feature identifier extraction from parent directory in `tests/unit/adapter/speckit/test_metadata.py`.
- [ ] T034 [P] [US3] Unit test for artifact type mapping — verify each filename maps to correct `artifact_type` per FR-005 table. Covers FR-005.
- [ ] T035 [P] [US3] Unit test for unknown file handling in `tests/unit/adapter/speckit/test_metadata.py` — verify unrecognized `.md` files get `artifact_type: unknown` and `kind: unknown`. Covers FR-007.
- [ ] T036 [P] [US3] Unit test for data-model.md having `kind: data-model` (not `kind: research`) in `tests/unit/adapter/speckit/test_metadata.py` — covers clarify session decision.
- [ ] T037 [P] [US3] Unit test for governance vs feature distinction in `tests/unit/adapter/speckit/test_metadata.py` — covers SC-004.

### Implementation for User Story 3

- [ ] T038 [US3] Implement artifact type resolution in `specmetrics/plugins/adapter/speckit/metadata.py` — build filename→type mapping from FR-005 table. Unrecognized filenames map to `unknown`. Covers FR-005, FR-007.
- [ ] T039 [US3] Implement `build_metadata()` full logic in `specmetrics/plugins/adapter/speckit/metadata.py` — integrate all metadata rules: framework (always `speckit`), artifact_type (from filename mapping), kind (from type-specific rules), feature (parent dir name under `specs/`, null for governance), workspace (`.specify/memory` or `specs/<feature>`), relative_path (relative to repo root). Covers FR-012–FR-019.
- [ ] T040 [US3] Implement section hierarchy preservation in `specmetrics/plugins/adapter/speckit/normalizer.py` — parse Markdown ATX headings into `DocumentSection` tree; attach non-heading content to preceding section. Covers FR-010.
- [ ] T041 [US3] Integration test: metadata preservation end-to-end in `tests/integration/adapter/speckit/test_full_scan.py`.

**Checkpoint**: US3 complete — all documents carry complete, traceable SpecKit metadata.

---

## Phase 7: Error Handling & Edge Cases

**Purpose**: Error isolation, malformed file handling, and robustness for production use.

- [ ] T042 [P] Implement per-file try/except in `scanner.py` — wrap each file read in try/except; unreadable files produce `ScanError` with `UNREADABLE` code; scan continues to next file. Covers FR-022, FR-024.
- [ ] T043 [P] Implement malformed Markdown handling in `normalizer.py` — if heading parsing fails, return document with raw content and empty sections list; do not raise. Covers FR-023.
- [ ] T044 [P] Implement corrupted UTF-8 handling in `normalizer.py` — catch `UnicodeDecodeError`, produce `ScanError` with `ENCODING_ERROR` code, continue scan. Covers Edge Cases: Corrupted UTF-8 files.
- [ ] T045 [P] Implement symbolic link resolution in `scanner.py` — follow symlinks during glob discovery; if a symlink is broken, log warning and skip. Covers Edge Cases: Symbolic links.
- [ ] T046 [P] Unit test for per-file error isolation in `tests/unit/adapter/speckit/test_scanner.py` — verify one unreadable file does not block other files. Covers SC-003.
- [ ] T047 [P] Unit test for feature-only-minimum (spec.md only) in `tests/unit/adapter/speckit/test_scanner.py` — covers Edge Cases.

---

## Phase 8: Observability & Polish

- [ ] T048 [P] Implement structured INFO/ERROR logging in `plugin.py` — log scan start, completion, per-file errors, and artifact count summary via structlog. Covers FR-025.
- [ ] T049 [P] Performance benchmark test in `tests/unit/adapter/speckit/test_scanner.py` — verify 500+ artifacts scanned in under 5 seconds. Covers SC-001.
- [ ] T050 [P] Register plugin entry point in `pyproject.toml` — add `[project.entry-points."specmetrics.plugins.adapter"] speckit = "specmetrics.plugins.adapter.speckit:SpecKitAdapter"`. Covers FR-020.
- [ ] T051 [P] Implement plugin metadata in `plugin.py` — expose `plugin_id`, `plugin_version`, `supported_framework`, `supported_artifact_types`. Covers FR-021.

---

## Dependencies

```text
Phase 1 (Setup)
  └─► Phase 2 (Foundational: adapter skeleton + data classes)
        ├─► Phase 3 (US4: Repository Detection) ◄── MVP
        │     ├─► Phase 4 (US1: Governance Discovery)
        │     │     ├─► Phase 5 (US2: Feature Workspaces)
        │     │     └─► Phase 6 (US3: Metadata)
        │     └─► Phase 7 (Error Handling)
        └─► Phase 8 (Observability & Polish)
```

## Parallel Execution Opportunities

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003 (directory creation) |
| Phase 2 | T004, T005 (skeleton + data classes) |
| Phase 3 (US4) | T006–T010 (all tests); T011 (implementation) |
| Phase 4 (US1) | T013–T016 (tests); T017 (scanner), T018 (normalizer), T019 (metadata) are independent |
| Phase 5 (US2) | T022–T027 (tests); T028 (feature scanner), T029 (metadata) |
| Phase 6 (US3) | T032–T037 (tests); T038, T039, T040 (each module) |
| Phase 7 | T042–T047 (all independent) |
| Phase 8 | T048–T051 (all independent) |

## Implementation Strategy

### MVP Scope

**Phase 1 + Phase 2 + Phase 3 (US4)** — Repository detection is the lightest MVP increment:
- Directory structure, adapter skeleton, data classes
- `supports()` implementation with path existence checks for 3 markers
- Fast repository detection without scanning

**Value at MVP**: The Plugin Registry can automatically select the SpecKit adapter when a repository follows the SpecKit convention.

### Incremental Delivery

1. **MVP** (Phase 1–3): Repository detection only
2. **US1** (Phase 4): Discover and normalize governance documents
3. **US2** (Phase 5): Add feature workspace discovery with all artifact types
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
| 3 | US4: Detect SpecKit Repositories | 7 | P1 🎯 MVP |
| 4 | US1: Discover Governance Documents | 9 | P1 |
| 5 | US2: Discover Feature Workspaces | 10 | P1 |
| 6 | US3: Preserve Feature Metadata | 10 | P1 |
| 7 | Error Handling & Edge Cases | 6 | Cross-cutting |
| 8 | Observability & Polish | 4 | Cross-cutting |
| **Total** | | **51** | |
