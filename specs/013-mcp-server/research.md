# Research: MCP Server

**Date**: 2026-07-15
**Feature**: MCP Server (013)

## Decisions

### MCP Python SDK

- **Decision**: Use the `mcp` Python package (official MCP protocol Python SDK)
- **Rationale**: The official SDK is maintained by the MCP specification authors and provides complete implementations of stdio and SSE transports, JSON-RPC message handling, and higher-level abstractions for tools, resources, and prompts. Using the SDK ensures protocol compliance and reduces maintenance burden.
- **Alternatives Considered**:
  - Custom MCP protocol implementation — high risk of protocol incompatibility, significant development effort, no benefit over using the SDK
  - Third-party MCP libraries — less maintained, smaller community compared to the official SDK

### Transport Layer

- **Decision**: Support both stdio transport (default for embedded use) and SSE transport (for standalone network server mode)
- **Rationale**: Stdio transport is the simplest and most reliable for local/embedded use cases — the MCP client (e.g., opencode) spawns the server as a subprocess and communicates via stdin/stdout. SSE transport enables remote clients to connect over the network, supporting the standalone server use case described in the spec. The MCP SDK provides built-in implementations for both transports.
- **Alternatives Considered**:
  - Stdio only — insufficient for remote access use case
  - WebSocket — not part of the MCP specification for v1; could be added as a future transport
  - Custom transport abstraction — unnecessary given SDK support

### Tool Discovery Mechanism

- **Decision**: Dynamic registry that polls the Kernel's capability registry for available pipeline stages, converting each registered stage into an MCP tool
- **Rationale**: This satisfies FR-012 (dynamic discoverability — new plugins automatically available without server restart). The Kernel capability registry (from 003 Plugin Discovery Registry) tracks all registered pipeline stages and their schemas. The MCP registry maps these to tool definitions and handlers.
- **Alternatives Considered**:
  - Static tool list defined at server startup — violates FR-012, requires server restart for new plugins
  - Decorator-based registration (`@mcp.tool`) — more explicit but would require separate registration per tool; Kernel registry already provides this metadata

### Resource URI Scheme

- **Decision**: `specmetrics://{resource_type}/{identifier}` URI scheme
- **Rationale**: Clear namespace isolation. Resource types map to pipeline domains: `spec` for specification documents, `measurement` for measurement results, `evidence` for evidence graph data, `export` for export artifacts. This scheme is extensible — new resource types simply add a new handler registered under a new resource type prefix.
- **Alternatives Considered**:
  - File-system-based paths (`file:///specs/...`) — ambiguous between project spec files and SpecMetrics managed data
  - Opaque identifiers — less discoverable, requires client-side knowledge of URI patterns

### Concurrency Model

- **Decision**: `asyncio` with the MCP SDK's `anyio`-based transport abstraction; thread pool for CPU-bound pipeline operations
- **Rationale**: The MCP SDK uses `anyio` for transport I/O, which runs on top of `asyncio` on CPython. Asyncio is well-suited for the I/O-bound nature of the MCP server (accepting connections, reading requests, writing responses). CPU-bound pipeline operations (measurement, extraction) are offloaded to a thread pool executor to avoid blocking the event loop. This achieves the 5+ concurrent client target (SC-002).
- **Alternatives Considered**:
  - `threading` with thread-per-connection — higher overhead per connection, more complex shutdown handling
  - `multiprocessing` — overkill for single-user context, adds IPC complexity
  - Synchronous single-thread — cannot handle concurrent clients

### Server Lifecycle Management

- **Decision**: CLI commands via Typer (`specmetrics mcp start`, `specmetrics mcp stop`, `specmetrics mcp status`)
- **Rationale**: Consistent with the existing CLI pattern established in 009-cli-mcp-interface. The `start` command runs the server as a managed subprocess, writing its PID to a file for `stop` and `status` commands. The `status` command checks the PID file and probes the server health endpoint.
- **Alternatives Considered**:
  - Systemd service — Linux-specific, not portable to macOS
  - Docker container — adds operational complexity for local execution
  - Daemon process with no lifecycle commands — requires manual process management

### Configuration

- **Decision**: Pydantic Settings model loaded from YAML configuration with CLI flag overrides
- **Rationale**: Matches the project's existing configuration pattern (Pydantic Settings + ruamel.yaml). Configuration options: `host`, `port`, `transport` (stdio/sse), `max_connections`, `log_level`, `pipeline_timeout_seconds`. CLI flags (e.g., `--port 8080`) override YAML values for quick ad-hoc configuration.
- **Alternatives Considered**:
  - CLI flags only — verbose for repeated use; no persistent configuration
  - Environment variables only — less discoverable, no configuration file for project-level settings

### Protocol Support

- **Decision**: Support MCP protocol version as advertised by the SDK; reject unsupported versions with descriptive error
- **Rationale**: The MCP SDK handles protocol version negotiation. The server advertises its supported version range. Clients requesting an unsupported version receive a clear error response (FR-009). This ensures forward compatibility as the MCP specification evolves.
- **Alternatives Considered**:
  - Always accept any version — risk of protocol incompatibility
  - Hard-code a single version — requires coordinated updates with clients
