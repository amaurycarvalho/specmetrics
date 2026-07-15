# Tasks: Export Layer

**Input**: Design documents from `specs/011-export-layer/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in spec — task phases below do not include test-specific tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/kernel/`, `specmetrics/plugins/`, `specmetrics/cli/`, `specmetrics/mcp/`, `specmetrics/tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and register plugin entry points

- [x] T001 Create `specmetrics/plugins/exporter/` and `specmetrics/plugins/publisher/` directory structures with `__init__.py` files
- [x] T002 Register `specmetrics.exporters` and `specmetrics.publishers` entry point groups in `pyproject.toml`
- [x] T003 Add `opentelemetry-api` and `opentelemetry-sdk` runtime dependencies to `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Plugin interfaces, data models, and orchestration service — MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 [P] Create `ExporterPlugin` abstract base class in `specmetrics/plugins/exporter/base.py` with `export()` method signature matching [exporter-plugin contract](contracts/exporter-plugin.md)
- [x] T005 [P] Create `PublisherPlugin` abstract base class in `specmetrics/plugins/publisher/base.py` with `publish()` method signature matching [publisher-plugin contract](contracts/publisher-plugin.md)
- [x] T006 [P] Create `ExportFormat` Pydantic model in `specmetrics/plugins/exporter/models.py` with fields: `id`, `name`, `description`, `file_extension`, `content_type`, `serializer`
- [x] T007 Create `ExportMetadata` Pydantic model in `specmetrics/plugins/exporter/models.py` with fields: `specmetrics_version`, `run_id`, `export_timestamp`, `function_count`, `pipeline_duration_ms`
- [x] T008 Create `ExportOrchestrator` service in `specmetrics/plugins/exporter/orchestrator.py` that iterates formats sequentially, isolates per-format errors, handles empty results (produces valid empty files), and manages file overwrite-with-warning behavior

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Export to Standard Formats (Priority: P1) 🎯 MVP

**Goal**: Users can export measurement results in JSON, CSV, and XML formats via CLI and MCP, with evidence traceability and metadata

**Independent Test**: Run a measurement pipeline and verify exported output files in JSON, CSV, and XML formats contain the same measurement data with evidence references and metadata

### Implementation for User Story 1

- [x] T009 [P] [US1] Implement JSON exporter plugin in `specmetrics/plugins/exporter/json_exporter.py` using stdlib `json` module; produce valid empty `[]` for zero results
- [x] T010 [P] [US1] Implement CSV exporter plugin in `specmetrics/plugins/exporter/csv_exporter.py` using stdlib `csv` module; produce header-only file for zero results
- [x] T011 [P] [US1] Implement XML exporter plugin in `specmetrics/plugins/exporter/xml_exporter.py` using stdlib `xml.etree.ElementTree`; produce empty root element for zero results
- [x] T012 [US1] Register JSON, CSV, XML exporter entry points in `pyproject.toml` under `specmetrics.exporters`
- [x] T013 [US1] Implement CLI export commands in `specmetrics/cli/export_commands.py` using Typer with `--format`, `--output-dir` flags; integrate with `ExportOrchestrator`
- [x] T014 [US1] Register export CLI commands with the main Typer app in `specmetrics/cli/app.py`
- [x] T015 [US1] Implement MCP export tools in `specmetrics/mcp/tools.py` with callable tool definitions for each format
- [x] T016 [US1] Add evidence reference inclusion to all three exporters — each measurement output must include document, section, and text fragment references (FR-002)
- [x] T017 [US1] Add metadata injection to all three exporters — include `ExportMetadata` fields in each output (FR-010)
- [x] T018 [US1] Add structured logging for export operations (format selected, file path, duration, result count) in `specmetrics/plugins/exporter/orchestrator.py`

**Checkpoint**: At this point, User Story 1 should be fully functional — users can export measurements to JSON/CSV/XML via CLI

---

## Phase 4: User Story 2 - Publish to OpenTelemetry (Priority: P2)

**Goal**: Team leads can automatically publish measurement results to OpenTelemetry-compatible observability backends

**Independent Test**: Configure a mock OTLP receiver, run measurement pipeline with publisher enabled, verify metrics arrive with correct names and values

### Implementation for User Story 2

