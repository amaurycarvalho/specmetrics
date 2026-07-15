# Research: OpenTelemetry Publisher

**Date**: 2026-07-15
**Feature**: OpenTelemetry Publisher (012)

## Decisions

### OTLP Exporter Package

- **Decision**: Use `opentelemetry-exporter-otlp-proto-grpc` (default) and `opentelemetry-exporter-otlp-proto-http` (alternative transport)
- **Rationale**: Supports both gRPC and HTTP transports as required by FR-002. These are the officially maintained OTLP exporter packages from the OpenTelemetry Python project, ensuring long-term compatibility with evolving OTLP specification versions.
- **Alternatives Considered**:
  - `opentelemetry-exporter-otlp` meta-package — same underlying packages, just a combined dependency
  - Custom OTLP serialization — unnecessary, would duplicate SDK functionality

### Batching Strategy

- **Decision**: Adapt the OpenTelemetry SDK's `BatchSpanProcessor` batching pattern (configurable `max_export_batch_size`, `scheduled_delay_millis`, `max_queue_size`)
- **Rationale**: This is the standard, battle-tested batching pattern in the OpenTelemetry Python ecosystem. It provides all required capabilities: configurable batch interval, maximum batch size, and queue overflow behavior.
- **Alternatives Considered**:
  - Custom batching with `threading.Timer` — more code to maintain, no advantage over proven SDK pattern
  - Third-party batching libraries — unnecessary dependency

### Authentication

- **Decision**: Use OTLP exporter header configuration (`exporter_headers` parameter) to pass API keys as HTTP headers
- **Rationale**: The OpenTelemetry SDK supports custom metadata/headers per exporter. API key authentication (FR-003) is implemented by setting an `Authorization` header via this mechanism. No custom authentication infrastructure needed.
- **Alternatives Considered**:
  - gRPC interceptor for auth — more complex implementation, no benefit for header-based auth
  - TLS client certificates — deferred (explicitly out of scope per spec Assumptions)

### Configuration Model

- **Decision**: Pydantic Settings models loaded from YAML configuration file, matching the project's existing configuration approach
- **Rationale**: The project already uses Pydantic v2 for models and ruamel.yaml for YAML handling. Extending this pattern to publisher configuration ensures consistency with the Export Layer (011) and other pipeline stages.
- **Alternatives Considered**:
  - Environment variables only — limited discoverability and less structured for complex config
  - JSON configuration — YAML is the established project convention

### Plugin Integration

- **Decision**: Implement the publisher as a pipeline stage plugin registered via Python Entry Points (following the existing plugin discovery pattern)
- **Rationale**: The Plugin Discovery Registry (003) and Kernel Pipeline Engine (002) provide the infrastructure for loading pipeline stage plugins. The publisher subscribes to the `MeasurementCompleted` event and produces the `TelemetryPublished` event, completing the pipeline defined in the constitution.
- **Alternatives Considered**:
  - Hard-coded stage in kernel — violates constitution Principle VIII (Plugin-Oriented)
  - CLI-only invocation — would bypass the pipeline event model

### TLS Support

- **Decision**: Use the gRPC channel's built-in SSL/TLS credentials with optional certificate verification
- **Rationale**: The OpenTelemetry OTLP gRPC exporter supports TLS natively via `channel_credentials`. Certificate verification can be toggled via `grpc.ssl_target_name_override` for testing environments.
- **Alternatives Considered**:
  - Custom TLS wrapper — unnecessary given native gRPC support

### Multi-endpoint Support

- **Decision**: Each telemetry endpoint is represented by an independent publisher plugin instance with its own configuration, batching queue, and status tracker
- **Rationale**: Independent instances isolate failures and configuration errors to individual endpoints. If one endpoint is unreachable, it does not affect metrics delivery to other endpoints. This aligns with the parallel-instance pattern commonly used in observability pipelines.
- **Alternatives Considered**:
  - Single publisher with fan-out distribution — higher coupling, single point of failure in the fan-out logic
  - Thread pool with shared queue — more complex, cross-endpoint contamination risk

### Metric Naming Convention

- **Decision**: Follow OpenTelemetry semantic conventions for custom metrics with `specmetrics.` namespace prefix
- **Rationale**: Namespace isolation (`specmetrics.` prefix) prevents naming collisions with application metrics. Following OTEL conventions ensures compatibility with standard dashboards and alerting rules.
- **Alternatives Considered**:
  - Flat naming — higher collision risk, less discoverable
  - Organization-specific prefix — less portable across deployments
