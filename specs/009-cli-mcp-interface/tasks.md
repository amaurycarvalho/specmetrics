# Tasks: CLI & MCP Interaction Layer

**Input**: Design documents from `/specs/009-cli-mcp-interface/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Optional — not explicitly requested in spec; quickstart.md provides manual validation scenarios.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

All source files under `specmetrics/` at repository root. Tests mirror source layout under `specmetrics/tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and directory structure

- [ ] T001 Create CLI package structure at `specmetrics/cli/__init__.py`
- [ ] T002 [P] Create MCP package structure at `specmetrics/mcp/__init__.py`
- [ ] T003 [P] Create application package at `specmetrics/application/__init__.py`
- [ ] T004 Add `typer`, `mcp`, and `structlog` dependencies to `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `PipelineRequest`, `PipelineResult`, `StageResult`, `MeasurementResult` Pydantic models in `specmetrics/application/models.py`
- [ ] T006 [P] Implement `StageName` and `OutputFormat` enums in `specmetrics/application/enums.py`
- [ ] T007 [P] Implement `PluginInfo` and `VersionInfo` Pydantic models in `specmetrics/application/models.py`
- [ ] T008 Create `PipelineOrchestrator` class skeleton in `specmetrics/application/orchestrator.py` with `execute(request: PipelineRequest) -> PipelineResult` method signature and docstring
- [ ] T009 Implement project configuration loader from `.specify/config.yml` in `specmetrics/application/config.py`

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 — Run Full Measurement Pipeline via CLI (Priority: P1) 🎯 MVP

**Goal**: Single `specmetrics measure` command executes the complete measurement pipeline and prints results

**Independent Test**: Run `specmetrics measure` on a test project — verify all pipeline stages execute and a summary is printed to stdout with exit code 0

- [ ] T010 [P] [US1] Create Typer application entry point with `measure`, `plugins`, `version`, and `help` commands in `specmetrics/cli/app.py`
- [ ] T011 [P] [US1] Implement CLI output formatter for text summary in `specmetrics/cli/formatters.py` — includes progress display and the structured table format defined in research.md
- [ ] T012 [US1] Implement `measure` command handler in `specmetrics/cli/measure.py` — accepts `PROJECT_PATH` argument, parses `--output`, `--verbose`, `--quiet` flags, calls orchestrator, and prints result
- [ ] T013 [US1] Implement `--output <format>` flag handling in `specmetrics/cli/measure.py` — supports `json`, `csv`, `xml`, `text` formats with optional path (`json:./path.json`)
- [ ] T014 [US1] Implement `--verbose` and `--quiet` flag handling in `specmetrics/cli/measure.py` — verbose shows per-stage detail, quiet suppresses all non-error output
- [ ] T015 [US1] Implement exit code handling in `specmetrics/cli/app.py` — exit 0 on success, 1 on error, 2 on plugin error
- [ ] T016 [US1] Implement `--help` and default help text for all commands in `specmetrics/cli/app.py`
- [ ] T017 [US1] Implement `version` command in `specmetrics/cli/app.py` — displays platform version and plugin versions
- [ ] T018 [US1] Wire `PipelineOrchestrator` into CLI `measure` command in `specmetrics/cli/measure.py` — calls `orchestrator.execute()` with the parsed `PipelineRequest`
- [ ] T019 [US1] Wire project config loading into CLI startup in `specmetrics/cli/app.py` — loads `.specify/config.yml` and applies defaults (output format, verbosity)

**Checkpoint**: `specmetrics measure` runs the full pipeline with output and exit codes — validates quickstart Scenarios 1, 2, 4, 6, 10

---

## Phase 4: User Story 2 — AI Agent Invokes Measurement via MCP (Priority: P1)

**Goal**: MCP Server starts on stdio, accepts initialize handshake, and exposes `measure` tool that runs the pipeline

**Independent Test**: Start `specmetrics-mcp`, send an MCP `initialize` request, then send a `tools/call` for `measure` — verify structured response

- [ ] T020 [P] [US2] Implement MCP server entry point with stdio transport and `initialize` handshake in `specmetrics/mcp/server.py`
- [ ] T021 [P] [US2] Implement `measure` MCP tool handler in `specmetrics/mcp/tools.py` — accepts `project_path`, `output_format`, `from_stage` params, calls orchestrator, returns serialized `PipelineResult`
- [ ] T022 [P] [US2] Implement `plugins_list` MCP tool handler in `specmetrics/mcp/tools.py` — returns list of installed plugins as serialized `PluginInfo`
- [ ] T023 [P] [US2] Implement `specmetrics_version` MCP tool handler in `specmetrics/mcp/tools.py` — returns platform version and plugin versions as serialized `VersionInfo`
- [ ] T024 [US2] Implement JSON-RPC error handling in `specmetrics/mcp/server.py` — returns structured error responses for parse errors, invalid requests, unknown methods, invalid params, and internal errors
- [ ] T025 [US2] Implement concurrent request handling in `specmetrics/mcp/server.py` — queues or rejects second request while measurement is in progress, never crashes
- [ ] T026 [US2] Implement stderr logging in `specmetrics/mcp/server.py` — logs requests, responses, and errors to stderr without interfering with stdio JSON-RPC
- [ ] T027 [US2] Wire MCP tools to `PipelineOrchestrator` in `specmetrics/mcp/server.py` — all tool handlers call `orchestrator.execute()` through the shared `orchestrator` instance

**Checkpoint**: MCP Server starts, handshakes, and handles `measure` requests — validates quickstart Scenarios 7, 8

---

## Phase 5: User Story 3 — Pipeline Stage Selection (Priority: P2)

**Goal**: Users can run specific stages or start from a given stage via `--stage` and `--from` flags on CLI and equivalent params on MCP

**Independent Test**: Run `specmetrics measure --stage extract` — verify only extraction stage executes. Run `specmetrics measure --from measure` — verify stages before `measure` are skipped.

- [ ] T028 [US3] Add `--stage <name>` flag parsing to `specmetrics/cli/measure.py` — accepts one of the `StageName` values, populates `PipelineRequest.stages`
- [ ] T029 [US3] Add `--from <name>` flag parsing to `specmetrics/cli/measure.py` — accepts one of the `StageName` values, populates `PipelineRequest.from_stage`
- [ ] T030 [US3] Add stage name validation in `specmetrics/cli/measure.py` — unknown stage names produce descriptive error listing valid options
- [ ] T031 [US3] Add `from_stage` parameter to MCP `measure` tool schema in `specmetrics/mcp/tools.py`
- [ ] T032 [US3] Implement stage filtering logic in `specmetrics/application/orchestrator.py` — `execute()` resolves stage names to pipeline events, applies `stages` or `from_stage` filtering, invokes only selected stages

**Checkpoint**: Stage selection works on both CLI and MCP — validates quickstart Scenario 3

---

## Phase 6: User Story 4 — Plugin Management Commands (Priority: P3)

**Goal**: Users can list installed plugins, verify compatibility, and view version information via CLI and MCP

**Independent Test**: Run `specmetrics plugins list` with a known plugin installed — verify it appears in output with correct name, version, and type

- [ ] T033 [P] [US4] Implement `plugins list` command in `specmetrics/cli/plugins.py` — lists all discovered plugins with name, version, type, and enabled status
- [ ] T034 [P] [US4] Implement `plugins verify` command in `specmetrics/cli/plugins.py` — checks all installed plugins for version compatibility with current platform
- [ ] T035 [US4] Add `--type` filter flag to `plugins list` in `specmetrics/cli/plugins.py` — filtered output for specific plugin families
- [ ] T036 [US4] Wire `plugins list` and `plugins verify` to Plugin Discovery Registry (003) in `specmetrics/cli/plugins.py`
- [ ] T037 [US4] Verify `plugins_list` and `specmetrics_version` MCP tools correctly expose the same data as their CLI counterparts in `specmetrics/mcp/tools.py`

**Checkpoint**: `specmetrics plugins list` and `specmetrics plugins verify` work — validates quickstart Scenario 5

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories or the overall quality of the interaction layer

- [ ] T038 [P] Add type hints and run `mypy` on all files under `specmetrics/cli/`, `specmetrics/mcp/`, and `specmetrics/application/`
- [ ] T039 Add `structlog` logging across CLI app and MCP server with appropriate log levels in `specmetrics/cli/app.py` and `specmetrics/mcp/server.py`
- [ ] T040 Run all quickstart.md validation scenarios end-to-end and fix any issues
- [ ] T041 Add module-level and function-level docstrings to all public interfaces in `specmetrics/cli/`, `specmetrics/mcp/`, and `specmetrics/application/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **US1 — CLI (Phase 3)**: Depends on Foundational completion — can proceed independently of other stories
- **US2 — MCP (Phase 4)**: Depends on Foundational completion — can proceed in parallel with US1
- **US3 — Stage Selection (Phase 5)**: Depends on US1 and US2 completion — extends both CLI and MCP
- **US4 — Plugin Management (Phase 6)**: Depends on Foundational completion — independent of US1, US2, US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependencies on other stories
- **US2 (P1)**: Can start after Foundational — no dependencies on other stories; can run in parallel with US1
- **US3 (P2)**: Depends on US1 and US2 — extends both interfaces with stage selection
- **US4 (P3)**: Can start after Foundational — independent of US1, US2, US3; can run in parallel with any story

