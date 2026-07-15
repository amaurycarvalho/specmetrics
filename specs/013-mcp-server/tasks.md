# Tasks: MCP Server

**Input**: Design documents from `/specs/013-mcp-server/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not requested in feature specification — test tasks are omitted. Testing strategy is defined in quickstart.md validation scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **SpecMetrics project**: `specmetrics/mcp/`, `specmetrics/cli/commands/`, `specmetrics/kernel/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create `specmetrics/mcp/__init__.py` package init with version and public API exports
- [x] T002 [P] Create `specmetrics/mcp/server.py` with `MCPServer` class skeleton (host, port, transport type, start/stop methods)
- [x] T003 [P] Create `specmetrics/mcp/transport.py` with `StdioTransport` and `SSETransport` base classes using MCP SDK
- [x] T004 [P] Create `specmetrics/mcp/registry.py` with `ToolRegistry`, `ResourceRegistry`, and `PromptRegistry` base classes
- [x] T005 [P] Create `specmetrics/mcp/tools/__init__.py` for tools subpackage
- [x] T006 [P] Create `specmetrics/mcp/resources/__init__.py` for resources subpackage
- [x] T007 [P] Create `specmetrics/mcp/prompts/__init__.py` for prompts subpackage
- [x] T008 Create `specmetrics/mcp/__init__.py` to expose `MCPServer`, `Registry`, and transport classes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 [P] Implement `ToolRegistry` in `specmetrics/mcp/registry.py` with `register()`, `get_tool()`, `list_tools()` methods returning name, description, and input_schema per MCP protocol
- [x] T010 [P] Implement `ResourceRegistry` in `specmetrics/mcp/registry.py` with `register()`, `match_uri()`, `list_templates()` methods for URI pattern matching
- [x] T011 [P] Implement `PromptRegistry` in `specmetrics/mcp/registry.py` with `register()`, `get_prompt()`, `list_prompts()` methods
- [x] T012 [P] Implement `StdioTransport` in `specmetrics/mcp/transport.py` using MCP SDK's `stdio_server` — reads from stdin, writes to stdout, handles JSON-RPC framing
- [x] T013 [P] Implement `SSETransport` in `specmetrics/mcp/transport.py` using MCP SDK's `sse_server` — accepts connections on configured host:port, handles HTTP upgrade
- [x] T014 [P] Implement `MCPConnection` data class in `specmetrics/mcp/server.py` with connection_id, transport_type, protocol_version, connected_at, last_activity_at, active_request_id fields
- [x] T015 [P] Implement `ServerConfiguration` Pydantic model in `specmetrics/mcp/server.py` with host, port, transport, max_connections, log_level, pipeline_timeout_seconds, shutdown_timeout_seconds fields and validation
- [x] T016 Implement `MCPServer` core request routing in `specmetrics/mcp/server.py` — dispatches `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get` to appropriate registry
- [x] T017 Implement protocol version negotiation in `specmetrics/mcp/server.py` — advertise supported version, reject unsupported versions with descriptive error (FR-009)
- [x] T018 Implement concurrent connection management in `specmetrics/mcp/server.py` — connection tracking, max_connections enforcement (FR-006)
- [x] T019 Implement structured logging in `specmetrics/mcp/server.py` using structlog — log all requests, responses, and errors without exposing configuration values (FR-007)
- [x] T020 Implement error handling middleware in `specmetrics/mcp/server.py` — catch all tool/resource handler exceptions, log with context, return structured error response (FR-008)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Expose measurement pipeline as MCP tools (Priority: P1) 🎯 MVP

**Goal**: AI agents can discover and invoke SpecMetrics pipeline operations via MCP tools

**Independent Test**: Connect an MCP client to the server, list available tools, invoke a measurement command, and verify structured response

### Implementation for User Story 1

