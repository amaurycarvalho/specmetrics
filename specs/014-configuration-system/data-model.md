# Data Model: Configuration System

## Entities

### ConfigurationSchema

The declarative definition of valid configuration settings for a component or plugin. Defined as Pydantic models.

```python
class ConfigurationSchema(BaseModel):
    """Base schema — core platform settings."""
    # Defined per component; example:
    pipeline: PipelineSettings
    logging: LoggingSettings
    plugins: dict[str, PluginConfig]  # namespace per plugin ID
```

**Fields (Pydantic model semantics)**:
- Field name corresponds to config key path
- Type annotation defines expected type and validation
- `Field(default=...)` provides default values
- `Field(..., description=...)` documents the setting
- `Field(..., json_schema_extra={"sensitive": True})` marks sensitive fields

**Validation rules** (from Pydantic v2):
- Type coercion with strict mode option
- `field_validator` for custom validation logic
- `model_validator` for cross-field validation
- `Field(ge=..., le=...)` for numeric range constraints
- `Field(min_length=..., max_length=...)` for string constraints
- `SecretStr` type for sensitive values (auto-masked in repr/dump)

### ConfigurationSource

A single source of configuration values with known precedence. Adapter pattern.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable source identifier (e.g., "project config", "SPECMETRICS_DEBUG") |
| `precedence` | `SourceLevel` | Enum: `SYSTEM`, `USER`, `PROJECT`, `ENVIRONMENT`, `CLI` |
| `load()` | method | Returns `dict[str, Any]` of raw key-value pairs |

**Concrete implementations**:
- `FileSource(path, format)` — reads YAML/JSON file
- `EnvironmentSource(prefix)` — reads env vars matching prefix (e.g., `SPECMETRICS_`)
- `CliSource(args)` — reads parsed CLI arguments

### SourceLevel (Enum)

```text
SYSTEM (0) < USER (1) < PROJECT (2) < ENVIRONMENT (3) < CLI (4)
```

Higher ordinal = higher precedence. Each level fully overrides same-key values from lower levels.

### ResolvedConfiguration

The final merged and validated configuration after processing all sources.

| Field | Type | Description |
|-------|------|-------------|
| `values` | `dict[str, Any]` | Effective resolved values (Pydantic model instance) |
| `provenance` | `dict[str, SourceProvenance]` | Per-key tracking of which source provided the value |
| `warnings` | `list[ConfigWarning]` | Non-fatal warnings (unrecognized keys, deprecated settings) |
| `schema` | `ConfigurationSchema` | The schema that validated this config |

**State transitions**:

```text
[Raw Sources] → merge() → [Unvalidated Dict] → validate(schema) → [ResolvedConfiguration]
                                                     ↓ error
                                            [ValidationError]
```

### SourceProvenance

Tracks where each configuration value originated.

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Config key path (e.g., `pipeline.timeout`) |
| `source` | `str` | Source name (e.g., `project config`, `SPECMETRICS_DEBUG`) |
| `level` | `SourceLevel` | Precedence level |
| `is_default` | `bool` | True if no explicit source provided the value |

### ConfigurationDump

Snapshot for introspection/export.

| Field | Type | Description |
|-------|------|-------------|
| `entries` | `list[DumpEntry]` | All resolved settings with metadata |
| `warnings` | `list[ConfigWarning]` | Warnings (unrecognized keys) |
| `sources_loaded` | `list[str]` | Which sources contributed values |

### DumpEntry

| Field | Type | Description |
|-------|------|-------------|
| `key` | `str` | Config key path |
| `value` | `Any` | Resolved value (masked if sensitive) |
| `source` | `str` | Source of origin |
| `level` | `str` | Precedence level name |
| `is_default` | `bool` | Whether value came from schema default |
| `is_sensitive` | `bool` | Whether field is marked sensitive |

### ConfigWarning

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | Human-readable warning |
| `key` | `str | None` | Config key involved, if applicable |
| `source` | `str | None` | Source that triggered the warning |

### PluginConfigDeclaration

Plugin schema registration interface.

```python
@dataclass
class PluginConfigDeclaration:
    plugin_id: str
    schema_model: type[BaseModel]
```

**Registration flow**:
1. Plugin's `register()` returns `PluginMetadata` with optional `config_schema` field
2. Config system collects all declarations during plugin discovery
3. Each plugin config is allocated under `plugins.{plugin_id}` namespace
4. Merged into the full `ConfigurationSchema` before validation

## Relationships

```text
ConfigurationSystem
  ├── loads from multiple ConfigurationSources
  ├── validates against ConfigurationSchema
  │     ├── CoreSchema (platform settings)
  │     └── PluginConfigDeclaration × N (per plugin)
  ├── produces ResolvedConfiguration
  │     └── tracks provenance via SourceProvenance × N
  └── exports ConfigurationDump
        └── contains DumpEntry × N
```

## Validation Rules (from spec FR-002, FR-010)

| Rule | Enforcement | Error Behavior |
|------|-------------|----------------|
| Required field missing | Pydantic `Field(..., required=True)` | `ConfigValidationError` with field path + expected type |
| Type mismatch | Pydantic type validation | `ConfigValidationError` with field path + invalid value + expected type |
| Out-of-range value | Pydantic `Field(ge=..., le=...)` | `ConfigValidationError` with constraint details |
| Unrecognized key | `model_extra = "forbid"` on core schemas; `model_extra = "ignore"` for plugin namespaces | Warning logged, key ignored |
| Circular reference | Graph cycle detection in resolver | `ConfigCircularRefError` with involved key paths |
| YAML/JSON parse error | `ruamel.yaml` parser | `ConfigParseError` with file path + line number + syntax description |
