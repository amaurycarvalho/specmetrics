# Data Model: Export Layer

**Phase 1 output for `/speckit.plan` command**

Extracted from `spec.md` Key Entities section, validated against requirements and constitution.

---

## Entity: ExportFormat

Represents a serialization format registered via the plugin system.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | `str` | Unique format identifier | Matches entry point name; lowercase alphanumeric + hyphens |
| `name` | `str` | Human-readable name | 3–50 chars |
| `description` | `str` | Short description of the format | Optional |
| `file_extension` | `str` | Default file extension (e.g., `.json`) | Starts with `.`; 2–6 chars |
| `content_type` | `str` | MIME type for the format | Valid MIME type string |
| `serializer` | `ExporterPlugin` | Plugin instance that performs serialization | Must implement `ExporterPlugin` interface |

**Validation rules**:
- Format ID must be unique across all registered exporters.
- File extension must not conflict with another registered format.
- Serializer plugin must pass capability check on registration.

**Relationships**:
- An `ExportFormat` is the registration record. The actual serialization logic lives in the plugin.
- An `ExportFormat` produces one `ExportArtifact` per invocation.

---

## Entity: ExportArtifact

Represents a single exported output (file or stream).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `format` | `ExportFormat` | The format used for this artifact | Must be a registered format |
| `output_path` | `Optional[Path]` | File path if written to disk, or `None` for stdout | Must be writable; parent dir must exist |
| `measurements` | `list[Measurement]` | The measurement data being exported | From Canonical Functional Model |
| `evidence_refs` | `list[EvidenceRef]` | Evidence references for traceability (FR-002) | At least one per measurement |
| `metadata` | `ExportMetadata` | Run metadata (FR-010) | See below |
| `created_at` | `datetime` | Timestamp of export | ISO 8601 UTC |

**ExportMetadata**:

| Field | Type | Description |
|-------|------|-------------|
| `specmetrics_version` | `str` | Version of SpecMetrics that produced this export |
| `run_id` | `str` | Unique measurement run identifier |
| `export_timestamp` | `datetime` | When the export was created |
| `function_count` | `int` | Number of functions in this export |
| `pipeline_duration_ms` | `int` | Total pipeline duration in milliseconds |

**Validation rules**:
- `evidence_refs` must contain at least one reference per measurement (FR-002).
- `output_path` parent directory must exist and be writable.
- On zero measurements, produce empty file (valid empty array/row/element).

**State transitions**:
1. **Pending** → Artifact requested but serialization not started
2. **Serializing** → Plugin actively producing output
3. **Completed** → Output written successfully
4. **Failed** → Plugin raised an error; warning logged, other formats continue

---

## Entity: PublisherTarget

Represents an external telemetry destination for measurement publishing.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | `str` | Unique publisher identifier | Matches entry point name |
| `name` | `str` | Human-readable name | 3–50 chars |
| `endpoint_url` | `str` | URL of the telemetry endpoint | Must be valid URL |
| `auth_credentials` | `Optional[dict]` | Authentication credentials for endpoint | Optional; stored via config |
| `publishing_interval` | `int` | Interval in seconds between publications | ≥ 1 |
| `publisher_plugin` | `PublisherPlugin` | Plugin instance | Must implement `PublisherPlugin` interface |
| `enabled` | `bool` | Whether this publisher is active | Default: true |

**Validation rules**:
- Endpoint URL must be reachable on initial configuration (with timeout).
- Publishing interval must be ≥ 1 second.
- If `enabled` is `true` but endpoint is unreachable, log warning and continue (FR-006).

**Relationships**:
- A `PublisherTarget` consumes measurements from the same `MeasurementRun` as export artifacts.
- A `PublisherTarget` failure does not affect other publishers or exporters.

---

## Entity: MeasurementRun

Identifies a single execution of the measurement pipeline.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `run_id` | `str` | Unique run identifier | UUID v4 |
| `started_at` | `datetime` | Pipeline start time | ISO 8601 UTC |
| `completed_at` | `datetime` | Pipeline completion time | ISO 8601 UTC; must be ≥ started_at |
| `function_count` | `int` | Number of measured functions | ≥ 0 |
| `measurements` | `list[Measurement]` | Canonical measurement results | From CFM |
| `status` | `RunStatus` | Pipeline execution status | `success`, `partial`, `error` |

**RunStatus**: `str` enum with values `success`, `partial`, `error`.

**Validation rules**:
- `run_id` must be unique across all runs (no dedup requirement in v1; archival is future).
- `completed_at` must be ≥ `started_at`.
- `status` is `error` only if the measurement engine itself failed (export failures do not change run status).

---

## Entity: Measurement (from Canonical Functional Model)

The core measurement record consumed by exporters and publishers. This entity lives in the
kernel's CFM; the export layer references it but does not own it.

| Field | Type | Description |
|-------|------|-------------|
| `function_id` | `str` | Unique identifier of the measured function/spec element |
| `function_name` | `str` | Human-readable function name |
| `category` | `str` | Functional category (e.g., `data`, `transaction`, `interface`) |
| `complexity` | `str` | Complexity rating: `simple`, `medium`, `complex` |
| `functional_size` | `float` | Measured functional size in FPA units |
| `evidence` | `list[EvidenceRef]` | Evidence links back to source specification |
| `attributes` | `dict[str, Any]` | Extended attributes from Rule Pack application |

---

## Entity: EvidenceRef

Links a measurement back to its source specification location.

| Field | Type | Description |
|-------|------|-------------|
| `document` | `str` | Source specification document path/name |
| `section` | `str` | Section identifier within the document |
| `text` | `str` | The specific text fragment that justifies this measurement |
| `offset` | `int` | Character offset within the document (optional) |

---

## Validation Cross-Reference

| Requirement | Validation Rule Location |
|-------------|------------------------|
| FR-001: Export to JSON/CSV/XML | Registered `ExportFormat` entries for each format |
| FR-002: Evidence traceability | `evidence_refs` on `ExportArtifact` |
| FR-003: Format selection via config | `ExportFormat` registration + configuration |
| FR-004: OpenTelemetry publishing | `PublisherTarget` with `endpoint_url` |
| FR-005: CFM-only consumption | `ExportArtifact.measurements` type from CFM |
| FR-006: Publisher failure isolation | `PublisherTarget.enabled` + error handling rules |
| FR-007: Plugin discovery | Plugin registry integration (separate spec) |
| FR-008: Plugin interface contract | `ExporterPlugin` and `PublisherPlugin` contracts |
| FR-009: Clear error reporting | State transitions to `Failed` on `ExportArtifact` |
| FR-010: Export metadata | `ExportMetadata` embedded in `ExportArtifact` |