- [x] T021 [P] [US1] Implement `run_pipeline` tool in `specmetrics/mcp/tools/measure.py` — accepts project_path, stage, export_format parameters; invokes pipeline orchestrator; returns run_id, metrics, timestamps
- [x] T022 [P] [US1] Implement `list_specs` tool in `specmetrics/mcp/tools/specs.py` — accepts project_path; returns array of spec document summaries (name, path, type, last_modified)
- [x] T023 [P] [US1] Implement `read_spec` tool in `specmetrics/mcp/tools/specs.py` — accepts spec_path; returns spec content with mime_type
- [x] T024 [P] [US1] Implement `export_results` tool in `specmetrics/mcp/tools/export.py` — accepts run_id, format, optional output_path; triggers export and returns export_path
- [x] T025 [P] [US1] Implement `get_status` tool in `specmetrics/mcp/tools/status.py` — returns ServerStatus (state, uptime, active_connections, total_requests, total_errors)
- [x] T026 [US1] Register all US1 tools with `ToolRegistry` in `specmetrics/mcp/server.py` — call `registry.register()` for each tool at startup
- [x] T027 [US1] Implement JSON Schema validation for all tool inputs in `specmetrics/mcp/server.py` before dispatching to handler — return invalid params error with field name and expected format (FR-005)

**Checkpoint**: At this point, User Story 1 should be fully functional — an MCP client can discover and invoke all pipeline tools

---

## Phase 4: User Story 2 — Expose SpecMetrics resources through MCP (Priority: P1)

**Goal**: AI agents can access specification documents, measurement results, and evidence graph data via standard MCP resource URIs

**Independent Test**: Connect an MCP client, fetch a resource URI for a known spec document, and verify content matches the on-disk file

### Implementation for User Story 2

- [x] T028 [P] [US2] Implement `spec` resource handler in `specmetrics/mcp/resources/specs.py` — resolves `specmetrics://spec/{path}` URIs, reads file content, returns with `text/markdown` MIME type
- [x] T029 [P] [US2] Implement `measurement` resource handler in `specmetrics/mcp/resources/measurements.py` — resolves `specmetrics://measurement/{run_id}` URIs, looks up run data, returns JSON
- [x] T030 [P] [US2] Implement `evidence` resource handler in `specmetrics/mcp/resources/measurements.py` — resolves `specmetrics://evidence/{run_id}` URIs, returns evidence graph data as JSON
- [x] T031 [P] [US2] Implement `export` resource handler in `specmetrics/mcp/resources/measurements.py` — resolves `specmetrics://export/{run_id}/{format}` URIs, returns exported content with appropriate MIME type
- [x] T032 [US2] Implement URI pattern matching in `specmetrics/mcp/registry.py` — match incoming URIs against registered templates using path parameter extraction
- [x] T033 [US2] Register all US2 resource handlers with `ResourceRegistry` in `specmetrics/mcp/server.py` — call `registry.register()` for each URI pattern at startup
- [x] T034 [US2] Implement path traversal protection in `specmetrics/mcp/resources/specs.py` — validate resolved path is within project directory; reject `..` traversal attempts with error code -32002

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — Server lifecycle management (Priority: P2)

**Goal**: Operators can start, stop, and monitor the MCP server via CLI commands

**Independent Test**: Start the server, verify it accepts connections, stop it, and confirm connections are refused

### Implementation for User Story 3

- [x] T035 [P] [US3] Implement `specmetrics mcp start` command in `specmetrics/cli/commands/mcp.py` — loads configuration, instantiates MCPServer, starts transport, writes PID to file
- [x] T036 [P] [US3] Implement `specmetrics mcp stop` command in `specmetrics/cli/commands/mcp.py` — reads PID file, sends graceful shutdown signal, waits for shutdown_timeout
- [x] T037 [P] [US3] Implement `specmetrics mcp status` command in `specmetrics/cli/commands/mcp.py` — checks PID file, probes server health, prints ServerStatus
- [x] T038 [US3] Implement graceful shutdown in `specmetrics/mcp/server.py` — on shutdown signal, stop accepting new connections, complete in-flight requests within shutdown_timeout_seconds, then terminate remaining (FR-010)
- [x] T039 [US3] Implement configuration loading in `specmetrics/mcp/server.py` — load `ServerConfiguration` from YAML, allow CLI flag overrides for host, port, transport (FR-004)
- [x] T040 [US3] Implement `ServerStatus` tracking in `specmetrics/mcp/server.py` — accumulate state, uptime, active_connections, total_requests_handled, total_errors, last_error_timestamp

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 — Prompt templates for common workflows (Priority: P3)

