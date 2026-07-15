# Quickstart: Export Layer Validation

**Phase 1 output for `/speckit.plan` command**

---

## Prerequisites

- SpecMetrics development environment (Python 3.13, uv/pipx)
- Measurement pipeline with test data (see existing tests in `tests/`)
- Plugin registry with built-in exporters registered

---

## Setup

```bash
# Install dependencies
uv sync

# Verify plugin registry detects exporters
python -m specmetrics plugins list
# Expected: exporters: json, csv, xml; publishers: otel
```

---

## Validation Scenarios

### 1. Basic Export (FR-001, FR-010)

```bash
# Run measurement pipeline with export to all formats
python -m specmetrics measure --export json,csv,xml --output-dir /tmp/export-test

# Verify outputs exist
ls /tmp/export-test/
# Expected: measurements.json, measurements.csv, measurements.xml
```

**Expected outcome**: Three files produced each containing measurement data with metadata
(run ID, timestamp, version). Each file's content is valid for its format.

---

### 2. Evidence Traceability (FR-002)

```bash
# Verify evidence references exist in JSON output
python -c "
import json
data = json.load(open('/tmp/export-test/measurements.json'))
assert len(data['measurements']) > 0
for m in data['measurements']:
    assert len(m['evidence']) > 0, f'Missing evidence for {m[\"function_id\"]}'
print('OK: All measurements have evidence references')
"
```

**Expected outcome**: All exported measurements include at least one evidence reference.

---

### 3. Empty Results Handling

```bash
# Run with a spec that produces zero functions
python -m specmetrics measure --spec tests/fixtures/empty-spec.md --export json

# Verify empty valid output
python -c "
import json
data = json.load(open('/tmp/export-test/measurements.json'))
assert data['measurements'] == [], 'Expected empty measurements array'
print('OK: Empty JSON array produced')
"
```

**Expected outcome**: Valid empty JSON array `[]`, CSV with header only, XML with empty root.

---

### 4. File Overwrite Warning

```bash
# Run export twice to same path
python -m specmetrics measure --export json --output measurements.json
python -m specmetrics measure --export json --output measurements.json
# Inspect logs for: WARNING  Overwriting existing file: measurements.json
```

**Expected outcome**: Second export overwrites the file. Warning is logged.

---

### 5. Publisher Telemetry (FR-004)

```bash
# Start mock OTLP receiver
python -m specmetrics.testing.mock_otel &

# Run with publisher enabled
python -m specmetrics measure --publish otel --otel-endpoint http://localhost:4318

# Verify metrics received
python -m specmetrics.testing.mock_otel check
# Expected: measurement.count, measurement.functional_size metrics received
```

**Expected outcome**: Metrics appear in the mock telemetry receiver within 30 seconds.

---

### 6. Publisher Failure Isolation (FR-006)

```bash
# Run with unreachable publisher endpoint
python -m specmetrics measure --publish otel --otel-endpoint http://localhost:19999

# Verify pipeline completes (export files still produced)
ls /tmp/export-test/measurements.json
# Verify warning logged
# Expected: ERROR logs for publisher, but export files still exist
```

**Expected outcome**: Pipeline completes. Exports produced. Publisher failure logged as warning.

---

### 7. Custom Plugin Registration (FR-007, FR-008, SC-003)

```bash
# Register a test plugin (see exporter-plugin contract)
python -m specmetrics plugins register tests/plugins/test_exporter.py

# List exporters to verify discovery
python -m specmetrics plugins list --type exporter
# Expected: json, csv, xml, test

# Export using custom plugin
python -m specmetrics measure --export test --output /tmp/export-test/test-output.testfmt
```

**Expected outcome**: Custom plugin discovered and executable without modifying core code.

---

## Edge Case Tests

| Scenario | Command | Expected Result |
|----------|---------|-----------------|
| No exporters configured | `python -m specmetrics measure --export ''` | Warning: no exporters selected |
| Zero-result pipeline | `python -m specmetrics measure --spec empty.md --export json` | Valid empty JSON file |
| Invalid export format | `python -m specmetrics measure --export invalidfmt` | Error: unknown format "invalidfmt" |
| Large dataset (10K funcs) | `python -m specmetrics measure --fixture large-10k --export json` | Completes in <60s |
| Concurrent run | Start two exports from different terminals | Both complete (serial per-format within each) |

---

## References

- [Data Model](data-model.md) — Entity definitions and validation rules
- [Exporter Plugin Contract](contracts/exporter-plugin.md) — Plugin interface specification
- [Publisher Plugin Contract](contracts/publisher-plugin.md) — Publisher plugin interface
- [Specification](spec.md) — Feature requirements and success criteria
