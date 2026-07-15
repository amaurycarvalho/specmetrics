# MCP Tool Definitions

**Date**: 2026-07-15
**Feature**: MCP Server (013)
**Applies to**: `specmetrics/mcp/tools/*`

## Overview

Each managed tool is defined by a name, description, input JSON Schema, and an async handler function. Tools are registered in the MCP registry at startup via the Kernel's capability registry. This document defines the initial tool set.

## Tool: `run_pipeline`

Execute the full measurement pipeline (or a specific stage) on a given specification project.

**Input Schema** (`input_schema`):

```json
{
  "type": "object",
  "properties": {
    "project_path": {
      "type": "string",
      "description": "Path to the specification project directory"
    },
    "stage": {
      "type": "string",
      "enum": ["full", "extract", "cfm", "measure", "export"],
      "description": "Pipeline stage to execute (default: full)"
    },
    "export_format": {
      "type": "string",
      "enum": ["json", "csv"],
      "description": "Export format for results (default: json)"
    }
  },
  "required": ["project_path"]
}
```

**Output**: JSON object containing measurement results, run ID, stage timestamps, and export paths.

**Error codes**:
| Code | Condition |
|------|-----------|
| -32602 | Invalid parameters (missing `project_path`, invalid `stage` value) |
| -32000 | Pipeline execution failed (internal error in pipeline stage) |
| -32001 | Project path does not exist or contains no specifications |

**Handler Contract**:

```python
async def handle_run_pipeline(params: dict) -> dict:
    # 1. Validate params against input_schema
    # 2. Resolve project_path to absolute path
    # 3. Call orchestrator.execute_pipeline(stage, project_path, export_format)
    # 4. Return structured result with run_id, metrics, timestamps
```

## Tool: `list_specs`

List all specification documents in a project.

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "project_path": {
      "type": "string",
      "description": "Path to the specification project directory"
    }
  },
  "required": ["project_path"]
}
```

**Output**: Array of specification document summaries (name, path, type, last modified).

**Error codes**:
| Code | Condition |
|------|-----------|
| -32602 | Missing `project_path` |
| -32001 | Project path does not exist |

**Handler Contract**:

```python
async def handle_list_specs(params: dict) -> list:
    # 1. Validate params
    # 2. Discover specs via Specification Adapter
    # 3. Return list of spec summaries
```

## Tool: `read_spec`

Read the content of a specification document.

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "spec_path": {
      "type": "string",
      "description": "Path to the specification file (absolute or relative to project)"
    }
  },
  "required": ["spec_path"]
}
```

**Output**: Object with `content` (string), `path` (string), `mime_type` (string).

**Error codes**:
| Code | Condition |
|------|-----------|
| -32602 | Missing `spec_path` |
| -32002 | Spec file not found at the given path |

## Tool: `export_results`

Export measurement results in a specified format.

**Input Schema**:

```json
{
  "type": "object",
  "properties": {
    "run_id": {
      "type": "string",
      "description": "Run ID from a previous pipeline execution"
    },
    "format": {
      "type": "string",
      "enum": ["json", "csv"],
      "description": "Export format"
    },
    "output_path": {
      "type": "string",
      "description": "Optional output path (default: auto-generated)"
    }
  },
  "required": ["run_id", "format"]
}
```

**Output**: Object with `export_path` (string), `format` (string), `run_id` (string).

**Error codes**:
| Code | Condition |
|------|-----------|
| -32602 | Invalid parameters |
| -32003 | Run ID not found |
| -32000 | Export generation failed |

## Tool: `get_status`

Retrieve server health and active connection information.

**Input Schema**:

```json
{
  "type": "object",
  "properties": {}
}
```

**Output**: ServerStatus object (state, uptime, active_connections, total_requests, total_errors).

## Tool Registration

Tools are registered programmatically at server startup:

```python
registry = ToolRegistry()

registry.register(
    name="run_pipeline",
    description="Execute the measurement pipeline on a specification project",
    input_schema=RUN_PIPELINE_SCHEMA,
    handler=handle_run_pipeline,
)

registry.register(
    name="list_specs",
    description="List specification documents in a project",
    input_schema=LIST_SPECS_SCHEMA,
    handler=handle_list_specs,
)

# ... additional tool registrations
```

The MCP `tools/list` request returns all registered tools with their names, descriptions, and input schemas. The `tools/call` request dispatches to the registered handler by name.
