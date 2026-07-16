# Contract: Configuration File Format

**Version**: 1.0.0 | **Date**: 2026-07-16 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

## Purpose

Defines the user-facing YAML/JSON schema for SpecMetrics configuration files.

## File Paths

Discovery order (lower → higher precedence):
1. `/etc/specmetrics/config.yml` (system-wide)
2. `~/.config/specmetrics/config.yml` (user-level)
3. `<project-root>/specmetrics.yml` or `<project-root>/.specmetrics.yml` (project-level)

Environment variable expansion is supported in path values (e.g., `$HOME`, `$PROJECT_ROOT`).

## Format

### YAML (primary)

```yaml
# specmetrics.yml — Project-level configuration
pipeline:
  stage_timeout: 60    # seconds per pipeline stage
  fail_fast: true

logging:
  level: info          # debug, info, warning, error
  format: console      # console, json

plugins:
  my-adapter:
    api_url: http://localhost:8080
    api_key: ${API_KEY}   # or plain string; sensitive fields masked in dumps

exporters:
  json:
    indent: 4
  csv:
    delimiter: ","
```

### JSON (secondary)

```json
{
  "pipeline": {
    "stage_timeout": 60,
    "fail_fast": true
  },
  "logging": {
    "level": "info",
    "format": "console"
  }
}
```

## Schema Rules

- Core settings live at the top level under well-known keys
- Plugin settings live under `plugins.<plugin_id>`
- Unrecognized keys at the top level produce a warning (not a fatal error)
- Unrecognized keys within recognized sections may produce a warning per section configuration
- Environment variable expansion in string values: `${VAR_NAME}` or `$VAR_NAME`
- Sensitive fields (API keys, tokens) should use `SecretStr` in schema; actual value may be plain string in the file
