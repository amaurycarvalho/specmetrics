# Contract: Configuration API

**Version**: 1.0.0 | **Date**: 2026-07-16 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

## Purpose

Defines the programmatic interface that platform components and plugins use to read resolved configuration values.

## Interface

### `ConfigProvider` (protocol)

```python
class ConfigProvider(Protocol):
    """Read-only configuration query interface."""

    def get(self, key: str, default: Any = MISSING) -> Any:
        """Get a resolved config value by dot-separated key path.

        Raises KeyError if key not found and no default given.
        """

    def get_model(self, model_type: type[BaseModelT]) -> BaseModelT:
        """Get configuration as a typed Pydantic model instance."""

    @property
    def dump(self) -> ConfigurationDump:
        """Snapshot of all resolved values with provenance metadata."""

    @property
    def warnings(self) -> list[ConfigWarning]:
        """Non-fatal warnings accumulated during loading/validation."""
```

### `ConfigurationSystem` (class)

```python
class ConfigurationSystem:
    """Central configuration system — initialize once at startup."""

    def __init__(self, config_path: Path | None = None) -> None: ...

    def register_plugin_schema(
        self, plugin_id: str, schema: type[BaseModel]
    ) -> None: ...

    def load(self) -> ConfigProvider:
        """Discover sources, merge, validate, and return a ConfigProvider."""
```

## Usage Patterns

### Component consuming config

```python
# At initialization
config = config_system.get_model(MyComponentSettings)

# Direct key access
timeout = config_system.get("pipeline.timeout", default=30)
```

### Plugin declaring config schema

```python
def register() -> PluginMetadata:
    return PluginMetadata(
        id="my-exporter",
        config_schema=MyExporterConfig,  # type[BaseModel]
        ...
    )
```

### CLI config file override

```sh
specmetrics --config ./custom-config.yml measure
specmetrics config dump
```
