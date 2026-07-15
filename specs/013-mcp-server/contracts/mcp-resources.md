# MCP Resource Definitions

**Date**: 2026-07-15
**Feature**: MCP Server (013)
**Applies to**: `specmetrics/mcp/resources/*`

## URI Scheme

All SpecMetrics resources use the URI scheme `specmetrics://` with the following pattern:

```
specmetrics://{resource_type}/{identifier}[?query_parameters]
```

The server advertises supported resource URI templates via the MCP `resources/list` request. Clients construct URIs from these templates by substituting `{identifier}` values.

## Resource: Specification Document

**URI Pattern**: `specmetrics://spec/{path}`

**Template**: `specmetrics://spec/{path}` — `{path}` is the filesystem path to the specification document (absolute or relative to the project root).

**MIME Type**: `text/markdown`

**Content**: The raw content of the specification document. If the document is in markdown format, it is returned as-is. Other formats (JSON, YAML) are returned with the appropriate MIME type.

**Example**: `specmetrics://spec/specs/013-mcp-server/spec.md`

**Handler Contract**:

```python
async def handle_spec_resource(uri: str) -> ResourceContent:
    # 1. Parse URI to extract {path}
    # 2. Resolve path (relative to project root if not absolute)
    # 3. Read file content
    # 4. Return content with MIME type
    # 5. Return ResourceNotFoundError if path does not exist or is outside project
```

**Error codes**:
| Code | Condition |
|------|-----------|
| -32601 | Resource not found — path does not exist |
| -32002 | Path resolution error (path traversal detected) |

## Resource: Measurement Results

**URI Pattern**: `specmetrics://measurement/{run_id}`

**Template**: `specmetrics://measurement/{run_id}` — `{run_id}` is the unique identifier from a pipeline execution.

**MIME Type**: `application/json`

**Content**: JSON object containing the full measurement results for the specified run, including function counts, function points, complexity distribution, and metadata.

**Example**: `specmetrics://measurement/run_20260715_143022_abc123`

**Handler Contract**:

```python
async def handle_measurement_resource(uri: str) -> ResourceContent:
    # 1. Parse URI to extract {run_id}
    # 2. Look up run data from the Export Layer's run store
    # 3. Return measurement results as JSON
    # 4. Return ResourceNotFoundError if run_id is unknown
```

**Error codes**:
| Code | Condition |
|------|-----------|
| -32601 | Run ID not found |
| -32000 | Error loading measurement data |

## Resource: Evidence Graph

**URI Pattern**: `specmetrics://evidence/{run_id}`

**Template**: `specmetrics://evidence/{run_id}` — `{run_id}` is the unique identifier from a pipeline execution.

**MIME Type**: `application/json`

**Content**: JSON object containing the evidence graph data for the specified run, linking each measurement to its source specification elements with full provenance.

**Example**: `specmetrics://evidence/run_20260715_143022_abc123`

**Handler Contract**:

```python
async def handle_evidence_resource(uri: str) -> ResourceContent:
    # 1. Parse URI to extract {run_id}
    # 2. Look up evidence graph data
    # 3. Return graph as JSON adjacency list or node/edge structure
    # 4. Return ResourceNotFoundError if run_id is unknown
```

## Resource: Export Artifact

**URI Pattern**: `specmetrics://export/{run_id}/{format}`

**Template**: `specmetrics://export/{run_id}/{format}` — `{run_id}` is the run identifier, `{format}` is the export format (`json`, `csv`).

**MIME Type**: `text/plain` for CSV, `application/json` for JSON

**Content**: The exported measurement results in the requested format.

**Example**: `specmetrics://export/run_20260715_143022_abc123/csv`

## Resource Registration

```python
registry = ResourceRegistry()

registry.register(
    uri_template="specmetrics://spec/{path}",
    name="Specification Document",
    description="Access specification document content by path",
    mime_type="text/markdown",
    handler=handle_spec_resource,
)

registry.register(
    uri_template="specmetrics://measurement/{run_id}",
    name="Measurement Results",
    description="Access measurement results by run ID",
    mime_type="application/json",
    handler=handle_measurement_resource,
)

# ... additional resource registrations
```

## Path Traversal Protection

Resource handlers that resolve filesystem paths MUST validate that the resolved path is within the allowed project directory. Paths containing `..` segments that escape the project root are rejected with a `-32002` error code.
