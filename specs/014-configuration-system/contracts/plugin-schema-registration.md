# Contract: Plugin Configuration Schema Registration

**Version**: 1.0.0 | **Date**: 2026-07-16 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

## Purpose

Defines how plugins declare their configuration schema for automatic validation and namespace allocation.

## Declaration

Plugins declare their config schema during registration via the `config_schema` field on `PluginMetadata`:

```python
from pydantic import BaseModel, Field

class MyAdapterConfig(BaseModel):
    api_url: str = Field(..., description="Base URL for the adapter API")
    api_key: str = Field(..., description="API key", json_schema_extra={"sensitive": True})
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")


def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-adapter",
        version="0.1.0",
        api_version="1.0.0",
        plugin_type=PluginType.ADAPTER,
        config_schema=MyAdapterConfig,  # <-- NEW field
        handler_factory=lambda: MyAdapterHandler(),
    )
```

## Namespace Allocation

- Plugin config is allocated under `plugins.{plugin_id}` in the merged configuration
- Example: `plugins.my-adapter.api_url`, `plugins.my-adapter.timeout`
- Plugin namespaces are isolated — no key collision with core settings
- A plugin without a `config_schema` receives no config namespace

## Validation Behavior

| Scenario | Result |
|----------|--------|
| Valid plugin config provided | Plugin receives validated model at initialization |
| No plugin config provided | Plugin receives default values from schema |
| Required field missing in plugin config | Validation error identifying plugin ID + missing field |
| Type mismatch in plugin config | Validation error identifying plugin ID + field + expected type |

## Plugin Config Access

Plugins receive their validated config model at initialization:

```python
class MyAdapterHandler:
    def __init__(self, config: MyAdapterConfig) -> None:
        self.config = config
```
