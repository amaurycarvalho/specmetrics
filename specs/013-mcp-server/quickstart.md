# Quickstart: MCP Server

**Date**: 2026-07-15
**Feature**: MCP Server (013)

## Prerequisites

- Python 3.13+
- SpecMetrics installed and configured (`specmetrics` command available)
- MCP-compatible client (e.g., opencode, or any JSON-RPC 2.0 client for SSE mode)
- Feature dependencies: 002 Kernel Pipeline Engine, 007 Canonical Functional Model, 008 Measurement Engine, 009 CLI & MCP Interface, 011 Export Layer

## Setup

### 1. Install MCP SDK dependency

```bash
uv add mcp
```

### 2. Configure the server

Create or update `specmetrics.yml`:

```yaml
mcp:
  transport: sse          # stdio | sse
  host: 127.0.0.1
  port: 8100
  max_connections: 10
  log_level: info
  pipeline_timeout_seconds: 120
```

### 3. Start the server

```bash
# Start with SSE transport (network mode)
specmetrics mcp start

# Start with stdio transport (embedded mode)
specmetrics mcp start --transport stdio

# Start with custom port
specmetrics mcp start --port 9000
```

## Validation Scenarios

### Scenario 1: Server lifecycle

**Goal**: Verify the server starts, accepts a connection, and shuts down gracefully.

1. Start the server: `specmetrics mcp start --port 8100`
2. **Expected**: Server prints "MCP server started on 127.0.0.1:8100 (transport: sse)" and process continues running
3. Check status: `specmetrics mcp status`
4. **Expected**: Status shows "running", uptime > 0, active_connections = 0
5. Stop the server: `specmetrics mcp stop`
6. **Expected**: Server prints "MCP server stopped gracefully" and exits
7. Verify: `specmetrics mcp status`
8. **Expected**: Status shows "stopped"

### Scenario 2: Tool discovery and invocation (stdio)

**Goal**: Verify an MCP client can discover and invoke tools via stdio transport.

1. Start the server with stdio: `specmetrics mcp start --transport stdio`
2. Connect using an MCP client (e.g., opencode configured with `"transport": "stdio"`)
3. Send a `tools/list` request
4. **Expected**: Response contains `run_pipeline`, `list_specs`, `read_spec`, `export_results`, `get_status` tools with descriptions and input schemas
5. Invoke `get_status` (no parameters)
6. **Expected**: Response contains server status with state "running" and transport "stdio"

### Scenario 3: Tool discovery and invocation (SSE)

**Goal**: Verify tool discovery works over SSE transport.

1. Start the server with SSE: `specmetrics mcp start --port 8100`
2. Connect an MCP client to `http://127.0.0.1:8100` via SSE
3. Send a `tools/list` request
4. **Expected**: Same tool set as Scenario 2, confirming transport-independent behavior
5. Invoke `list_specs` with `{"project_path": "."}`
6. **Expected**: Response lists specification documents in the current project directory

### Scenario 4: Resource access

**Goal**: Verify specification documents and measurement results are accessible via resource URIs.

1. Run a measurement pipeline to generate results: `specmetrics measure`
2. Note the `run_id` from the output
3. Send a `resources/list` request
4. **Expected**: Response includes URI templates for `specmetrics://spec/{path}`, `specmetrics://measurement/{run_id}`, `specmetrics://evidence/{run_id}`, `specmetrics://export/{run_id}/{format}`
5. Read a spec resource: `specmetrics://spec/specs/013-mcp-server/spec.md`
6. **Expected**: Returns the spec document content with MIME type `text/markdown`
7. Read a measurement resource: `specmetrics://measurement/{run_id}`
8. **Expected**: Returns measurement data as JSON with run metadata and functional size results

### Scenario 5: Error handling — invalid parameters

**Goal**: Verify descriptive error responses for invalid tool parameters.

1. Invoke `run_pipeline` without required `project_path` parameter
2. **Expected**: Error response with code `-32602`, message containing "Missing required parameter: project_path"
3. Invoke `run_pipeline` with `{"project_path": "./nonexistent"}`
4. **Expected**: Error response with code `-32001`, message indicating project path does not exist

### Scenario 6: Concurrent connections

**Goal**: Verify the server handles multiple concurrent clients.

1. Start the server with `max_connections: 5`
2. Open 3 client connections simultaneously
3. Send a `get_status` request from each client
4. **Expected**: All 3 clients receive valid responses. Server status shows `active_connections: 3`.
5. Open 3 more connections (total 6, exceeding limit)
6. **Expected**: The 6th connection is rejected with a message about max connections being reached

### Scenario 7: Prompt templates

**Goal**: Verify prompt templates are available and usable.

1. Send a `prompts/list` request
2. **Expected**: Response includes prompt names and descriptions (e.g., `analyze_spec`, `measure_project`)
3. Request a specific prompt: `prompts/get` with `{"name": "measure_project"}`
4. **Expected**: Returns the prompt template with argument definitions. Arguments include `project_path`, `export_format`.
5. Fill in the template and invoke the associated tools
6. **Expected**: Workflow executes correctly (measurement runs, results returned)

## Verification Checklist

- [ ] Server starts and stops via CLI commands
- [ ] Tools are discoverable via `tools/list`
- [ ] Tool invocation returns correct results via `tools/call`
- [ ] Resources are accessible via `resources/read`
- [ ] Resource URI templates are listed in `resources/list`
- [ ] Invalid tool parameters return descriptive errors
- [ ] Nonexistent resources return "not found" errors
- [ ] Server handles multiple concurrent clients
- [ ] Connection limit enforcement works
- [ ] Server shuts down gracefully without orphaned processes
- [ ] Stdio transport works for embedded use (piped stdin/stdout)
- [ ] SSE transport works for network clients
- [ ] Prompt templates are discoverable and usable
- [ ] Server status reports accurate connection and error counts
