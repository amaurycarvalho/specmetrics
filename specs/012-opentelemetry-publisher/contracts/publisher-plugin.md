# Publisher Plugin Contract

**Date**: 2026-07-15
**Feature**: OpenTelemetry Publisher (012)
**Applies to**: `plugins/publisher/*`

## Plugin Interface

The publisher plugin implements the standard pipeline stage plugin contract used by all SpecMetrics plugins. It registers itself via Python Entry Points under the `specmetrics.plugins.publisher` group.

### Entry Point Registration

```python
# setup.py or pyproject.toml entry
entry_points = {
    "specmetrics.plugins.publisher": [
        "otlp = specmetrics.plugins.publisher.plugin:OTLPPublisherPlugin",
    ],
}
```

### PublisherPlugin Protocol

```python
class PublisherPlugin:
    """Interface that every publisher plugin must implement."""

    def __init__(self, config: dict):
        """Initialize publisher with configuration dictionary.
        Raises ConfigurationError if config is invalid.
        """

    def start(self):
        """Start the publisher, establish connection, begin batching.
        Must be non-blocking — returns immediately after initialization.
        Raises ConnectionError if initial connection cannot be established.
        """

    def publish(self, metrics: list[TelemetryMetric]) -> None:
        """Enqueue metrics for publishing. Returns immediately.
        Must never block the caller.
        Raises QueueFullError if queue is at capacity and metrics cannot be accepted.
        """

    def stop(self) -> None:
        """Gracefully stop the publisher.
        Flushes remaining metrics, closes connections, cancels timers.
        Blocks until shutdown is complete (max timeout_seconds).
        """

    def get_status(self) -> PublisherStatus:
        """Return current publisher status snapshot.
        Must be safe to call from any thread at any time.
        """

    @property
    def endpoint(self) -> str:
        """Return the endpoint URL this publisher targets."""
```

## Event Integration

The publisher subscribes to the `MeasurementCompleted` event from the Kernel Pipeline Engine.

### Consumed Event

```
MeasurementCompleted
  ├── run_id: str
  ├── timestamp: datetime
  ├── cfm: CanonicalFunctionalModel
  └── rule_pack_applied: bool
```

### Produced Event

```
TelemetryPublished
  ├── run_id: str
  ├── publisher_endpoint: str
  ├── metrics_published: int
  ├── status: str (success/partial/failed)
  └── timestamp: datetime
```

## Configuration Schema

Publisher configuration is loaded from the project's YAML configuration file under a `publisher` key:

```yaml
publisher:
  endpoints:
    - endpoint_url: "https://otlp.example.com:4318"
      protocol: "grpc"
      api_key: "${OTLP_API_KEY}"   # env var reference
      tls_enabled: true
      batch_interval_seconds: 5
      batch_max_size: 100
      enabled: true

    - endpoint_url: "http://localhost:4318"
      protocol: "http"
      tls_enabled: false
      batch_interval_seconds: 10
      batch_max_size: 50
      enabled: false
```

## Pipeline Placement

The publisher stage executes after the Export Layer stage in the pipeline:

```text
Measurement Engine → ExportCompleted → Publisher → TelemetryPublished
```

## Error Handling Contract

| Scenario | Behavior |
|----------|----------|
| Endpoint unreachable at start | Log warning, queue metrics, retry with backoff |
| Endpoint fails mid-batch | Retry entire batch; after max retries, discard batch with warning |
| Queue full | Drop oldest metrics, log warning with metric name/value |
| Invalid configuration | Report all validation errors at pipeline startup, fail fast |
| Multiple endpoints | Each endpoint instance operates independently — one failure does not affect others |
