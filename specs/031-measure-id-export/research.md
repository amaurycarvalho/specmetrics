# Research: Measure ID & Export Commands

## Decisions

### Decision 1: Measure ID Format

- **Decision**: Timestamp-prefixed UUID (`YYYYMMDD-HHMMSS-<short-uuid>`)
- **Rationale**: Encodes creation time directly in the directory name, enabling natural ordering for `export list` and "most recent run" detection without separate metadata storage. The short-uuid suffix (first 8 hex chars of UUID4) guarantees uniqueness even within the same second.
- **Alternatives considered**:
  - Pure UUID v4: requires separate `.metadata.json` per run to store timestamps for ordering; adds complexity
  - Pure timestamp: collisions possible with concurrent runs
  - Sequential number: fragile across machines and concurrent executions

### Decision 2: `export run` Backward Compatibility

- **Decision**: Fall back to running the pipeline directly when no measure runs exist
- **Rationale**: Preserves existing scripts and workflows that call `export run` independently. The new read-from-run-directory behavior activates only when run directories are present. When a specific ID is requested and not found, an error is shown.
- **Alternatives considered**:
  - Pure new behavior: breaks existing callers, requiring them to run `measure` first
  - Flag-gated: adds unnecessary complexity; users must remember a `--from-run` flag

### Decision 3: CSV/XML Conversion Approach

- **Decision**: Normalize each stage's data to a tabular format (rows+columns) and serialize using generic CSV/XML writers
- **Rationale**: The existing CFM-based exporter plugins (`JsonExporter`, `CsvExporter`, `XmlExporter`) operate on `Measurement` objects extracted from the Canonical Functional Model, which does not map to per-stage data (documents list, items with content, metric results). Tabular normalization is lightweight, stage-appropriate, and avoids coupling to CFM-specific interfaces. JSON export continues to be a direct file copy.
- **Alternatives considered**:
  - New per-stage converters: more code to maintain per stage type
  - Wrap as fake `Measurement` objects: couples stage data to CFM schema; adds conceptual confusion
  - Re-run pipeline export stage: bypasses the persisted-run benefit entirely

## Pipeline Stage Data Inventory

| Stage | `count_type` | Data to export |
|-------|-------------|----------------|
| discover | documents | Document names + relative paths |
| extract | items | Extracted items with content |
| graph | items | Evidence graph node/edge summary |
| csm | items | Canonical Spec Model elements |
| cfm | items | Canonical Functional Model elements |
| rule | items | Applied rule pack results |
| measure | metrics | Metric names + total values + breakdown |

## Existing Code Patterns

### Measure ID Generation
- `PipelineContext.execution_id` uses `uuid4()` — existing UUID generation pattern to reuse
- `PipelineResult.run_id` stores the UUID as a string
- New pattern: combine timestamp + short UUID for directory naming

### JSON Output Structure (`MeasureOutput`)
```python
class MeasureOutput(BaseModel):
    measure: MeasureMetadata
    results: list[MetricResult]
    stages: list[StageInfo]
    errors: list[ErrorRecord]
```

### Export Flow (current)
1. CLI `export run` → `PipelineOrchestrator.execute()` (full pipeline re-run)
2. `ExportOrchestrator.export_to_dir(cfm, output_dir, formats)` 
3. Each exporter plugin serializes `Measurement` list

### Export Flow (new)
1. CLI `export run <id>` → read `.specmetrics/runs/<id>/`
2. For JSON: `shutil.copytree()` or equivalent
3. For CSV/XML: load per-stage JSON, normalize to rows+columns, write via `csv.writer` / `xml.etree.ElementTree`
