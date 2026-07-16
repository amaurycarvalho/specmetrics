# Quickstart Validation Guide: CLI & MCP Interaction Layer

## Prerequisites

- SpecMetrics project initialized at `/path/to/specmetrics`
- Python 3.13+ with `uv` or `pipx`
- Build and install the development package: `uv sync` or `pip install -e .`

---

## Scenario 1: Full Pipeline via CLI

**Validates**: FR-001, FR-002, FR-005, SC-001

### Setup

```bash
# Create a minimal test project structure
mkdir -p /tmp/specmetrics-test/specs/my-feature
cat > /tmp/specmetrics-test/specs/my-feature/spec.md << 'EOF'
# Test Specification
## Requirements
- FR-001: Users can register
EOF

# Initialize specmetrics config
mkdir -p /tmp/specmetrics-test/.specmetrics
```

### Execution

```bash
# Run from the test project
specmetrics measure /tmp/specmetrics-test
```

### Expected Outcome

```
SpecMetrics v0.1.0 — Measurement Complete
────────────────────────────────────────
Project: /tmp/specmetrics-test
Pipeline: full (7 stages)
Duration: <30s

Stages:
  ✓ discover   (...s)
  ✓ extract    (...s)
  ✓ graph      (...s)
  ✓ cfm        (...s)
  ✓ rule       (...s)
  ✓ measure    (...s)
  ✓ export     (...s)

Exit code: 0
```

---

## Scenario 2: JSON Output

**Validates**: FR-003

### Execution

```bash
specmetrics measure /tmp/specmetrics-test --output json:/tmp/result.json
```

### Expected Outcome

- File `/tmp/result.json` created with valid JSON
- Contains `status`, `total_function_points`, `stages_executed`, `duration_seconds`
- Exit code: 0

---

## Scenario 3: Stage Selection

**Validates**: FR-006, FR-007

### Execution

```bash
# Single stage
specmetrics measure --stage extract /tmp/specmetrics-test

# From stage onwards
specmetrics measure --from measure /tmp/specmetrics-test
```

### Expected Outcome

- `--stage extract`: Only extraction runs; output shows 1 stage executed
- `--from measure`: Stages before `measure` are skipped; output shows `measure` and subsequent stages
- Exit code: 0

---

## Scenario 4: Error Handling

**Validates**: FR-002 (missing project), FR-005 (non-zero exit)

### Execution

```bash
specmetrics measure /tmp/nonexistent-project
```

### Expected Outcome

```
Error: Project path not found: /tmp/nonexistent-project
```
Exit code: 1

---

## Scenario 5: Plugin List

**Validates**: FR-008

### Execution

```bash
specmetrics plugins list
```

### Expected Outcome

```
Plugin List:
  openspec v0.1.0 (adapter) ✓
  speckit  v0.1.0 (adapter) ✓
  fpa      v0.1.0 (measurement) ✓
```
Exit code: 0

---

## Scenario 6: Version Command

**Validates**: FR-009

### Execution

```bash
specmetrics version
```

### Expected Outcome

```
SpecMetrics v0.1.0
Python 3.13.3
```
Exit code: 0

---

## Scenario 7: MCP Server — Measurement Request

**Validates**: FR-010, FR-013, FR-020, SC-002

### Setup

```bash
# Start MCP server in background
specmetrics-mcp &
MCP_PID=$!
```

### Execution (using a JSON-RPC client)

```bash
# Send initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
  tee /dev/stderr | \
  specmetrics-mcp | \
  head -1

# Send measure request
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"measure","arguments":{"project_path":"/tmp/specmetrics-test"}}}' | \
  specmetrics-mcp | \
  head -1
```

### Expected Outcome

- Initialize response includes server capabilities with `tools` support
- Measure response contains `result.content[0].text` with serialized `PipelineResult`

### Cleanup

```bash
kill $MCP_PID 2>/dev/null
```

---

## Scenario 8: MCP Server — Invalid Request

**Validates**: FR-014, SC-006

### Execution

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"nonexistent"}}' | \
  specmetrics-mcp | \
  head -1
```

### Expected Outcome

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32601,
    "message": "Method not found: nonexistent"
  }
}
```

---

## Scenario 9: Interface Independence

**Validates**: FR-016, SC-003

### Setup

```bash
# Run CLI to completion (no MCP needed)
specmetrics measure /tmp/specmetrics-test --output json:/tmp/cli-result.json
```

### Expected Outcome

- CLI runs without MCP server running
- MCP server starts and accepts connections without CLI running
- Both produce equivalent measurement results for the same project

---

## Scenario 10: Help Command

**Validates**: FR-017

### Execution

```bash
specmetrics --help
specmetrics measure --help
specmetrics plugins --help
specmetrics plugins list --help
```

### Expected Outcome

Each command shows usage, arguments, options, and examples. Help pages are self-consistent (no missing flags or contradictions).
