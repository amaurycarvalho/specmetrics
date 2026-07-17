# Feature Specification: CLI & MCP Interaction Layer

**Created**: 2026-07-15

**Status**: Draft

**Input**: User description: "F08"

## User Scenarios & Testing

### User Story 1 — Run Full Measurement Pipeline via CLI (Priority: P1)

A quality engineer runs a single command to execute the complete measurement pipeline on their project. The CLI discovers specifications, performs semantic extraction, builds the evidence graph and CFM, applies Rule Packs, runs the FPA measurement, and exports results — all from one terminal command.

**Why this priority**: The CLI is the primary interaction mechanism for human users and CI/CD pipelines. Without it, no user can execute the platform capabilities.

**Independent Test**: Can be fully tested by running `specmetrics measure` on a known test project and verifying that all pipeline stages execute in sequence and produce a measurement result.

**Acceptance Scenarios**:

1. **Given** a valid SpecKit project at the current directory, **When** the user runs `specmetrics measure`, **Then** the CLI executes the full pipeline (discovery → extraction → CFM → Rule Pack → measurement → export) and prints a summary to stdout
2. **Given** a project with no specifications, **When** the user runs `specmetrics measure`, **Then** the CLI reports an informative error indicating no specifications were found
3. **Given** the `--output json` flag, **When** the user runs the pipeline, **Then** the CLI writes the measurement result as a JSON file to the specified path
4. **Given** the `--verbose` flag, **When** the pipeline executes, **Then** the CLI prints detailed progress for each pipeline stage

---

### User Story 2 — AI Agent Invokes Measurement via MCP (Priority: P1)

An AI coding assistant invokes SpecMetrics through the Model Context Protocol to measure the functional size of a specification project. The agent receives structured measurement results without needing a terminal or manual CLI invocation.

**Why this priority**: Principle X (AI-Friendly by Design) requires machine-consumable interfaces. The MCP Server enables AI agents to incorporate functional measurement into development workflows programmatically.

**Independent Test**: Can be tested by starting the MCP Server, sending a measurement request from an MCP client, and verifying the response contains structured measurement data.

**Acceptance Scenarios**:

1. **Given** the MCP Server is running, **When** an AI agent sends a `measure` request with a project path, **Then** the server executes the measurement pipeline and returns structured results via MCP
2. **Given** the MCP Server is running without a project, **When** an AI agent sends a request, **Then** the server returns a descriptive error indicating the required parameters
3. **Given** the MCP Server is processing a measurement, **When** a second concurrent request arrives, **Then** the server queues or rejects the second request without crashing

---

### User Story 3 — Pipeline Stage Selection (Priority: P2)

An experienced user wants to run only specific pipeline stages (e.g., extraction only, or measurement only) to inspect intermediate results or debug a specific stage without re-running the entire pipeline.

**Why this priority**: Stage selection enables iterative development and debugging. However, the full pipeline execution is sufficient for the primary use case.

**Independent Test**: Can be tested by running each stage individually and verifying only that stage produces output without executing subsequent stages.

**Acceptance Scenarios**:

1. **Given** the `--stage extract` flag, **When** the pipeline runs, **Then** only the semantic extraction stage executes and produces a CFM output
2. **Given** the `--stage measure` flag and a pre-existing CFM, **When** the pipeline runs, **Then** only the measurement stage executes on the existing CFM
3. **Given** the `--from measure` flag, **When** the pipeline runs, **Then** it skips stages before measurement and starts from the measurement stage

---

### User Story 4 — Plugin Management Commands (Priority: P3)

A team lead wants to inspect which plugins are installed, verify their versions, and check compatibility with the current platform version.

**Why this priority**: Plugin management supports the plugin-oriented architecture but is not required for the core measurement workflow.

**Independent Test**: Can be tested by installing a known plugin, running `specmetrics plugins list`, and verifying the plugin appears in the output.

**Acceptance Scenarios**:

1. **Given** plugins are installed, **When** the user runs `specmetrics plugins list`, **Then** the CLI lists all discovered plugins with their names, versions, and types
2. **Given** a plugin with an incompatible version, **When** the user runs `specmetrics plugins verify`, **Then** the CLI reports the incompatibility

---

### Edge Cases

- What happens when the user runs the CLI from a directory that is not a SpecMetrics project? The CLI searches parent directories for configuration; if none found, it reports an error with initialization instructions.
- What happens when the MCP Server receives an invalid JSON-RPC request? The server responds with a standard JSON-RPC error response and continues listening for valid requests.
- What happens when the pipeline crashes mid-execution? The CLI prints the error, the partial output (if any), and exits with a non-zero exit code; no partial results are persisted as final results.
- How does the CLI handle very long output? Measurement summaries are printed by default; detailed output is written to a file when `--output` is specified.
- How does the MCP Server handle client disconnection during measurement? The server continues processing and discards the result when no client is connected to receive it.

## Constitution Check

**Engaged Principles**:

