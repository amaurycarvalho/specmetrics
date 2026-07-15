# Implementation Plan: OpenTelemetry Publisher

**Branch**: `012-opentelemetry-publisher` | **Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-opentelemetry-publisher/spec.md`

## Summary

Publish functional measurement results from the SpecMetrics pipeline as OpenTelemetry metrics via OTLP protocol, with configurable endpoints, authentication, batching, retry, and multi-endpoint support — enabling continuous visibility into functional size alongside operational telemetry.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: OpenTelemetry SDK + OTLP exporter, structlog, Pydantic v2

**Storage**: N/A — metrics are published to external telemetry endpoints, not stored locally

**Testing**: pytest with mock OTLP receiver for integration tests

**Target Platform**: Linux (CLI tool, local execution)

**Project Type**: CLI tool + MCP Server (plugin implementing a pipeline stage)

**Performance Goals**: Publish metrics within 30s of pipeline completion (SC-001); batch of 100 metrics delivered within configured batch interval + 5s (SC-004)

**Constraints**: Non-blocking to measurement pipeline (FR-008), configurable queue size limit (FR-010), retry with exponential backoff (FR-007)

**Scale/Scope**: Up to 10,000 functions per run; single-user local execution; supports multiple simultaneous endpoint targets (FR-011)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Engaged Principles**: V (Evidence First), VI (Explainability by Design), VII (Canonical Representation), VIII (Plugin-Oriented Architecture), XI (Observability as a Native Capability), XIV (Layer Independence)

**Compliance Verifications**:
- [x] Specification First: The publisher consumes measurement data derived from specifications, respecting the spec-first architecture
- [x] Evidence First: Every published metric includes evidence references tracing back to source specification elements (FR-012)
- [x] Canonical Representation: Publisher consumes exclusively from the Canonical Functional Model — no framework-specific artifacts
- [x] Plugin-Oriented: Publisher is implemented as a plugin registered via Python Entry Points, matching the established plugin architecture
- [x] Rule Externalization: N/A — the publisher transmits measurements; it does not define measurement policies
- [x] Layer Independence: Publisher depends only on the CFM contract and its own configuration; no coupling to extraction, graph, or measurement engine internals
- [x] Open by Default: OTLP is an open standard; publisher exposes documented configuration interface

## Project Structure

### Documentation (this feature)

```text
specs/012-opentelemetry-publisher/
├── spec.md              # Feature specification (done)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── publisher-plugin.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
specmetrics/
├── plugins/
│   └── publisher/
│       ├── __init__.py
│       ├── plugin.py           # Pipeline stage plugin (entry point)
│       ├── config.py           # PublisherConfiguration model
│       ├── metrics.py          # TelemetryMetric → OTLP conversion
│       ├── exporter.py         # OTLP exporter orchestration
│       ├── batcher.py          # Batch accumulation and flushing
│       ├── retry.py            # Retry with exponential backoff
│       └── status.py           # PublisherStatus tracking
├── kernel/
│   └── events.py               # TelemetryPublished event (update)
└── tests/
    ├── unit/
    │   └── publisher/
    │       ├── test_config.py
    │       ├── test_metrics.py
    │       ├── test_batcher.py
    │       └── test_retry.py
    └── integration/
        ├── test_publisher_e2e.py
        └── mocks/
            └── mock_otlp_receiver.py
```

**Structure Decision**: Single-project layout with publisher as a plugin under `plugins/publisher/`, mirroring the existing plugin directory convention (001-mvp-release-outline established the plugin architecture pattern). Tests follow the existing unit/integration split under `tests/`.

## Complexity Tracking

No constitution violations to justify.

## Phase 0: Research

The following decisions were researched and resolved based on the project's established technology stack and industry best practices:

| Topic | Decision | Rationale | Alternatives Considered |
|-------|----------|-----------|------------------------|
| OTLP Exporter Package | opentelemetry-exporter-otlp-proto-grpc + opentelemetry-exporter-otlp-proto-http | Supports both gRPC and HTTP transports as required by FR-002. Most widely adopted OTLP exporter packages in the Python ecosystem. | opentelemetry-exporter-otlp (combined) — same, just a meta-package |
| Batching Strategy | OpenTelemetry SDK BatchSpanProcessor pattern | Proven pattern used across the OpenTelemetry ecosystem. Configurable max export batch size, scheduled delay, and queue max size. | Custom batching — unnecessary given SDK built-in support |
| Authentication | OTLP headers via exporter headers config | OpenTelemetry SDK supports custom headers per exporter. API key auth is implemented by adding an `Authorization` header. | gRPC interceptor — more complex, no benefit for this use case |
| Configuration Model | Pydantic Settings with YAML file | Matches the project's existing configuration approach (Pydantic Settings + ruamel.yaml). Extends the pattern used by the Export Layer (011). | Environment variables only — less flexible for complex publisher config |
| Plugin Integration | Python Entry Point (publisher plugin) | Matches the existing plugin discovery pattern used by other pipeline stages. Plugin implements the pipeline stage contract and registers for `MeasurementCompleted` event. | Hard-coded stage — violates Plugin-Oriented principle |
| TLS Support | Built-in gRPC SSL channel credentials | OpenTelemetry exporter gRPC channel supports TLS natively. Certificate verification toggle is a standard configuration option. | Custom TLS wrapper — unnecessary complexity |
| Multi-endpoint | Multiple publisher plugin instances | Each endpoint gets its own publisher plugin instance with independent configuration, batching, and status tracking. | Single publisher with fan-out — higher risk of cross-endpoint contamination |
| Metric Naming | OpenTelemetry semantic conventions for custom metrics | Follows established naming patterns: `specmetrics.function_points.total`, `specmetrics.functions.count`, `specmetrics.functions.by_type`. All names prefixed with `specmetrics.` for namespace isolation. | Custom naming scheme — less interoperable with existing observability tooling |

## Phase 1: Design

### Data Model

See [data-model.md](data-model.md) for complete entity definitions, fields, validation rules, and relationships.

### Contracts

See [contracts/publisher-plugin.md](contracts/publisher-plugin.md) for the publisher plugin interface contract and event integration points.

### Quickstart

See [quickstart.md](quickstart.md) for validation scenarios, setup instructions, and expected outcomes.
