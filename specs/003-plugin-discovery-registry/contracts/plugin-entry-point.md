# Contract: Plugin Entry Point

**Version**: 1.0.0 | **Date**: 2026-07-15 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines how a Python package declares itself as a SpecMetrics plugin.

---

## Entry Point Registration

Plugins declare their entry point in `pyproject.toml`:

```toml
[project.entry-points."specmetrics.plugins"]
my-plugin-id = "my_package:register"
```

The entry point name **must** match the plugin's `id` field. It must be unique
across all installed plugins.

---

## Register Function

The target callable must be a module-level function with zero arguments that
returns a `PluginMetadata` instance:

```python
def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-adapter",
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=[EventType.REPOSITORY_LOADED],
        handler_factory=lambda: MyAdapterHandler(),
    )
```

**Rules**:
- Must be a top-level function (not nested, not a class)
- Must accept zero arguments
- Must return a valid `PluginMetadata` instance
- Must not have side effects beyond constructing metadata
- Must be importable without triggering plugin business logic

---

## PluginMetadata Fields

See [data-model.md](../data-model.md#PluginMetadata) for full field definitions.

| Field | Required | Example |
|-------|----------|---------|
| `id` | Yes | `"openspec-adapter"` |
| `api_version` | Yes | `"1.0.0"` |
| `plugin_type` | Yes | `PluginType.ADAPTER` |
| `handled_event_types` | Yes | `[EventType.REPOSITORY_LOADED]` |
| `handler_factory` | When handled_event_types is non-empty | `lambda: MyHandler()` |
| `name` | No | `"OpenSpec Adapter"` |
| `description` | No | `"Adapter for OpenSpec SDD documents"` |
| `author` | No | `"SpecMetrics Team"` |
| `version` | No | `"0.1.0"` |
| `dependencies` | No | `["adapter-plugin", "semantic-provider"]` |

---

## API Version Compatibility

| Platform API | Plugin API | Result |
|-------------|------------|--------|
| `1.0.0` | `1.0.0` | ✅ Compatible |
| `1.0.0` | `1.5.0` | ✅ Compatible (minor/patch within major) |
| `1.0.0` | `2.0.0` | ❌ Rejected (major mismatch) |
| `1.0.0` | `invalid` | ❌ Rejected (unparseable) |

---

## Error Handling

The plugin discovery system handles errors gracefully per FR-005:

| Scenario | Behavior |
|----------|----------|
| `register()` raises an exception | Plugin is SKIPPED, error logged |
| `handler_factory()` raises on first call | Error surfaces at pipeline execution time via StageError |
| Entry point references non-existent module | Plugin is SKIPPED, error logged |
| Metadata has invalid fields | Plugin is REJECTED, validation errors recorded |
| Duplicate entry point name | Last registration wins, warning logged |
| Declared dependency not found | Plugin is REJECTED, missing dependency listed |

---

## Example: Minimal Plugin

```python
# my_plugin/__init__.py
from specmetrics.kernel import EventType, PluginMetadata, PluginType

class MyHandler:
    handled_event_type = EventType.REPOSITORY_LOADED
    handler_id = "my_handler"
    stage_name = "MyStage"
    def handle(self, event):
        return event.context

def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-plugin",
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        handled_event_types=[EventType.REPOSITORY_LOADED],
        handler_factory=lambda: MyHandler(),
    )
```

```toml
# pyproject.toml (in plugin package)
[project.entry-points."specmetrics.plugins"]
my-plugin = "my_plugin:register"
```