- **X (AI-Friendly by Design)** — The MCP Server exposes all platform capabilities to autonomous AI agents through a standard protocol. CLI provides the equivalent functionality for human users and automation.
- **VII (Canonical Representation)** — Both CLI and MCP consume only the Canonical Functional Model and measurement results; they never access specification documents or internal pipeline state directly.
- **VIII (Plugin-Oriented)** — CLI commands and MCP tools are implemented as discoverable commands rather than hardcoded logic. New pipeline stages and features become available as CLI commands automatically when registered.
- **XI (Observability as a Native Capability)** — The CLI supports structured output formats consumable by CI/CD pipelines; the MCP Server exposes raw structured data suitable for AI consumption.
- **XIV (Layer Independence)** — The Interaction Layer depends only on stable pipeline contracts. Changes to the CLI or MCP do not affect semantic extraction, measurement, or other internal layers.

**Compliance Notes**: Principle X is satisfied by providing both human (CLI) and machine (MCP) interfaces with equivalent capabilities. Principle VII is satisfied because neither interface accesses implementation details — they consume published outputs (CFM, measurement results). Principle VIII is satisfied by registering CLI commands and MCP tools through the platform's plugin/command registration mechanism. Principle XIV is satisfied by isolating interface logic from pipeline logic — the CLI and MCP orchestrate the pipeline through public APIs without coupling to implementation details.

## Requirements

### Functional Requirements

- **FR-001**: The CLI MUST provide a `measure` command that executes the complete measurement pipeline (discovery → extraction → evidence graph → CFM → Rule Pack → measurement → export) from a single invocation
- **FR-002**: The CLI MUST accept a project path argument, defaulting to the current working directory when not provided
- **FR-003**: The CLI MUST support the `--output <format>` flag to specify export format (json, csv, xml) and optionally a file path
- **FR-004**: The CLI MUST support `--verbose` and `--quiet` flags to control output verbosity
- **FR-005**: The CLI MUST exit with code 0 on successful execution and non-zero on errors
- **FR-006**: The CLI MUST support selecting individual pipeline stages via `--stage <stage_name>` flag
- **FR-007**: The CLI MUST support running the pipeline from a specific stage via `--from <stage_name>` flag, skipping earlier stages
- **FR-008**: The CLI MUST provide a `plugins list` command that displays all discovered plugins with their names, versions, types, and enabled status
- **FR-009**: The CLI MUST provide a `version` command that displays the platform version and installed plugin versions
- **FR-010**: The MCP Server MUST expose a `measure` tool that accepts a project path and optional parameters (output format, stages) and returns structured measurement results
- **FR-011**: The MCP Server MUST expose a `plugins/list` tool that returns the list of installed plugins
- **FR-012**: The MCP Server MUST expose a `specmetrics/version` tool that returns platform and plugin version information
- **FR-013**: The MCP Server MUST communicate via the standard Model Context Protocol (JSON-RPC 2.0 over stdio)
- **FR-014**: The MCP Server MUST handle invalid JSON-RPC requests gracefully, returning structured error responses without crashing
- **FR-015**: Both CLI and MCP Server MUST use the same underlying pipeline orchestration — equivalent operations MUST produce equivalent results regardless of interface
- **FR-016**: The CLI MUST NOT require a running MCP Server (or vice versa) — each interface must operate independently
- **FR-017**: The CLI MUST provide a `help` command (or `--help` flag) that documents available commands, flags, and usage examples
- **FR-018**: The CLI MUST support loading project configuration from the `.specmetrics/` directory, including plugin selection and pipeline options
- **FR-019**: The MCP Server MUST log its activity to stderr for debugging without interfering with the stdio JSON-RPC communication
- **FR-020**: The MCP Server MUST support the MCP `initialize` handshake, returning server capabilities including a list of available tools
- **FR-021**: The CLI MUST accept `none` as a valid LLM provider in `config llm set none`, configuring the pipeline to use the DeterministicSemanticEngine and requiring no API key or network access
- **FR-022**: The CLI MUST provide a `config llm list` command that displays all available providers with their default model and API URL

### Key Entities

- **CLI Command Registry**: The set of registered CLI commands (measure, plugins, version, help) — each command maps to a handler that invokes the appropriate pipeline or service capability
- **MCP Tool Registry**: The set of tools exposed through the Model Context Protocol — each tool maps to the same underlying capabilities as CLI commands
- **Pipeline Orchestrator**: The shared logic that translates CLI commands or MCP requests into pipeline execution, stage selection, and result collection — ensures behavioral consistency across interfaces
- **CLI Output Formatter**: Component that formats measurement results and progress information for terminal display, supporting human-readable text and machine-parseable formats (JSON)
- **MCP Server Process**: The long-running process that maintains the MCP connection, handles JSON-RPC message serialization/deserialization, and manages concurrent requests

## CLI Command Reference

The following commands are registered on the root `specmetrics` app.

### `specmetrics measure`

