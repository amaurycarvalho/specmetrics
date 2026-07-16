# Data Model: Plugin Discovery & Registry

**Date**: 2026-07-15 | **Spec**: [spec.md](spec.md)

---

## Entity-Relationship Overview

```
PluginMetadata (declared by plugin)
    │
    ▼
PluginDescriptor (internal — wraps metadata + entry point + validation)
    │
    ├──► PluginRegistry (stores all descriptors)
    │
    └──► HandlerRegistry (F01) — after install_handlers()
```

---

## PluginMetadata

Declared by each plugin via its factory function. Immutable after creation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique plugin identifier (e.g., `"openspec-adapter"`) |
| `api_version` | `str` | Yes | SemVer string declaring API compatibility |
| `plugin_type` | `PluginType` | Yes | Category of the plugin |
| `handled_event_types` | `list[EventType]` | Yes | Event types this plugin handles |
| `handler_factory` | `Callable[[], EventHandler]` | Yes | Factory that returns a handler instance |
| `name` | `str` | No | Human-readable name (defaults to `id`) |
| `description` | `str` | No | Human-readable description |
| `author` | `str` | No | Plugin author |
| `version` | `str` | No | Plugin's own version string |
| `dependencies` | `list[str]` | No | Plugin IDs this plugin depends on |

**Validation Rules**:
- `id` must be non-empty, alphanumeric with hyphens
- `api_version` must be a valid SemVer 2.0.0 string
- `handled_event_types` may be empty (non-handler plugins like exporters)
- `handler_factory` is required when `handled_event_types` is non-empty
- `dependencies` must reference plugin IDs that exist in the discovered set; missing dependencies cause REJECTED status

---

## PluginType

Enum categorizing plugins by architectural role.

| Value | Description |
|-------|-------------|
| `ADAPTER` | SDD framework adapter |
| `SEMANTIC` | Semantic extraction provider |
| `MEASUREMENT` | Measurement engine |
| `EXPORTER` | Export format plugin |
| `PUBLISHER` | Telemetry publisher |
| `UNSPECIFIED` | Catch-all for plugins that don't fit above categories |

---

## PluginDescriptor

Internal representation wrapping a discovered and validated plugin.

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | `PluginMetadata` | The plugin's declared metadata |
| `entry_point_name` | `str` | Name of the entry point that discovered this plugin |
| `status` | `PluginStatus` | Current validation/registration status |
| `validation_errors` | `list[str]` | Errors if status is REJECTED |

---

## PluginStatus

| Value | Description |
|-------|-------------|
| `PENDING` | Discovered but not yet validated |
| `REGISTERED` | Validated and registered successfully |
| `REJECTED` | Failed validation; not registered |
| `SKIPPED` | Loading error occurred; not registered |

---

## PluginRegistry

Central store for all discovered plugins.

| Field | Type | Description |
|-------|------|-------------|
| `_plugins` | `dict[str, PluginDescriptor]` | All discovered plugins by ID |
| `_by_event_type` | `dict[EventType, list[PluginDescriptor]]` | Index for event type lookup |
| `_by_plugin_type` | `dict[PluginType, list[PluginDescriptor]]` | Index for plugin type lookup |

**Methods**:
- `register(descriptor)` — Add a validated plugin descriptor
- `get_handler(event_type)` → `EventHandler | None` — Find handler for event type (US3)
- `get_handlers(event_type)` → `list[EventHandler]` — All handlers for event type
- `list_plugins()` → `list[PluginDescriptor]` — All registered plugins
- `install_handlers(handler_registry)` — Populate F01 HandlerRegistry
- `get_by_type(plugin_type)` → `list[PluginDescriptor]` — Filter by type

---

## State Transitions

```
 DISCOVERED ──► VALIDATED ──► REGISTERED
                    │               │
                    ▼               ▼
                REJECTED        (active in registry)
                    
 SKIPPED (import/load error — no validation attempted)
```

**Notes**:
- `DISCOVERED` is ephemeral — happens during `scan()`
- `VALIDATED` → `REGISTERED` transition happens atomically in `register()`
- `REJECTED` descriptors are preserved in a separate error log for diagnostics
- `SKIPPED` plugins are logged but not stored — they have no metadata to record
