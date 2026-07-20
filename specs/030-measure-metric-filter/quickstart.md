# Quickstart: Measure Metric Filtering & JSON Output

## Prerequisites

- Python 3.13+
- SpecMetrics installed (`pip install -e .` or `uv sync`)
- A valid SpecMetrics project with specification documents

## Setup

No additional setup required. Metric filtering is built into the existing `specmetrics measure` command.

## Run Measurement with All Metrics (Default)

```bash
# Default — all metrics
specmetrics measure

# Explicit all
specmetrics measure all

# Expected text output:
#   SpecMetrics v0.3.1 — Measurement Complete
#   ────────────────────────────────────────────────
#   Project: /home/user/project
#   Pipeline: 6 stages
#   Duration: 42.0s
#
#   Results:
#     Business Complexity Points: 18
#     Function Points: 42
#     Simplified Function Points: 38
#     SNAP: 15
#     Story Points: 21
#     TShirt XS: 0
#     TShirt S: 1
#     TShirt M: 2
#     TShirt L: 1
#     TShirt XL: 1
#     TShirt XXL: 0
#     Token Points: 1200
#     Cognitive Points: 34
#     ├─ ILF: 10  (sub-details preserved)
#     ├─ EIF: 3
#     ...
#
#   Stages:
#     ✓ discover      (1.2s) [speckit] (5 documents)
#     ✓ extract       (5.7s) (24 items)
#     ✓ measure       (42.0s) (8 metrics)
#
#   Output: .specmetrics/output/specmetrics-output.json
```

## Filter to a Single Metric

```bash
# Single metric
specmetrics measure fpa

# Expected: Only Function Points result displayed
# Results:
#   Function Points: 42
#   ├─ ILF: 10
#   ├─ EIF: 3
```

```bash
specmetrics measure sfp

# Results:
#   Simplified Function Points: 38
```

## Filter to Multiple Metrics

```bash
specmetrics measure fpa, sfp

# Results:
#   Function Points: 42
#   ├─ ILF: 10
#   ├─ EIF: 3
#   Simplified Function Points: 38
```

```bash
specmetrics measure bcp, sp, tp

# Results:
#   Business Complexity Points: 18
#   Story Points: 21
#   Token Points: 1200
```

## Error Handling

```bash
# Invalid metric name
specmetrics measure unknown
# Expected: Exit code 1, lists valid identifiers

# Partially invalid
specmetrics measure fpa, unknown
# Expected: Exit code 1, error before any execution
```

## JSON Output

After any successful `specmetrics measure` run, the JSON file is at:

```bash
cat .specmetrics/output/specmetrics-output.json
```

See [contracts/measure-cli-interface.md](contracts/measure-cli-interface.md) for the full JSON schema.

## Test Suite

```bash
# Run CLI tests
pytest tests/cli/test_app.py -v -k "measure"

# Run orchestrator filter tests
pytest tests/unit/application/test_orchestrator.py

# Run integration test
pytest tests/integration/test_metric_filter_pipeline.py

# Run contract tests
pytest tests/contract/test_measure_output.py
```

## Key Contracts

| Artifact | Location |
|---|---|
| CLI interface | [contracts/measure-cli-interface.md](contracts/measure-cli-interface.md) |
| Data model | [data-model.md](data-model.md) |
| JSON output schema | `contracts/measure-cli-interface.md#json-output-format` |

## Scenarios Covered

| Scenario | Command | Expected Result |
|---|---|---|
| All metrics (default) | `specmetrics measure` | Exit 0, all 8 metrics shown, JSON file written |
| Single metric | `specmetrics measure fpa` | Exit 0, only FPA shown |
| Multiple metrics | `specmetrics measure fpa, sfp` | Exit 0, only FPA and SFP shown |
| Invalid metric | `specmetrics measure bad` | Exit 1, error with valid IDs |
| Partial invalid | `specmetrics measure fpa, bad` | Exit 1, error before execution |
| With stage filter | `specmetrics measure fpa --stage measure` | Only measure stage, only FPA |
| Default all | `specmetrics measure all` | Same as `specmetrics measure` |
