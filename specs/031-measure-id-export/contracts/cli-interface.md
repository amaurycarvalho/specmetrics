# CLI Interface Contracts: Measure ID & Export Commands

## Command: `specmetrics measure`

**Purpose**: Execute measurement pipeline with optional export.

**Syntax**:
```
specmetrics measure [PROJECT_PATH] [--metrics METRICS] [--export] [--format FORMAT]
                     [--output OUTPUT] [--stage STAGE] [--from STAGE]
                     [--verbose | --quiet] [--log-file FILE] [--config FILE]
```

**New parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--export` | flag | `false` | Automatically run `export run` after measurement completes |
| `--format` | string | `json` | Export format(s) when `--export` is used (comma-separated: `json,csv,xml`) |

**Behavior**:
1. Generates a timestamp-prefixed UUID measure ID
2. Executes the measurement pipeline (existing logic)
3. Prints `Measure ID: <id>` to stdout
4. Writes per-stage JSON files to `.specmetrics/runs/<id>/`
5. Updates `.specmetrics/output/specmetrics-output.json` with `measure.id` and `measure.id_path`
6. If `--export` is set, calls `export run <id> --format <format>` automatically

**Exit codes**:
- `0`: Success (including partial success with errors recorded)
- `1`: Fatal error (configuration, invalid arguments)

---

## Command: `specmetrics export list`

**Purpose**: List all available measure run IDs.

**Syntax**:
```
specmetrics export list [PROJECT_PATH] [--verbose | --quiet]
```

**Behavior**:
1. Scans `.specmetrics/runs/` for subdirectories matching the measure ID pattern
2. Orders entries from most recent to oldest (by directory name descending)
3. Prints each ID and its creation timestamp

**Output format**:
```
Measure ID            | Created
----------------------|----------------------------
20260720-143022-a1b2c3d4 | 2026-07-20 14:30:22
20260720-153045-b5e6f7a8 | 2026-07-20 15:30:45
```

**When no runs exist**:
```
No measure runs found.
```

**Exit codes**:
- `0`: Success
- `1`: Project path not found or inaccessible

---

## Command: `specmetrics export run`

**Purpose**: Export measurement results from a specific (or latest) measure run.

**Syntax**:
```
specmetrics export run [<MEASURE-ID>] [PROJECT_PATH] [--format FORMAT] [--output-dir DIR]
                        [--publish] [--otel-endpoint URL] [--verbose | --quiet]
```

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `<MEASURE-ID>` | positional | *(latest run)* | Specific measure ID to export |
| `--format` | string | `json` | Export format(s): `json`, `csv`, `xml`, or comma-separated |

**Behavior**:
1. If `<MEASURE-ID>` is provided:
   - Reads from `.specmetrics/runs/<MEASURE-ID>/`
   - If directory does not exist, prints error and exits with code 1
2. If `<MEASURE-ID>` is omitted:
   - Scans `.specmetrics/runs/` for the most recent run (latest directory name)
   - If no runs exist, falls back to running the measurement pipeline directly (backward compatible)
3. For JSON format: copies files from the run directory to `exports/`
4. For CSV/XML format: loads each stage's JSON, normalizes to tabular form, writes per-stage files

**Output directory**:
```
exports/
├── discover.<ext>
├── extract.<ext>
├── graph.<ext>
├── csm.<ext>
├── cfm.<ext>
├── rule.<ext>
└── measure.<ext>
```

**Exit codes**:
- `0`: Success
- `1`: Specified measure ID not found; project path not found; fatal export error

---

## Tabular Normalization Formats (CSV/XML)

### Discover Stage
```
document_name, relative_path
README.md, README.md
specs/spec.md, specs/spec.md
```

### Measure Stage
```
metric, total, status, duration_ms
function_points, 42, completed, 1234
story_points, 10, completed, 567
```

### Extract / Graph / CSM / CFM / Rule Stages
Each item is flattened to key-value columns. Varying fields per item type.
```
id, type, content, ...
ent_1, function, "User registration...", ...
```
