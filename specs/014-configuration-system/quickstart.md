# Quickstart: Configuration System

## Prerequisites

- Python >=3.12 with `uv` or `pipx`
- SpecMetrics installed in development mode: `uv pip install -e .`
- `pydantic-settings` added to dependencies

## Setup

```bash
# Create a test project config
cat > specmetrics.yml << 'EOF'
pipeline:
  stage_timeout: 60
  fail_fast: true
logging:
  level: info
  format: console
plugins:
  sample-adapter:
    api_url: http://localhost:8080
    api_key: test-key-123
EOF
```

## Validation Scenarios

### Scenario 1: Centralized loading (FR-001)

```bash
specmetrics --config ./specmetrics.yml measure
```

**Expected**: Platform uses settings from `specmetrics.yml`. Component behavior matches configured values (e.g., info-level logging, 60s timeout).

### Scenario 2: Environment override (FR-001, hierarchy)

```bash
SPECMETRICS_LOGGING_LEVEL=debug specmetrics --config ./specmetrics.yml measure
```

**Expected**: Logging level is `debug` (overrides file's `info`), other settings from file.

### Scenario 3: CLI override (FR-001, hierarchy)

```bash
specmetrics --config ./specmetrics.yml --pipeline-stage-timeout 120 measure
```

**Expected**: Stage timeout is 120s (overrides file's 60s and env var).

### Scenario 4: Missing required field (FR-002)

Create invalid config:

```yaml
# invalid.yml
pipeline:
  stage_timeout: not-a-number
```

```bash
specmetrics --config ./invalid.yml measure
```

**Expected**: Descriptive error — field path, invalid value (`not-a-number`), expected type (`int`). Platform does not start.

### Scenario 5: Unrecognized key warning (FR-008)

```yaml
# with-unknown.yml
pipeline:
  stage_timeout: 60
unknown_setting: true
```

```bash
specmetrics --config ./with-unknown.yml measure
```

**Expected**: Platform starts with defaults for unknown key. Warning printed about `unknown_setting`.

### Scenario 6: Config dump (FR-006)

```bash
specmetrics config dump
```

**Expected**: Table or JSON output showing each setting with its resolved value, source of origin, and whether it is a default.

### Scenario 7: Plugin schema registration (FR-005)

```bash
# Register a test plugin with a config schema, then:
specmetrics --config ./specmetrics.yml measure
```

**Expected**: Plugin receives its validated config model at initialization under `plugins.sample-adapter`.

### Scenario 8: Sensitive value masking (FR-007)

```bash
specmetrics config dump
```

**Expected**: `api_key` value shown as `**********` in dump output and logs.

### Scenario 9: Malformed YAML (Edge cases)

```bash
echo "invalid: [unclosed" > malformed.yml
specmetrics --config ./malformed.yml measure
```

**Expected**: Parse error with file path, line number, and syntax description. Platform aborts.

### Scenario 10: Circular reference (FR-010)

```yaml
# circular.yml
a: ${b}
b: ${a}
```

**Expected**: Error reporting circular reference between `a` and `b`.
