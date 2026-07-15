# Data Model: Kernel & Pipeline Engine

## Pipeline Context

Central container for all execution state. Immutable between stages — each
event produces a new version.

| Field | Type | Description |
|-------|------|-------------|
| `execution_id` | UUID | Unique identifier for this pipeline execution |
| `repository` | Repository (opaque) | Resolved specification repository reference |
| `adapter_result` | AdapterResult or None | Output from Specification Adapter stage |
| `evidence_graph` | EvidenceGraph or None | Output from Semantic Extraction stage |
| `canonical_model` | CanonicalModel or None | Output from CFM Builder stage |
| `measurement_result` | MeasurementResult or None | Output from Measurement Engine stage |
| `exported_files` | list[FilePath] or None | Output from Export stage |
| `published_events` | list[PipelineEvent] | Ordered list of all published events |
| `diagnostics` | Diagnostics | Execution metadata (timing, status per stage) |
| `metadata` | ExecutionMetadata | User-provided and system metadata |

### Validation Rules

- `execution_id` MUST be a valid UUID v4 generated at pipeline start
- `published_events` MUST preserve insertion order (event publication sequence)
- `diagnostics` MUST contain exactly one entry per executed stage
- Fields are `None` until their corresponding stage produces output

### State Transitions

1. **Created** — `execution_id` generated, all outputs `None`
2. **RepositoryLoaded** — `repository` populated
3. **DocumentsDiscovered** — `adapter_result` populated
4. **SemanticExtractionCompleted** — `evidence_graph` populated
5. **EvidenceGraphBuilt** — (context grows, no new field)
6. **CanonicalModelBuilt** — `canonical_model` populated
7. **RulePackApplied** — (context grows, no new field)
8. **MeasurementCompleted** — `measurement_result` populated
9. **ExportCompleted** — `exported_files` populated
10. **TelemetryPublished** — (context grows, no new field)

---

## Pipeline Event

Immutable domain event.

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | EventType | Canonical event type identifier (enum) |
| `publisher` | str | Identity of the publishing component |
| `payload` | dict | Stage-specific output data |
| `context` | PipelineContext | Snapshot of pipeline state at this point |
| `timestamp` | datetime | ISO-8601 UTC timestamp of publication |

### Event Types (enum)

| EventType | Published By |
|-----------|-------------|
| `REPOSITORY_LOADED` | Pipeline Engine |
| `DOCUMENTS_DISCOVERED` | Specification Adapter |
| `SEMANTIC_EXTRACTION_COMPLETED` | Semantic Provider |
| `EVIDENCE_GRAPH_BUILT` | Evidence Graph Builder |
| `CANONICAL_MODEL_BUILT` | Canonical Model Builder |
| `RULE_PACK_APPLIED` | Rule Pack Engine |
| `MEASUREMENT_COMPLETED` | Measurement Engine |
| `EXPORT_COMPLETED` | Export Plugin |
| `TELEMETRY_PUBLISHED` | Publisher Plugin |
| `PIPELINE_COMPLETED` | Pipeline Engine |
| `PIPELINE_FAILED` | Pipeline Engine |

### Validation Rules

- `event_type` MUST be one of the predefined enum values
- `timestamp` MUST be set at publication time, never modified afterward
- `context` MUST be the PipelineContext snapshot valid at the time of publication
- Events are append-only — never modified after publication

---

## Event Handler Registration

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | EventType | The event this handler subscribes to |
| `handler_id` | str | Unique name identifying the handler (e.g. "adapter.openspec") |
| `handler_fn` | Callable | Function receiving event, returning updated context |
| `stage_name` | str | Human-readable stage name for diagnostics |

### Validation Rules

- Each `event_type` MUST have exactly one registered handler at runtime
- Handler functions MUST be pure — no side effects beyond returning a new context
- Registration is populated once at startup, immutable during execution

---

## Execution Metadata / Diagnostics

| Field | Type | Description |
|-------|------|-------------|
| `started_at` | datetime | Pipeline start timestamp |
| `completed_at` | datetime or None | Pipeline completion timestamp |
| `stage_timings` | dict[str, StageTiming] | Per-stage: started_at, completed_at, duration_ms, status |
| `errors` | list[StageError] | Collected errors: stage, message, exception type |
| `total_duration_ms` | int or None | Total execution time in milliseconds |

### StageTiming

| Field | Type | Description |
|-------|------|-------------|
| `stage_name` | str | Name of the stage |
| `status` | StageStatus | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` |
| `started_at` | datetime | When the stage started |
| `completed_at` | datetime or None | When the stage finished |
| `duration_ms` | int or None | Elapsed time in milliseconds |

### StageError

| Field | Type | Description |
|-------|------|-------------|
| `stage_name` | str | Stage that failed |
| `message` | str | Human-readable error description |
| `exception_type` | str | Fully-qualified exception class name |
| `timestamp` | datetime | When the error occurred |

---

## Execution ID

- Format: UUID v4
- Generated once at pipeline start
- Used to correlate all events, context versions, and output artifacts
- Included in all exported files and telemetry for traceability
