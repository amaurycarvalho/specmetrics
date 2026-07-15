# Quickstart: OpenTelemetry Publisher

**Date**: 2026-07-15
**Feature**: OpenTelemetry Publisher (012)

## Prerequisites

- Python 3.13+
- SpecMetrics CLI installed and configured
- Access to an OTLP-compatible telemetry endpoint (or use a local mock)
- Feature specs: 002 Kernel Pipeline Engine, 007 Canonical Functional Model, 008 Measurement Engine, 011 Export Layer

## Setup

### 1. Install OpenTelemetry dependencies

```bash
# Core SDK
uv add opentelemetry-sdk

# OTLP exporters (gRPC default, HTTP optional)
uv add opentelemetry-exporter-otlp-proto-grpc
# uv add opentelemetry-exporter-otlp-proto-http  # uncomment for HTTP transport
```

### 2. Configure the publisher

Add to your project's YAML configuration (e.g., `specmetrics.yml`):

```yaml
publisher:
  endpoints:
    - endpoint_url: "http://localhost:4318"
      protocol: "grpc"
      tls_enabled: false
      batch_interval_seconds: 5
      batch_max_size: 100
      enabled: true
```

### 3. Run the measurement pipeline

```bash
specmetrics measure --spec ./path/to/spec
```

## Validation Scenarios

### Scenario 1: Basic metric publication

**Goal**: Verify that metrics appear at the telemetry endpoint after a pipeline run.

1. Start a mock OTLP receiver (see [Mock Receiver](#mock-receiver) below)
2. Configure the publisher to point to the mock endpoint
3. Run `specmetrics measure`
4. **Expected**: Mock receiver logs show metric names `specmetrics.function_points.total`, `specmetrics.functions.count`, etc.
5. Verify each metric includes `project_name` and `run_id` resource attributes

### Scenario 2: Configuration validation

**Goal**: Verify invalid configuration is caught at startup.

1. Set `endpoint_url` to an empty string in configuration
2. Run `specmetrics measure`
3. **Expected**: Pipeline fails with descriptive error: "Publisher configuration validation failed: endpoint_url must be a valid URL"

### Scenario 3: Endpoint unavailability

**Goal**: Verify pipeline completes even when telemetry endpoint is down.

1. Configure publisher with an unreachable endpoint (e.g., `http://localhost:19999`)
2. Run `specmetrics measure`
3. **Expected**: Pipeline completes successfully. Logs contain a warning about unreachable endpoint. Metrics are queued for retry.

### Scenario 4: Batch delivery

**Goal**: Verify metrics are delivered in batches.

1. Configure `batch_interval_seconds: 2` and `batch_max_size: 50`
2. Run measurement on a spec with at least 60 functions
3. **Expected**: Metrics are delivered in 2+ batches. Each batch contains no more than 50 metrics.

### Scenario 5: Publisher status reporting

**Goal**: Verify status command works.

1. Run `specmetrics publisher status`
2. **Expected**: Shows configured endpoints, connection state, last publish timestamp, metrics published count, and queue depth

## Mock Receiver

For local testing without a real OTLP backend, start a minimal OTLP gRPC receiver:

```bash
# Using a simple Python script
python -c "
from grpc_health.v1 import health
from concurrent import futures
import grpc

# See specs/012-opentelemetry-publisher/tests/mocks/mock_otlp_receiver.py for full implementation
print('Mock OTLP receiver placeholder — implement per contract/publisher-plugin.md')
"
```

See the full mock implementation at `tests/integration/mocks/mock_otlp_receiver.py`.

## Verification Checklist

- [ ] Metrics appear at the configured OTLP endpoint
- [ ] Metrics include resource attributes (project_name, run_id, etc.)
- [ ] Metrics include evidence references
- [ ] Configuration errors are reported descriptively
- [ ] Pipeline completes when endpoint is unreachable
- [ ] Metrics are delivered in batches per configuration
- [ ] Status command reports active publisher state
- [ ] Multiple endpoints receive metrics independently
- [ ] Expired/queued metrics are dropped oldest-first when queue is full