- [x] T019 [P] [US2] Implement OpenTelemetry publisher plugin in `specmetrics/plugins/publisher/otel_publisher.py` publishing function count (counter) and complexity distribution (histogram) metrics
- [x] T020 [P] [US2] Create `PublisherTarget` Pydantic model in `specmetrics/plugins/publisher/models.py` with fields: `id`, `endpoint_url`, `enabled`, `publishing_interval`
- [x] T021 [US2] Implement publisher orchestration in `specmetrics/plugins/publisher/orchestrator.py` that loads enabled publishers, calls `publish()` per target, isolates failures per FR-006
- [x] T022 [US2] Register `otel` publisher entry point in `pyproject.toml` under `specmetrics.publishers`
- [x] T023 [US2] Add publisher CLI flags (`--publish`, `--otel-endpoint`) to export command in `specmetrics/cli/export_commands.py`
- [x] T024 [US2] Add MCP publisher tools via `export` tool in `specmetrics/mcp/tools.py`
- [x] T025 [US2] Integrate publisher with measurement pipeline — `export run --publish` invokes publishers after export
- [x] T026 [US2] Handle unreachable endpoints gracefully — log warning, return `PublishResult(success=False)`, do not block pipeline (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Plugin Custom Export Formats (Priority: P3)

**Goal**: Platform integrators can register custom export format plugins without modifying core platform code

**Independent Test**: Register a third-party export plugin via entry point, select it as an export format, verify it receives measurement data and produces custom output

### Implementation for User Story 3

- [x] T027 [P] [US3] Implement plugin discovery for `specmetrics.exporters` entry point group in `specmetrics/plugins/exporter/discovery.py` — scan, validate, and load exporter plugins
- [x] T028 [P] [US3] Implement plugin discovery for `specmetrics.publishers` entry point group in `specmetrics/plugins/publisher/discovery.py`
- [x] T029 [US3] Create plugin registry integration that exposes discovered exporters/publishers via `ExportOrchestrator` and publisher orchestration
- [x] T030 [US3] Add `plugins list-formats` CLI command showing discovered exporters and publishers in `specmetrics/cli/plugins.py`
- [x] T031 [US3] Add plugin validation — verify each discovered plugin implements the correct abstract base class before registration; report clear errors for invalid plugins

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Performance, hardening, and validation

- [x] T032 [P] Add size-based batching for large datasets (>5,000 functions) to prevent memory issues during serialization
- [x] T033 [P] Add configurable output path option (`--output-dir`) with directory creation fallback
- [x] T034 Run through [quickstart.md](quickstart.md) validation scenarios to verify end-to-end correctness
- [x] T035 Review all error messages for clarity (FR-009) — unsupported formats, invalid config, filesystem errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–5)**: All depend on Foundational phase completion
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational — May read from `ExportOrchestrator` but should be independently testable with mock data
- **User Story 3 (P3)**: Can start after Foundational — Depends on plugin discovery infrastructure but not on specific exporter implementations

### Parallel Opportunities

- All Phase 1 tasks can run in parallel
- All Phase 2 `[P]` tasks can run in parallel
- T009, T010, T011 (US1 exporters) can run in parallel
- T019, T020 (US2 models and publisher) can run in parallel
- T027, T028 (US3 plugin discovery) can run in parallel
- Once Foundational completes, US1, US2, and US3 can be worked on in parallel by different developers

---

## Parallel Example: User Story 1

```bash
# Launch all three exporter implementations in parallel:
Task: "Implement JSON exporter in specmetrics/plugins/exporter/json_exporter.py"
Task: "Implement CSV exporter in specmetrics/plugins/exporter/csv_exporter.py"
Task: "Implement XML exporter in specmetrics/plugins/exporter/xml_exporter.py"

# After exporters complete, CLI and MCP integration can run in parallel:
Task: "Implement CLI export commands in specmetrics/cli/export_commands.py"
Task: "Implement MCP export tools in specmetrics/mcp/tools/export_tools.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (export to JSON/CSV/XML)
4. **STOP and VALIDATE**: Test User Story 1 independently — `python -m specmetrics measure --export json,csv,xml`
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Export to files (MVP!)
3. Add User Story 2 → Publish to telemetry
4. Add User Story 3 → Custom plugin formats
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (exporters + CLI/MCP)
   - Developer B: User Story 2 (OpenTelemetry publisher)
   - Developer C: User Story 3 (plugin discovery)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
