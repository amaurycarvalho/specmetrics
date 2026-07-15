# Implementation Plan: MCP Server

**Branch**: `013-mcp-server` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-mcp-server/spec.md`

## Summary

Implement a standalone MCP (Model Context Protocol) server that exposes SpecMetrics pipeline capabilities as MCP tools, resources, and prompts. Building on the basic MCP interface from feature 009 (CLI & MCP Interaction Layer), this feature delivers a production-grade MCP server with SSE/stdio transport, concurrent client support, dynamic capability discovery, resource-based access to specs and measurement results, and full lifecycle management.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: `mcp` (MCP protocol Python SDK), structlog (logging), Pydantic v2 (schemas), Typer (CLI integration for server start/stop commands)

**Storage**: N/A — no persistent storage; reads/writes project filesystem paths provided by client

**Testing**: pytest with MCP test client (`mcp` SDK testing utilities); integration tests against a running server instance

**Target Platform**: Linux (primary), macOS (secondary)

**Project Type**: CLI tool + MCP server (standalone process; can be started via CLI command)

**Performance Goals**: Server starts and accepts connections in <3s (SC-004); tool invocation returns results within 2s of underlying pipeline stage (SC-002); resource fetch within 1s (SC-003); supports 5+ concurrent clients without degradation (SC-002)

**Constraints**: No authentication for v1 (trusted network environments per Assumptions); stdio transport for embedded use, SSE for network mode; no server→client notifications in v1

**Scale/Scope**: Single-user/single-project context per server instance; up to 5 concurrent client connections; server runs as long-lived process

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: X (AI-Friendly by Design), VIII (Plugin-Oriented), XIV (Layer Independence), I (Specification First)

**Compliance Verifications**:
- [x] Specification First: MCP server consumes spec-driven outputs (CFM, measurement results) — it does not bypass specifications. Resources expose specification documents as-is.
- [x] Evidence First: Tool responses and resource representations pass through measurement results with provenance intact — evidence references are preserved.
- [x] Canonical Representation: All pipeline operations invoked through MCP tools consume the Canonical Functional Model — no framework-specific artifacts.
- [x] Plugin-Oriented: MCP tools and resources are registered via a provider registry; new pipeline capabilities become automatically available as MCP tools when they register.
- [x] Rule Externalization: N/A — the MCP server is an interaction layer; it does not define or apply measurement policies.
- [x] Layer Independence: MCP server depends only on the pipeline orchestration contract (orchestrator) and the Kernel's capability registry — no coupling to extraction, measurement, or export internals.
- [x] Open by Default: MCP is an open JSON-RPC 2.0 based protocol; all server capabilities are discoverable via `tools/list`, `resources/list`, and `prompts/list`.

## Project Structure

### Documentation (this feature)

```text
specs/013-mcp-server/
├── spec.md              # Feature specification (done)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── mcp-tools.md     # MCP tool definitions and schemas
│   └── mcp-resources.md # MCP resource URI patterns and handlers
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # MCP server process, transport, request routing
│   ├── transport.py        # StdioTransport and SSETransport implementations
│   ├── registry.py         # Tool, resource, and prompt provider registry
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── measure.py      # run_pipeline tool
│   │   ├── specs.py        # list_specs, read_spec tools
│   │   ├── export.py       # export_results tool
│   │   └── status.py       # get_status tool
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── specs.py        # spec:// resource handler
│   │   └── measurements.py # measurement:// resource handler
│   └── prompts/
│       ├── __init__.py
│       └── templates.py    # Prompt template definitions
├── cli/
│   └── commands/
│       └── mcp.py          # `specmetrics mcp start|stop|status` commands
├── kernel/
│   └── capability_registry.py  # Shared registry (updated — used by MCP for discovery)
└── tests/
    ├── unit/
    │   └── mcp/
    │       ├── test_server.py
    │       ├── test_transport.py
    │       ├── test_registry.py
    │       ├── tools/
    │       │   ├── test_measure.py
    │       │   ├── test_specs.py
    │       │   └── test_status.py
    │       └── resources/
    │           ├── test_specs_resources.py
    │           └── test_measurements_resources.py
    └── integration/
        └── mcp/
            └── test_server_e2e.py
```

**Structure Decision**: Single-project layout with `mcp/` as a top-level package under `specmetrics/`, building on the structure established in 009-cli-mcp-interface. The `mcp/` package is organized by MCP protocol domain (tools, resources, prompts) rather than by pipeline capability, ensuring that adding a new tool does not require touching unrelated transport or registry code. The CLI `mcp` subcommand lives under `cli/commands/` following the existing CLI organization pattern.

## Complexity Tracking

No constitution violations detected — the design satisfies all engaged principles without complexity trade-offs.

## Phase 0: Research

The following decisions were researched and resolved based on the project's established technology stack and industry best practices:

| Topic | Decision | Rationale | Alternatives Considered |
|-------|----------|-----------|------------------------|
| MCP Python SDK | `mcp` package (official Python SDK) | Official SDK maintained by the MCP specification authors. Provides stdio and SSE transport implementations, JSON-RPC message handling, and tool/resource/prompt abstractions. | Custom MCP protocol implementation — unnecessary, would duplicate SDK functionality |
| Transport Layer | Stdio (default for embedded) + SSE (for network mode) | Stdio transport is the simplest for local/embedded use (direct integration with AI coding tools). SSE transport enables remote client connections as a standalone server. | WebSocket — more complex, not part of MCP spec for v1; gRPC — not supported by MCP protocol |
| Tool Discovery | Dynamic registry that polls Kernel capability registry | Tools are dynamically discovered from the Kernel's capability registry, ensuring new pipeline stages automatically appear as MCP tools without server restart (FR-012). | Static tool list — simpler but violates FR-012; decorator-based registration — less flexible for dynamic discovery |
| Resource URI Scheme | `specmetrics://{resource_type}/{identifier}` | Clear namespace isolation with `specmetrics://` scheme. Resource types map to pipeline domains: `spec`, `measurement`, `evidence`, `export`. | Hierarchical paths (`/specs/...`) — ambiguous with file paths; flat scheme — harder to extend |
| Concurrency Model | `asyncio` with `anyio` (stdlib `asyncio` for SSE, `anyio` for stdio) | MCP SDK uses `anyio` for transport abstraction. Python 3.13 asyncio provides mature async concurrency. Thread pool for CPU-bound pipeline operations. | `threading` — higher complexity for connection management; `multiprocessing` — overkill for single-user context |
| Server Lifecycle | CLI commands via Typer (`specmetrics mcp start/stop/status`) | Consistent with existing CLI pattern (009). The `start` command forks or runs the server as a managed subprocess. `stop` sends graceful shutdown signal. `status` reports server health. | Systemd service — too environment-specific; Docker-only — limits local execution use case |
| Configuration | Pydantic Settings from YAML + CLI flags | Matches the project's existing configuration approach. Server host, port, transport type, max connections, and log level are configurable. | Environment variables only — less discoverable; JSON config — YAML is the project convention |

## Phase 1: Design

### Data Model

See [data-model.md](data-model.md) for complete entity definitions, fields, validation rules, and state transitions.

### Contracts

See [contracts/mcp-tools.md](contracts/mcp-tools.md) for MCP tool definitions, input/output schemas, and handler contracts.
See [contracts/mcp-resources.md](contracts/mcp-resources.md) for resource URI patterns, content types, and handler contracts.

### Quickstart

See [quickstart.md](quickstart.md) for validation scenarios, setup instructions, and expected outcomes.