**Goal**: AI agents can discover and use pre-defined prompt templates for common SpecMetrics workflows

**Independent Test**: List available prompts, retrieve a prompt template, and verify it contains expected parameter placeholders

### Implementation for User Story 4

- [x] T041 [P] [US4] Define `measure_project` prompt template in `specmetrics/mcp/prompts/templates.py` — guides agent through measuring a project with project_path and export_format arguments
- [x] T042 [P] [US4] Define `analyze_spec` prompt template in `specmetrics/mcp/prompts/templates.py` — guides agent through reading and analyzing a specification document with spec_path argument
- [x] T043 [P] [US4] Define `export_results` prompt template in `specmetrics/mcp/prompts/templates.py` — guides agent through exporting measurement results with run_id and format arguments
- [x] T044 [US4] Register all prompt templates with `PromptRegistry` in `specmetrics/mcp/server.py` — call `registry.register()` for each prompt at startup

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T045 [P] Configure `specmetrics mcp` CLI commands as a Typer subcommand group in `specmetrics/cli/commands/mcp.py` — register under the main specmetrics CLI app
- [ ] T046 [P] Run quickstart.md validation — execute all 7 validation scenarios and verify expected outcomes
- [x] T047 Code cleanup and refactoring across `specmetrics/mcp/` — ensure consistent error handling, logging, and docstrings
- [x] T048 Verify SC-006 — compare CLI command list against MCP `tools/list` response to confirm all pipeline capabilities are exposed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3) and US2 (Phase 4) share P1 priority — can proceed in parallel
  - US3 (Phase 5) can run in parallel with US1/US2
  - US4 (Phase 6) can run in parallel with US1/US2/US3
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational — no dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational — no dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational — depends on ServerConfiguration (T015) being complete
- **User Story 4 (P3)**: Can start after Foundational — no dependencies on other stories

### Within Each User Story

- Registry implementations before tool/resource/prompt handlers
- Core server request routing before tool-specific logic
- Schema validation infrastructure before tool implementations
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (T009-T015)
- Once Foundational phase completes, US1, US2, US3, and US4 can all start in parallel
- All tasks within a user story marked [P] can run in parallel
- US1 has 4 parallel tool implementations (T021-T025)

---

## Parallel Example: User Story 1

```bash
# Launch all tool implementations for User Story 1 together:
Task: "Implement run_pipeline tool in specmetrics/mcp/tools/measure.py"
Task: "Implement list_specs tool in specmetrics/mcp/tools/specs.py"
Task: "Implement read_spec tool in specmetrics/mcp/tools/specs.py"
Task: "Implement export_results tool in specmetrics/mcp/tools/export.py"
Task: "Implement get_status tool in specmetrics/mcp/tools/status.py"

# After tools complete, register them with the registry:
Task: "Register tools with ToolRegistry in specmetrics/mcp/server.py"
Task: "Implement JSON Schema validation in specmetrics/mcp/server.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (tools)
4. **STOP and VALIDATE**: Run quickstart Scenario 2 (tool discovery and invocation via stdio)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → MCP server skeleton with transport and registries
2. Add User Story 1 (tools) → MVP: AI agents can invoke pipeline operations → Deploy/Demo
3. Add User Story 2 (resources) → Agents can read specs and results via URIs → Deploy/Demo
4. Add User Story 3 (lifecycle) → Operators can start/stop/status via CLI → Deploy/Demo
5. Add User Story 4 (prompts) → Agents get guided workflow templates → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (tools)
   - Developer B: User Story 2 (resources)
   - Developer C: User Story 3 (lifecycle)
3. After US1 is stable, Developer A picks up User Story 4 (prompts)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
