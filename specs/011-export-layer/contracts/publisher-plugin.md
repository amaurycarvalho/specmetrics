# Publisher Plugin Interface Contract

**Phase 1 output for `/speckit.plan` command**

---

## Purpose

Defines the contract that custom publisher plugins must implement to publish
measurement data to external telemetry or observability systems.

---

## Plugin Discovery

Publishers are discovered via Python entry points under the `specmetrics.publishers`
group.

```python
# pyproject.toml (example for a custom publisher)
[project.entry-points."specmetrics.publishers"]
custom = "myplugin.custom_publisher:CustomPublisher"
```

---

## Interface: `PublisherPlugin`

### Methods

#### `publisher_id() -> str`

Returns the unique identifier for this publisher (e.g., `"otel"`, `"custom"`).
Must match the entry point name.

#### `name() -> str`

Returns a human-readable name.

#### `publish(measurements: list[Measurement], metadata: ExportMetadata, config: PublisherConfig) -> PublishResult`

Publishes measurements to the external system.

| Parameter | Type | Description |
|-----------|------|-------------|
| `measurements` | `list[Measurement]` | Canonical measurement records |
| `metadata` | `ExportMetadata` | Run metadata |
| `config` | `PublisherConfig` | Publisher-specific configuration |

**Return value**: `PublishResult` with fields:
- `success: bool` — Whether publication succeeded
- `message: str` — Status message (for logging)
- `metrics_count: int` — Number of metrics published

**Behavior requirements**:
- Must not raise exceptions for network failures. Return `PublishResult(success=False, message=...)` instead.
- Must be idempotent for the same `run_id` (publishing the same run twice should not create duplicate metrics).
- Must complete within 30 seconds or return a timeout result.

---

## Configuration Schema

```python
class PublisherConfig(BaseModel):
    endpoint_url: str
    auth_credentials: dict | None = None
    publishing_interval: int = 30
```

---

## Built-in Implementation

| Publisher | Plugin ID | Entry Point |
|-----------|-----------|-------------|
| OpenTelemetry | `otel` | `specmetrics.plugins.publisher.otel_publisher:OTelPublisher` |
