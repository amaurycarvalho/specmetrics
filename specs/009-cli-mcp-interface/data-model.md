# Data Model: CLI & MCP Interaction Layer

## Overview

The Interaction Layer defines configuration models and contract models shared between the CLI, MCP Server, and the Pipeline Orchestrator. These are Pydantic v2 models consumed by the orchestration layer and serialized for MCP responses and CLI output.

---

## Pipeline Request

Represents a user's intention to execute the measurement pipeline — regardless of whether the request comes from CLI or MCP.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_path` | `Path` | Yes | Path to the SpecMetrics project (defaults to cwd) |
| `stages` | `list[StageName]` | No | Specific stages to run (None = full pipeline) |
| `from_stage` | `StageName` | No | Start pipeline from this stage |
| `output_format` | `OutputFormat` | No | Export format: `json`, `csv`, `xml`, or `none` |
| `output_path` | `Path` | No | Where to write export output |
| `verbose` | `bool` | No | Enable detailed progress output |
| `quiet` | `bool` | No | Suppress non-error output |

**Validation rules**:
- `stages` and `from_stage` are mutually exclusive
- `output_format` requires a compatible `output_path` or defaults to project directory
- `verbose` and `quiet` are mutually exclusive

---

## StageName

Enum matching the canonical pipeline stage names (resolved from research.md).

| Value | Pipeline Event |
|-------|---------------|
| `discover` | RepositoryLoaded |
| `extract` | DocumentsDiscovered |
| `graph` | SemanticExtractionCompleted |
| `cfm` | EvidenceGraphBuilt |
| `rule` | CanonicalModelBuilt |
| `measure` | RulePackApplied |
| `export` | MeasurementCompleted |

---

## OutputFormat

Enum: `json`, `csv`, `xml`, `text`, `none`

`text` is the default for terminal display. `none` suppresses file output.

---

## PipelineResult

The structured response produced by the Pipeline Orchestrator after execution.

| Field | Type | Description |
|-------|------|-------------|
| `status` | `PipelineStatus` | `success`, `partial`, `failed` |
| `project_path` | `Path` | Resolved project path |
| `stages_executed` | `list[StageResult]` | Results for each executed stage |
| `measurement` | `MeasurementResult` | Final measurement output (if completed) |
| `duration_seconds` | `float` | Total wall-clock time |
| `error` | `str` | Error message if status is `failed` or `partial` |
| `export_path` | `Path` | Path to exported output file (if any) |

---

## StageResult

| Field | Type | Description |
|-------|------|-------------|
| `stage` | `StageName` | Which stage |
| `status` | `StageStatus` | `pending`, `running`, `completed`, `skipped`, `failed` |
| `duration_seconds` | `float` | Stage execution time |
| `entities_found` | `int` | Count of entities extracted/processed |

---

## MeasurementResult

The structured measurement output (opaque to the Interaction Layer — produced by the Measurement Engine).

| Field | Type | Description |
|-------|------|-------------|
| `total_function_points` | `int` | Total FP count |
| `breakdown` | `dict[str, int]` | Per-type breakdown (ILF, EIF, EI, EO, EQ) |
| `complexity_distribution` | `dict[str, dict[str, int]]` | Complexity by type (Low, Avg, High) |
| `evidence_refs` | `list[str]` | Evidence references for traceability |
| `applied_rule_pack` | `str` | Rule pack identifier used |

---

## MCP Tool Definition

Each MCP tool is registered with a name, description, and typed parameter schema.

| Tool Name | Description | Parameters | Returns |
|-----------|-------------|------------|---------|
| `measure` | Execute the measurement pipeline | `project_path` (string, required), `output_format` (string, optional), `from_stage` (string, optional) | `PipelineResult` |
| `plugins_list` | List installed plugins | none | `list[PluginInfo]` |
| `specmetrics_version` | Get platform version | none | `VersionInfo` |

---

## PluginInfo

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Plugin package name |
| `version` | `str` | Installed version |
| `type` | `str` | Plugin family (adapter, measurement, export, etc.) |
| `enabled` | `bool` | Whether the plugin is active |
| `compatible` | `bool` | Whether version is compatible with platform |

---

## VersionInfo

| Field | Type | Description |
|-------|------|-------------|
| `platform_version` | `str` | SpecMetrics platform version |
| `python_version` | `str` | Python runtime version |
| `plugins` | `list[PluginInfo]` | Installed plugins |

---

## Configuration Schema (`.specify/config.yml`)

```yaml
# CLI/MCP Configuration — loaded from .specify/ directory
pipeline:
  default_stages: full              # full | stage name
  default_output_format: json       # json | csv | xml | text | none
  verbose: false

plugins:
  enabled_only: false               # if true, only enabled plugins run
  verify_compatibility: true        # fail on incompatible plugins

mcp:
  transport: stdio                  # stdio only for MVP
  log_level: info                   # stderr log level
```
