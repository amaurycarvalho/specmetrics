# Research Report: Plugin Discovery & Registry

**Date**: 2026-07-15 | **Feature**: [spec.md](spec.md)

---

## 1. Entry Point Metadata Schema

**Decision**: Plugin entry points use a factory function pattern with structured
metadata returned via a `PluginMetadata` dataclass.

**Rationale**: Python Entry Points support both string values and callable
references. A factory function pattern (`module:function`) is the most flexible
approach — it allows plugins to construct metadata dynamically and avoids
encoding structured data in setup.py/pyproject.toml strings, which would be
error-prone and hard to validate.

**How it works**:
- Plugin declares entry point in `pyproject.toml`:
  ```toml
  [project.entry-points."specmetrics.plugins"]
  my-adapter = "my_plugin:register"
  ```
- The `register` function is a top-level callable that takes no arguments and
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

**Alternatives considered**:
- **Entry point extras/attributes**: `importlib.metadata` supports accessing
  entry point attributes, but this is a Python 3.13+ feature and requires
  declaring metadata in setup.py strings. Less type-safe.
- **Package-level metadata**: Reading metadata from module-level variables
  (`__plugin_metadata__`). Requires importing the package, which could have
  side effects. Not isolated enough.

---

## 2. Platform API Version Source

**Decision**: The platform API version is read from
`importlib.metadata.version("specmetrics")` at startup.

**Rationale**: SpecMetrics is installed as a Python package. Its version string
(defined in `pyproject.toml`) serves as the canonical API version. Using
`importlib.metadata.version()` avoids hardcoding and stays consistent with the
distribution.

**SemVer comparison rules**:
- Major version mismatch (`1.x.x` vs `2.x.x`) → plugin rejected
- Minor/patch within same major (`1.0.0` vs `1.5.0`) → accepted
- Pre-release tags are ignored for comparison
- Unparseable version strings → plugin rejected with clear error

**Alternatives considered**:
- **Module `__version__` attribute**: Less reliable — not all packages define
  it, and it can become stale.
- **Hardcoded constant in code**: Requires manual updates on every release.
  Error-prone.

---

## 3. Integration with F01 HandlerRegistry

**Decision**: The PluginRegistry manages plugin metadata and lifecycle; it
populates the F01 HandlerRegistry during a `register_handlers()` call.

**Rationale**: The F01 HandlerRegistry (`specmetrics/kernel/handler_registry.py`)
already provides the `register()` and `resolve()` methods needed by the
Pipeline Engine. Instead of replacing it, the PluginRegistry acts as a
higher-level component that:
1. Discovers plugins via entry points
2. Validates their metadata
3. Instantiates handler factories
4. Registers the resulting handlers into the F01 HandlerRegistry

**Flow**:
```
PluginDiscovery.scan()
  ↓
PluginRegistry.register(plugin_metadata)  # stores metadata
  ↓
PluginRegistry.install_handlers(handler_registry)  # populates F01's registry
```

**Alternatives considered**:
- **Replace F01 HandlerRegistry**: Would break the existing working F01
  implementation. Unnecessary coupling.
- **Registry inherits HandlerRegistry**: Would mix concerns — metadata
  management vs. handler resolution. Better to compose.

---

## 4. Plugin Type Taxonomy

**Decision**: Plugin types map to the architectural layers and are defined as a
`PluginType` enum.

| Type | Entry Point Subgroup | Purpose |
|------|---------------------|---------|
| ADAPTER | `adapter` | SDD framework adapters |
| SEMANTIC | `semantic` | Semantic extraction providers |
| MEASUREMENT | `measurement` | Measurement engines (FPA, etc.) |
| EXPORTER | `exporter` | Export format plugins |
| PUBLISHER | `publisher` | Telemetry publishers |

**Rationale**: The spec mentions `specmetrics.plugins.{type}` convention. Each
plugin type maps to a specific pipeline stage and has distinct interface
requirements. The subgroup convention allows filtering and clear organization.

---

## 5. Error Isolation Strategy

**Decision**: Each plugin is loaded in an isolated try/except block. A single
plugin failure never blocks other plugins.

**Pattern**:
```python
for entry_point in discovered:
    try:
        metadata = entry_point.load()()
        validate(metadata)
        registry.register(metadata)
    except Exception as exc:
        logger.warning("plugin_skipped", plugin=entry_point.name, error=str(exc))
```

This covers:
- Import errors (broken dependencies, missing modules)
- Validation errors (incompatible version, missing fields)
- Runtime errors in factory functions

**Trade-offs acknowledged**:
- No sandboxing or subprocess isolation — a plugin could theoretically consume
  memory or hang. Acceptable for MVP; sandboxing is a post-MVP concern.
- Plugin A's import may affect Plugin B's import if they share transitive
  dependencies with version conflicts. Python's import system handles this at
  the module level — not fully isolated but sufficient for MVP.
