# Measure CLI Interface Contract

## Command: `specmetrics measure`

### Syntax

```
specmetrics measure [OPTIONS] [METRICS]
```

### Arguments

| Argument | Type | Default | Description |
|---|---|---|---|
| `METRICS` | `str` | `all` | Comma-separated metric identifiers. Valid values: `all`, `bcp`, `fpa`, `sfp`, `snap`, `sp`, `tshirt`, `tp`, `cp`. Whitespace around commas is trimmed. |

### Options

| Option | Type | Default | Description |
|---|---|---|---|
| `--output` / `-o` | `str` | — | Output format and optional path: `json`, `csv`, `xml`, `text`, or `json:./path.json` |
| `--stage` / `-s` | `str` | — | Run only this stage: `discover`, `extract`, `graph`, `cfm`, `rule`, `measure`, `export` |
| `--from` | `str` | — | Start from this stage (skip earlier stages) |
| `--verbose` / `-v` | `bool` | `False` | Show detailed per-stage progress |
| `--quiet` / `-q` | `bool` | `False` | Suppress non-error output |
| `--log-file` / `-l` | `str` | — | Persist logs to `.specmetrics/logs/<filename>` |
| `--config` / `-c` | `Path` | — | Path to configuration file |

### Exit Codes

- `0` — All selected metrics completed successfully (or partial success with errors recorded)
- `1` — Invalid metric identifier, configuration error, or pipeline failure

### Metric ID → Plugin Mapping

| CLI ID | Plugin Entry Point | JSON Name |
|---|---|---|
| `bcp` | `specmetrics.plugins.measurement.bcp` | `business_complexity_points` |
| `fpa` | `specmetrics.plugins.measurement.fpa` | `function_points` |
| `sfp` | `specmetrics.plugins.measurement.sfp` | `simplified_function_points` |
| `snap` | `specmetrics.plugins.measurement.snap` | `snap` |
| `sp` | `specmetrics.plugins.measurement.storypoints` | `story_points` |
| `tshirt` | `specmetrics.plugins.measurement.tshirt` | `tshirt` |
| `tp` | `specmetrics.plugins.measurement.token_points` | `token_points` |
| `cp` | `specmetrics.plugins.measurement.cognitive_points` | `cognitive_points` |

## JSON Output Format (`specmetrics-output.json`)

Written to `.specmetrics/output/specmetrics-output.json` by default.

```json
{
  "measure": {
    "sdd_framework": "speckit",
    "created": "2026-07-20T10:30:00Z",
    "llm": {
      "provider": "openai",
      "model": "gpt-4"
    },
    "project_path": "/home/user/project"
  },
  "results": [
    {
      "name": "function_points",
      "total": 42,
      "status": "completed",
      "duration_ms": 10542
    },
    {
      "name": "business_complexity_points",
      "total": 18,
      "status": "completed",
      "duration_ms": 15320
    },
    {
      "name": "simplified_function_points",
      "total": 38,
      "status": "completed",
      "duration_ms": 2100
    },
    {
      "name": "snap",
      "total": 15,
      "status": "completed",
      "duration_ms": 3200
    },
    {
      "name": "story_points",
      "total": 21,
      "status": "completed",
      "duration_ms": 1800
    },
    {
      "name": "tshirt",
      "total": 5,
      "status": "completed",
      "duration_ms": 500
    },
    {
      "name": "token_points",
      "total": 1200,
      "status": "completed",
      "duration_ms": 800
    },
    {
      "name": "cognitive_points",
      "total": 34,
      "status": "completed",
      "duration_ms": 1600
    }
  ],
  "stages": [
    {
      "name": "discover",
      "count": 5,
      "count_type": "documents",
      "duration_ms": 1234
    },
    {
      "name": "extract",
      "count": 24,
      "count_type": "items",
      "duration_ms": 5678
    },
    {
      "name": "measure",
      "count": 8,
      "count_type": "metrics",
      "duration_ms": 42000
    }
  ],
  "errors": []
}
```

### When a metric fails:

```json
{
  "measure": { ... },
  "results": [
    {
      "name": "function_points",
      "total": 42,
      "status": "completed",
      "duration_ms": 10542
    },
    {
      "name": "business_complexity_points",
      "total": 0,
      "status": "failed",
      "duration_ms": 30000
    }
  ],
  "errors": [
    {
      "stage": "measure",
      "message": "BCP measurement failed: LLM timeout after 30s",
      "details": {
        "metric": "bcp",
        "plugin_id": "specmetrics.plugins.measurement.bcp"
      }
    }
  ]
}
```

## Error Messages

### Invalid metric name:

```
Error: Unknown metric identifier(s): invalid_metric, bad_name
Valid identifiers: all, bcp, fpa, sfp, snap, sp, tshirt, tp, cp
```

### Empty metric list (treated as all):

(No error — silently defaults to `all`)

### Invalid combination with `--stage`:

```
Error: --stage discover specified with metric filter 'fpa'. Metric filtering only applies to the measure stage.
```
