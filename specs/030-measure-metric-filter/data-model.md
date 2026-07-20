# Data Model: Measure Metric Filtering & JSON Output

## Entities

### MeasureOutput

The root structure of `specmetrics-output.json`.

| Field | Type | Description |
|---|---|---|
| `measure` | MeasureMetadata | Metadata about the measurement run |
| `results` | list[MetricResult] | Per-metric measurement results |
| `stages` | list[StageInfo] | Per-stage execution information |
| `errors` | list[ErrorRecord] | Errors encountered during execution |

**Relationships**: Contains one MeasureMetadata, one MetricResult per selected metric, one StageInfo per executed stage, zero or more ErrorRecord entries.

### MeasureMetadata

Metadata block identifying the measurement context.

| Field | Type | Description |
|---|---|---|
| `sdd_framework` | str | Detected SDD framework: `"speckit"` or `"openspec"` |
| `created` | str | ISO 8601 datetime of measurement execution |
| `llm` | dict | `{ "provider": "...", "model": "..." }` from active LLM config |
| `project_path` | str | Resolved absolute path to the project |

### MetricResult

Result for a single measured metric.

| Field | Type | Description |
|---|---|---|
| `name` | str | Snake_case metric name (e.g., `function_points`, `business_complexity_points`) |
| `total` | int | Total value for this metric |
| `status` | str | `"completed"`, `"failed"`, or `"skipped"` |
| `duration_ms` | int | Execution time in milliseconds |

### StageInfo

Execution information for a single pipeline stage.

| Field | Type | Description |
|---|---|---|
| `name` | str | Stage name (e.g., `discover`, `extract`, `measure`) |
| `count` | int | Number of items processed |
| `count_type` | str | Type of items counted (e.g., `documents`, `items`) |
| `duration_ms` | int | Execution time in milliseconds |

### ErrorRecord

An error encountered during pipeline execution.

| Field | Type | Description |
|---|---|---|
| `stage` | str | Stage where the error occurred |
| `message` | str | Error description |
| `details` | dict \| None | Additional error context (optional) |

### PipelineRequest (application model)

Extended to carry metric filter selection.

| Field | Type | Description |
|---|---|---|
| `project_path` | Path | Path to the SpecMetrics project |
| `metrics_filter` | list[str] \| None | Selected metric identifiers or `None` for all |
| `stages` | list[StageName] \| None | Stage filter (existing) |
| `from_stage` | StageName \| None | Start stage (existing) |
| `output_format` | OutputFormat | Output format enum |
| `output_path` | Path \| None | Custom output path |
| `verbose` | bool | Verbose output flag |
| `quiet` | bool | Quiet mode flag |

### MetricNameMapping

Mapping from CLI metric short ID to canonical JSON output name.

| Source ID | JSON Name |
|---|---|
| `bcp` | `business_complexity_points` |
| `fpa` | `function_points` |
| `sfp` | `simplified_function_points` |
| `snap` | `snap` |
| `sp` | `story_points` |
| `tshirt` | `tshirt` |
| `tp` | `token_points` |
| `cp` | `cognitive_points` |

## State Transitions

```text
User runs: specmetrics measure [metrics]
         │
         ▼
  CLI (app.py) parses optional positional argument
         │
         ▼
  run_measure() validates metric IDs
         │
         ├── Invalid IDs → Print error, exit 1
         └── Valid IDs → PipelineRequest.metrics_filter = parsed list
                 │
                 ▼
          PipelineOrchestrator.execute(request)
                 │
                 ├── Run discovery → extraction → CFM → Rule Pack stages (unchanged)
                 │
                 ├── Measurement stage:
                 │     For each registered measurement plugin:
                 │       └── If metrics_filter is None or "all" or plugin ID in filter → execute
                 │       └── Else → skip (mark as SKIPPED, duration = 0)
                 │
                 ├── Collect results per metric:
                 │     ├── total, status, duration_ms
                 │     └── Aggregate errors
                 │
                 └── Export stage:
                       └── Write specmetrics-output.json
                       └── Print text summary to stdout
```

## Validation Rules

| Rule | Description |
|---|---|
| `metric-id-valid` | Every metric ID must be one of: `all`, `bcp`, `fpa`, `sfp`, `snap`, `sp`, `tshirt`, `tp`, `cp` |
| `no-duplicate-metrics` | Duplicate metric IDs are ignored (not an error) |
| `all-override` | If `all` appears in the list, treat as `all` regardless of other entries |
| `json-schema-conformant` | `specmetrics-output.json` must validate against the defined schema |
| `error-array-exists` | `errors` array must always be present (may be empty) |
