# Data Model: MCP Server

**Date**: 2026-07-15
**Feature**: MCP Server (013)

## Entities

### ServerConfiguration

Represents the full configuration for the MCP server instance.

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `host` | string | yes | Network interface to bind (SSE mode) | Default: `127.0.0.1` |
| `port` | integer | yes | TCP port to listen on (SSE mode) | Must be 1024–65535; default: `8100` |
| `transport` | enum | yes | Transport protocol: `stdio` or `sse` | Default: `stdio` |
| `max_connections` | integer | yes | Maximum concurrent client connections | Must be >= 1; default: `10` |
| `log_level` | enum | yes | Logging verbosity | `debug`, `info`, `warning`, `error`; default: `info` |
| `pipeline_timeout_seconds` | integer | yes | Max wait time for pipeline tool execution | Must be >= 30; default: `120` |
| `shutdown_timeout_seconds` | integer | yes | Max wait for in-flight requests on shutdown | Must be >= 1; default: `10` |

### MCPToolDefinition

A single tool exposed via MCP, wrapping a pipeline capability.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Tool name (e.g., `run_pipeline`, `list_specs`) |
| `description` | string | yes | Human-readable description of what the tool does |
| `input_schema` | dict | yes | JSON Schema defining valid input parameters |
| `handler` | callable | yes | Async function implementing the tool logic |
| `pipeline_capability` | string | no | Name of the underlying pipeline capability this tool wraps (if applicable) |
| `timeout_seconds` | integer | no | Custom timeout for this tool; inherits server default if unset |

**Relationships**: A `MCPToolDefinition` wraps a pipeline capability from the Kernel's capability registry. Multiple tools may reference the same pipeline capability with different parameters (e.g., `run_pipeline` with `--stage` flag vs `run_full_pipeline`).

### MCPResourceDefinition

A resource type exposed via MCP, mapping URI patterns to content handlers.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `uri_pattern` | string | yes | URI template pattern (e.g., `specmetrics://spec/{path}`) |
| `name` | string | yes | Human-readable name for the resource type |
| `description` | string | yes | Description of what this resource provides |
| `mime_type` | string | yes | Content type (e.g., `text/markdown`, `application/json`) |
| `handler` | callable | yes | Async function that resolves a URI to content |

**URI Patterns**:

| URI Pattern | MIME Type | Description |
|-------------|-----------|-------------|
| `specmetrics://spec/{path}` | `text/markdown` | Access specification documents by filesystem path |
| `specmetrics://measurement/{run_id}` | `application/json` | Access measurement results by run ID |
| `specmetrics://evidence/{run_id}` | `application/json` | Access evidence graph data for a run |
| `specmetrics://export/{run_id}/{format}` | `text/plain` | Access exported results by format (json, csv) |

### MCPPromptDefinition

A pre-defined prompt template for common workflows.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Prompt name (e.g., `analyze_spec`, `measure_project`) |
| `description` | string | yes | Description of when to use this prompt |
| `template` | string | yes | Prompt template string with `{parameter}` placeholders |
| `arguments` | list[PromptArgument] | yes | Argument definitions for template parameters |

### PromptArgument

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Argument name (matches `{placeholder}` in template) |
| `description` | string | yes | Description of what this argument represents |
| `required` | boolean | yes | Whether the argument is required |

### MCPConnection

Represents a single active client connection to the server.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `connection_id` | string | yes | Unique identifier for this connection |
| `transport_type` | enum | yes | `stdio` or `sse` |
| `protocol_version` | string | yes | MCP protocol version negotiated with client |
| `connected_at` | datetime | yes | When the connection was established |
| `last_activity_at` | datetime | yes | Timestamp of the last request from this client |
| `active_request_id` | string | no | ID of the currently executing request, if any |

### ServerStatus

Represents the overall health and state of the MCP server.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `state` | enum | yes | `running`, `stopped`, `starting`, `stopping` |
| `uptime_seconds` | float | yes | Seconds since server started |
| `active_connections` | integer | yes | Number of currently connected clients |
| `max_connections` | integer | yes | Configured maximum connections |
| `total_requests_handled` | integer | yes | Cumulative count of processed requests |
| `total_errors` | integer | yes | Cumulative count of errors encountered |
| `last_error_timestamp` | datetime | no | When the last error occurred |
| `transport` | enum | yes | Active transport type |
| `version` | string | yes | MCP protocol version being served |

### ToolRequest

Represents a single tool invocation request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | yes | Unique request identifier from client |
| `tool_name` | string | yes | Name of the tool being invoked |
| `parameters` | dict | yes | Input parameters per tool's input schema |
| `received_at` | datetime | yes | When the request was received |
| `connection_id` | string | yes | Which connection sent this request |

### ToolResponse

Represents the result of a tool invocation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | yes | Matches the request this responds to |
| `success` | boolean | yes | Whether the invocation succeeded |
| `result` | any | no | The tool's output (present on success) |
| `error` | ToolError | no | Error details (present on failure) |

### ToolError

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | integer | yes | Error code (MCP standard error codes) |
| `message` | string | yes | Human-readable error message |
| `details` | dict | no | Additional context (invalid parameter name, expected values, etc.) |

## State Transitions

### Server State Machine

```text
[stopped] → [starting] → [running] → [stopping] → [stopped]
                ↑              ↓
                └── [error] ←──┘
```

- **stopped → starting**: `specmetrics mcp start` command or programmatic `server.start()`
- **starting → running**: Transport bound, registry initialized, accepting connections
- **starting → error**: Port in use, configuration invalid, transport initialization failed
- **running → stopping**: `specmetrics mcp stop` command, shutdown signal (SIGTERM/SIGINT), or unrecoverable error
- **stopping → stopped**: All connections drained, in-flight requests completed or timed out
- **running → error**: Unrecoverable internal error (e.g., registry corruption, transport failure)

### Connection State Machine

```text
[connecting] → [active] → [disconnecting] → [disconnected]
                    ↓
               [error]
```

- **connecting → active**: Protocol handshake completed, version negotiated
- **active → disconnecting**: Client sends close, server initiates shutdown, idle timeout exceeded
- **active → error**: Transport error, protocol violation, unhandled exception during request processing

## Validation Rules

1. **Configuration validation**: All `ServerConfiguration` fields validated at server startup. Invalid configuration reports all violations.
2. **Tool input validation** (FR-005): Every tool invocation validates parameters against the tool's `input_schema` (JSON Schema). Invalid parameters return a `ToolError` with code `-32602` (Invalid Params per JSON-RPC) and details identifying the invalid field, the provided value, and the expected format.
3. **URI resolution**: Resource URIs must match a registered `uri_pattern`. Unmatched URIs return a "resource not found" error with code `-32601`.
4. **Connection limits** (FR-006): When `active_connections` reaches `max_connections`, new connection attempts are rejected with a descriptive message. The count resets on disconnection.
5. **Protocol version check** (FR-009): Incoming connections must request a supported protocol version. Unsupported versions return a protocol error before any tool/resource/prompt exchange.
6. **Graceful shutdown** (FR-010): On shutdown signal, the server stops accepting new connections, waits for in-flight requests up to `shutdown_timeout_seconds`, then forcefully terminates remaining connections.