Execute the full measurement pipeline (discover → extract → graph → cfm → rule → measure → export).

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `project_path` | `Path` | `"."` | Path to the SpecMetrics project |
| `--output` / `-o` | `str` | — | Output format and optional path: `json`, `csv`, `xml`, `text`, or `json:./path.json` |
| `--stage` / `-s` | `str` | — | Run only this stage: `discover`, `extract`, `graph`, `cfm`, `rule`, `measure`, `export` |
| `--from` | `str` | — | Start from this stage (skip earlier stages) |
| `--verbose` / `-v` | `bool` | `False` | Show detailed per-stage progress |
| `--quiet` / `-q` | `bool` | `False` | Suppress non-error output |
| `--log-file` / `-l` | `str` | — | Persist logs to `.specmetrics/logs/<filename>` |
| `--config` / `-c` | `Path` | — | Path to configuration file (supports `$ENV_VAR` expansion) |

### `specmetrics version`

Print platform version, Python version, and list of discovered plugins.

No arguments or options.

---

### `specmetrics plugins`

Sub-commands for plugin management.

| Command | Description |
|---------|-------------|
| `plugins list` | List discovered plugins (filter with `--type adapter\|measurement\|export\|publisher`, detail with `--verbose`) |
| `plugins verify` | Verify compatibility of all discovered plugins |
| `plugins list-formats` | List discovered export formats and publishers |

### `specmetrics export`

Sub-commands for result export.

| Command | Description |
|---------|-------------|
| `export run` | Export measurement results (`--format json,csv,xml`, `--output-dir`, `--publish`, `--otel-endpoint`) |
| `export list-formats` | List discovered exporter plugins |
| `export publisher-status` | Show status of configured telemetry publishers |

### `specmetrics config`

Sub-commands for configuration management.

| Command | Description |
|---------|-------------|
| `config dump` | Dump all resolved configuration entries (`--format text\|json`) |

#### `specmetrics config llm`

Nested sub-commands for LLM provider configuration. Config is stored outside the project in `~/.config/specmetrics/config.yml`.

| Command | Description |
|---------|-------------|
| `config llm list` | List all available LLM providers with their default model and API URL |
| `config llm set <provider>` | Set LLM provider. Valid providers: `none` (deterministic engine, offline), `chatgpt`, `gemini`, `copilot`, `claude`, `deepseek`, `ollama`, `custom`. Options: `--model`, `--api-key`, `--api-url` (overrides preset defaults) |
| `config llm show` | Display current LLM configuration, or indicate that `none` (deterministic engine) is the active/default provider |
| `config llm set-model <model>` | Change the model identifier only |
| `config llm set-api-key <key>` | Change the API key only |

### `specmetrics explain`

Sub-commands for measurement explanation.

| Command | Description |
|---------|-------------|
| `explain <run_id>` | Explain a measurement run (`--metric`, `--format text\|json`, `--compare <run_id>`, `--run-dir`) |

### `specmetrics mcp`

Sub-commands for the MCP server (Model Context Protocol).

| Command | Description |
|---------|-------------|
| `mcp start` | Start the MCP server (`--host`, `--port`, `--transport stdio\|sse`, `--max-connections`, `--log-level`, `--config`) |
| `mcp stop` | Stop the MCP server (`--timeout <seconds>`) |
| `mcp status` | Show whether the MCP server is running |

### `specmetrics validate`

Sub-commands for specification validation.

| Command | Description |
|---------|-------------|
| `validate <spec_paths...>` | Validate specification files (`--rules`, `--format text\|json\|quiet`, `--batch`, `--constitution-only`, `--structural-only`) |

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: The complete pipeline executes via CLI with a single `specmetrics measure` command on a standard project, producing output within 30 seconds
- **SC-002**: An AI agent can invoke measurement and receive structured results through the MCP Server without requiring terminal access or CLI knowledge
- **SC-003**: Running the same operation through CLI and MCP produces identical measurement results for the same project and parameters
- **SC-004**: CLI error messages clearly identify the root cause (missing project, plugin failure, configuration error) without requiring internal platform knowledge
- **SC-005**: The MCP Server starts and accepts connections within 5 seconds, and responds to measurement requests within the same timeframe as CLI execution
- **SC-006**: Invalid MCP requests receive structured JSON-RPC error responses — the server never crashes or enters an unrecoverable state from malformed input
- **SC-007**: All CLI commands and MCP tools remain functional when individual plugins are missing or fail, reporting clear plugin-specific errors rather than crashing the interface

## Assumptions

- The Kernel Pipeline Engine (002) and Plugin Discovery Registry (003) are fully implemented and provide the orchestration and discovery mechanisms that the CLI and MCP Server consume
- The Canonical Functional Model (007), Measurement Engine (008), Rule Pack Engine (F09), and Export Layer (F10) are available as pipeline stages, but the CLI and MCP can be developed and tested with mock/simulated stages before those features are complete
- The CLI uses standard argument parsing libraries for command definition, flag handling, and help text generation
- The MCP Server uses stdio transport for the MVP; future versions may support SSE or WebSocket transports
- The CLI targets Unix-like environments (Linux, macOS) for the MVP; Windows support is deferred
- Authentication and authorization are out of scope for the MVP — both CLI and MCP operate with the permissions of the invoking user/process
- The MCP Server runs as a single process serving one client at a time for the MVP; concurrent client support is deferred
- Log files are persisted to `.specmetrics/logs/<filename>` when `--log-file` is specified
