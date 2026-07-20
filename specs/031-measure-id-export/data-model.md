# Data Model: Measure ID & Export Commands

## Entities

### MeasureRun

Represents a single execution of the measurement pipeline, persisted to disk.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Timestamp-prefixed UUID (`YYYYMMDD-HHMMSS-<short-uuid>`) |
| `created_at` | `datetime` | ISO 8601 timestamp of run creation |
| `sdd_framework` | `str` | Detected SDD framework (`speckit`, `openspec`, `unknown`) |
| `llm` | `dict` or `null` | LLM provider/model info used during extraction |
| `project_path` | `str` | Absolute path to measured project |
| `stages` | `list[StageData]` | Per-stage results (one entry per pipeline stage) |
| `results` | `list[MetricResult]` | Metric measurement results |
| `errors` | `list[ErrorRecord]` | Errors encountered during execution |

### StageData

Captures the outcome of a single pipeline stage.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Stage name (`discover`, `extract`, `graph`, `csm`, `cfm`, `rule`, `measure`) |
| `status` | `str` | Execution status (`completed`, `failed`, `skipped`) |
| `count` | `int` | Number of entities found |
| `count_type` | `str` | Type of entities (`documents`, `items`, `metrics`) |
| `duration_ms` | `int` | Stage execution time in milliseconds |
| `entities` | `list[dict]` | Stage-specific entity data (varies by stage) |

### Stage Entity Data Structures

#### Discover Stage (count_type = "documents")
```json
{
  "name": "discover",
  "entities": [
    {"document_name": "README.md", "relative_path": "README.md"},
    {"document_name": "specs/spec.md", "relative_path": "specs/spec.md"}
  ]
}
```

#### Extract / Graph / CSM / CFM / Rule Stages (count_type = "items")
```json
{
  "name": "extract",
  "entities": [
    {"id": "ent_1", "type": "function", "content": "User registration process..."}
  ]
}
```

#### Measure Stage (count_type = "metrics")
```json
{
  "name": "measure",
  "entities": [
    {"metric": "function_points", "total": 42, "status": "completed", "duration_ms": 1234}
  ]
}
```

### MetricResult

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Snake-case metric identifier (e.g., `function_points`) |
| `total` | `float` | Computed metric value |
| `status` | `str` | `completed` or `failed` |
| `duration_ms` | `int` | Computation time |

### ErrorRecord

| Field | Type | Description |
|-------|------|-------------|
| `stage` | `str` | Stage where error occurred |
| `message` | `str` | Error description |
| `details` | `str` or `null` | Additional error context |

---

## Filesystem Layout

```
.specmetrics/
├── runs/
│   ├── 20260720-143022-a1b2c3d4/
│   │   ├── metadata.json     # RunMetadata (id, created_at, sdd_framework, llm, project_path)
│   │   ├── discover.json     # StageData for discover stage
│   │   ├── extract.json      # StageData for extract stage
│   │   ├── graph.json        # StageData for graph stage
│   │   ├── csm.json          # StageData for csm stage
│   │   ├── cfm.json          # StageData for cfm stage
│   │   ├── rule.json         # StageData for rule stage
│   │   └── measure.json      # StageData for measure stage + MetricResult list
│   └── 20260720-153045-b5e6f7a8/
│       └── ...
├── output/
│   └── specmetrics-output.json   # Existing aggregated output (now with measure.id/id_path)
└── exports/                      # Export run output directory
    ├── discover.json
    ├── extract.json
    └── ... (stage files per format)
```

---

## Validation Rules

- **MeasureRun.id** must match regex `^\d{8}-\d{6}-[a-f0-9]{8}$`
- **Stages** array must contain at least one entry
- **Stage count** must be >= 0
- **duration_ms** must be >= 0
- **errors** is optional; defaults to empty list
- **metadata.json** must always be present in a run directory
- Per-stage JSON files must contain a `name` field matching the filename stage

---

## State Transitions

```
[Pipeline executed]
       |
       v
[MeasureRun created] ──> [JSON files written to .specmetrics/runs/<id>/]
       |
       +──> [specmetrics-output.json updated with measure.id/id_path]
       |
       +──> [Optional: export run triggered if --export flag set]
```
