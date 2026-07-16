# Research: Configuration System

## Technology: pydantic-settings

- **Decision**: Use `pydantic-settings` as the configuration loading foundation
- **Rationale**: Already established as the project's configuration approach (per spec assumptions, used in specs 011, 013). Provides built-in support for environment variables, CLI args via model creation, and YAML loading via custom settings sources. Integrates natively with Pydantic v2 validation.
- **Alternatives Considered**:
  - Manual YAML parsing + os.environ — no validation, no type coercion, no hierarchy merging
  - Dynaconf — heavier dependency, adds features (hot-reload, redis) not needed for v1
  - Python `configparser` — INI format only, no nested structures or type validation

## Configuration Format: YAML + JSON

- **Decision**: YAML primary, JSON secondary
- **Rationale**: YAML is more human-readable for configuration files; JSON provides compatibility with tooling that generates JSON. `ruamel.yaml` is already a project dependency (from constitution).
- **Alternatives Considered**:
  - TOML — not currently a dependency; `pyproject.toml` uses it but not for application config
  - YAML only — sufficient for v1; JSON support is low-cost via `ruamel.yaml` which can parse both

## Discovery Paths: XDG Base Directory

- **Decision**: Follow XDG Base Directory Specification
  - System: `/etc/specmetrics/config.{yml,yaml,json}`
  - User: `~/.config/specmetrics/config.{yml,yaml,json}`
  - Project: `<project-root>/specmetrics.{yml,yaml,json}` or `<project-root>/.specmetrics.{yml,yaml,json}`
- **Rationale**: Standard Unix convention; already specified in spec assumptions. `$XDG_CONFIG_HOME` and `$XDG_CONFIG_DIRS` respected when set.
- **Alternatives Considered**:
  - Single project-level file only — loses system/user-level defaults
  - All in environment variables — not discoverable, verbose for nested config

## Precedence Hierarchy

- **Decision**: CLI > Environment > Project > User > System
- **Rationale**: CLI is most explicit (per-invocation), environment for session-level overrides, project/user/system files for persistent config at decreasing specificity.
- **Pattern**: Deep merge with higher-precedence sources overriding individual keys, not replacing entire sections.

## Plugin Configuration Registration

- **Decision**: Plugins declare a Pydantic model via their `register()` function (existing registration pattern from spec 003). The config system collects these during plugin discovery and allocates a `plugins.<id>` namespace.
- **Rationale**: Reuses existing `register()` → `PluginMetadata` pattern. No new registration mechanism needed. Plugin config schemas are Pydantic models, consistent with core config schemas.
- **Pattern from spec 011 (exporter contracts)**: `config_schema()` classmethod returning `type[BaseModel]`.

## Sensitive Value Marking

- **Decision**: Pydantic `SecretStr` / `SecretBytes` for sensitive fields
- **Rationale**: Pydantic `SecretStr` already provides masking in `__repr__`, `__str__`, and `.model_dump()`. Matches the "mark fields as sensitive" requirement without custom masking logic.
- **Masking behavior**: Logs and dumps show `'**********'` instead of actual value. CLI should accept both plain strings and `SecretStr` transparently.

## CLI Integration

- **Decision**: `specmetrics config dump` subcommand for introspection; `--config` global option for specifying config file path
- **Rationale**: Matches existing CLI patterns (see `cli/app.py` which uses `app.add_typer()` for subcommand groups). Introspection command provides source-of-origin display.