### Within Each User Story

- Models before services
- Core implementation before wiring/integration
- CLI and MCP tool implementations are independent within each story
- Each story must be independently testable before moving to next priority

### Parallel Opportunities

| Tasks | Can Run In Parallel |
|-------|-------------------|
| T001, T002, T003 | All Setup package creation |
| T005, T006, T007 | Models and enums (different files) |
| T010, T011 | App entry point and output formatter |
| T020, T021, T022, T023 | MCP server init and all tool handlers |
| T033, T034 | Plugin list and verify commands |
| US1 and US2 | Entire stories can be implemented in parallel |
| US4 | Can run in parallel with US1, US2, or US3 |

---

## Parallel Example: User Story 1

```bash
# Launch app entry point and formatter together:
Task: T010 - Create Typer app in specmetrics/cli/app.py
Task: T011 - Implement output formatter in specmetrics/cli/formatters.py
```

## Parallel Example: User Story 2

```bash
# Launch server init and all tool handlers together:
Task: T020 - Implement MCP server in specmetrics/mcp/server.py
Task: T021 - Implement measure tool in specmetrics/mcp/tools.py
Task: T022 - Implement plugins_list tool in specmetrics/mcp/tools.py
Task: T023 - Implement specmetrics_version tool in specmetrics/mcp/tools.py
```

## Parallel Example: US1 + US2 (full parallel)

```bash
# Two developers can implement US1 and US2 simultaneously:
Developer A: T010-T019 (US1 - CLI)
Developer B: T020-T027 (US2 - MCP)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (CLI full pipeline)
4. **STOP and VALIDATE**: Run `specmetrics measure` on a test project
5. Deploy/demo if ready — CLI provides core interaction mechanism

### Incremental Delivery

1. **Setup + Foundational** → Foundation ready
2. **US1 (CLI Full Pipeline)** → Test via `specmetrics measure` → **MVP!**
3. **US2 (MCP Server)** → Test via MCP client → AI agents can now access the platform
4. **US3 (Stage Selection)** → Debug and iterate specific pipeline stages
5. **US4 (Plugin Management)** → Visibility into installed plugins
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With two developers:

1. **Both**: Complete Phase 1 + Phase 2 together
2. **Developer A**: User Story 1 (CLI) + User Story 3 (Stage Selection — extends CLI)
3. **Developer B**: User Story 2 (MCP) + User Story 4 (Plugin Management — independent)
4. At end: Integrate and validate all stories together

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently completable and testable
- Quickstart.md provides manual validation scenarios for each story
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
