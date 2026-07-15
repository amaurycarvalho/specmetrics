# Data Model: OpenTelemetry Publisher

**Date**: 2026-07-15
**Feature**: OpenTelemetry Publisher (012)

## Entities

### PublisherConfiguration

Represents the full configuration for a single publisher instance (one per telemetry endpoint).

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `endpoint_url` | string | yes | OTLP receiver URL (e.g., `https://otlp.example.com:4318`) | Must be a valid URL with scheme (http/https/grpc) |
| `protocol` | enum | yes | Transport protocol: `grpc` or `http` | Must be one of the supported values; default: `grpc` |
| `api_key` | string | no | API key for authenticated endpoints | If provided, must be non-empty |
| `tls_enabled` | boolean | yes | Enable TLS for the connection | Default: `true` |
| `tls_verify` | boolean | yes | Verify server certificate | Default: `true`; ignored when `tls_enabled` is false |
| `tls_ca_cert_path` | string | no | Path to custom CA certificate file | If provided, must reference an existing file |
| `timeout_seconds` | integer | yes | Connection and request timeout | Must be >= 1; default: 10 |
| `batch_interval_seconds` | integer | yes | Max time between batch exports | Must be >= 1; default: 5 |
| `batch_max_size` | integer | yes | Max metrics per batch export | Must be >= 1; default: 100 |
| `queue_max_size` | integer | yes | Max metrics in memory queue | Must be >= 1; default: 4096 |
| `retry_max_attempts` | integer | yes | Max retry attempts for transient failures | Must be >= 0; 0 = no retry; default: 3 |
| `retry_base_delay_seconds` | float | yes | Initial delay before first retry | Must be >= 0.1; default: 1.0 |
| `retry_max_delay_seconds` | float | yes | Max delay between retries | Must be >= retry_base_delay; default: 30.0 |
| `enabled` | boolean | yes | Whether this publisher instance is active | Default: `true` |

**Relationships**: A project may define multiple `PublisherConfiguration` instances (one per telemetry endpoint). Each configuration produces one `PublisherInstance` at runtime.

### TelemetryMetric

A single measurement value ready for OTLP export.

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `name` | string | yes | Metric name following OTEL semantic conventions (e.g., `specmetrics.function_points.total`) | Must match `[a-z0-9._-]+` pattern |
| `value` | float | yes | The measurement value | Must be a valid non-NaN finite float |
| `unit` | string | yes | Unit of measurement (e.g., `{function_points}`, `{functions}`, `{count}`) | Must be non-empty string |
| `description` | string | yes | Human-readable description of what this metric represents | Must be non-empty string |
| `timestamp` | datetime | yes | When the measurement was taken | UTC timestamp; populated by the measurement engine |
| `attributes` | dict | yes | Resource and metric attributes (see ResourceAttributes) | Must contain at minimum project_name and run_id |
| `evidence_refs` | list[EvidenceRef] | yes | References to source specification elements | At least one reference required |

**Relationships**: A `TelemetryMetric` belongs to a `MeasurementRun`. Multiple metrics are grouped into batches for export.

### EvidenceRef

A reference tracing a metric back to its source specification element.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `spec_document` | string | yes | Path or identifier of the source specification document |
| `spec_section` | string | yes | Section heading or anchor within the document |
| `spec_element_id` | string | no | Specific element identifier (if applicable, e.g., FR-001) |
| `extracted_text` | string | no | The textual fragment that justifies the measurement |

### ResourceAttributes

Metadata describing the source of the telemetry, applied to all metrics from the same pipeline execution.

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `project_name` | string | yes | Name of the project being measured | Must be non-empty |
| `run_id` | string | yes | Unique identifier for this pipeline execution | Must be non-empty, globally unique |
| `specification_version` | string | yes | Version of the specification being measured | Must be non-empty |
| `tool_version` | string | yes | SpecMetrics version that produced the measurement | Must be non-empty |
| `pipeline_execution_timestamp` | datetime | yes | When the pipeline execution started | UTC timestamp |

### PublisherStatus

Runtime state of a single publisher instance.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint_url` | string | yes | The endpoint this status applies to |
| `connection_state` | enum | yes | `connected`, `disconnected`, `error`, `connecting` |
| `last_successful_publish_at` | datetime | no | Timestamp of the last successful publication |
| `total_metrics_published` | integer | yes | Cumulative count of metrics successfully published |
| `consecutive_errors` | integer | yes | Number of consecutive publication failures |
| `queue_depth` | integer | yes | Current number of metrics waiting in the queue |
| `last_error_message` | string | no | Description of the last error encountered |
| `uptime_seconds` | float | yes | Seconds since this publisher instance was initialized |

### PublisherInstance

A runtime instance managing one endpoint's publishing lifecycle.

| Field | Type | Description |
|-------|------|-------------|
| `config` | PublisherConfiguration | The configuration for this instance |
| `status` | PublisherStatus | Current runtime status |
| `metric_queue` | queue | Bounded queue of pending TelemetryMetrics |
| `batch_timer` | timer | Timer for batch interval |
| `otlp_exporter` | exporter | Configured OTLP exporter instance |

**State Transitions**:

```text
[initialized] → [connecting] → [connected] → [publishing] → [connected]
                                    ↓                ↓
                               [disconnected]    [error]
                                    ↓                ↓
                               [reconnecting] → [connecting]
```

## Metric Catalog

The following metrics are published for each measurement run:

| Metric Name | Type | Unit | Description |
|-------------|------|------|-------------|
| `specmetrics.function_points.total` | Gauge | `{function_points}` | Total unadjusted function point count |
| `specmetrics.function_points.adjusted` | Gauge | `{function_points}` | Value-adjusted function point count (if VAF configured) |
| `specmetrics.functions.count` | Gauge | `{functions}` | Total number of identified functions |
| `specmetrics.functions.by_type` | Gauge | `{functions}` | Function count per type (ILF, EIF, EI, EO, EQ) — one metric per type using `type` attribute |
| `specmetrics.functions.by_complexity` | Gauge | `{functions}` | Function count per complexity (Low, Average, High) — one metric per level using `complexity` attribute |
| `specmetrics.functions.excluded` | Gauge | `{functions}` | Number of functions excluded by Rule Packs |

Each metric includes resource attributes (project_name, run_id, etc.) and evidence references.

## Validation Rules

1. **Configuration validation** (FR-013): All `PublisherConfiguration` fields validated at pipeline startup. Invalid configuration produces descriptive error listing all violations — not just the first one found.
2. **Metric invariants**: Every `TelemetryMetric` must have at least one `EvidenceRef`. Metrics without evidence references are rejected before entering the queue.
3. **Queue bounds** (FR-010): When the metric queue exceeds `queue_max_size`, the oldest metrics are dropped first. A warning is logged for each dropped metric including its name and value.
4. **Batch formation**: A batch is exported when either `batch_interval_seconds` has elapsed since the last export, or `batch_max_size` metrics have accumulated — whichever occurs first (FR-006).
5. **Retry limits** (FR-007): After `retry_max_attempts` consecutive failures for a batch, the batch is discarded and a warning is logged. Subsequent metrics continue to be queued normally.
