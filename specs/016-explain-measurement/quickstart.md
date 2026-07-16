# Quickstart: Explain Measurement

## Prerequisites

- Python 3.13+
- SpecMetrics installed (`pip install -e .` or `uv sync`)
- A measurement run that has completed successfully (via `specmetrics measure`)

## Setup

No additional setup required. The explain capability is built into the `specmetrics` CLI.

## Explain a Measurement

```bash
# Explain all metrics from a measurement run
specmetrics explain meas-20260716-143022

# Expected output (text format):
#   Measurement Run: meas-20260716-143022
#   Spec: specs/015-validation-pipeline/spec.md
#
#   Metrics:
#     functional_size = 12
#       Elements: UserRepository (ILF, Low, 3), ...
#       Evidence: 5 references from 3 sections
#     function_count = 5
#       Elements: 3 ILF, 2 EIF
#       Evidence: 5 references from 4 sections
#
#   Rules Applied: 2 (weight_override: complexity_override)
```

```bash
# Explain a specific metric
specmetrics explain meas-20260716-143022 --metric functional_size

# With JSON output
specmetrics explain meas-20260716-143022 --format json
```

## Compare Two Measurement Runs

```bash
# Compare current run with a baseline
specmetrics explain meas-20260716-143022 --compare meas-20260715-120000

# Expected output:
#   Comparison: meas-20260715-120000 → meas-20260716-143022
#   Changed: functional_size (10 → 12, Δ +2)
#   Added: 0 metrics
#   Removed: obsolete_metric
#   Unchanged: function_count
```

## Error Handling

```bash
# Non-existent run ID
specmetrics explain meas-nonexistent
# Expected: Exit code 1, "Run ID not found: meas-nonexistent"

# Invalid metric name
specmetrics explain meas-20260716-143022 --metric nonexistent
# Expected: Metric "nonexistent" not found in run meas-20260716-143022
```

## Test Suite

```bash
# Run explanation unit tests
pytest tests/unit/explanation/

# Run integration tests
pytest tests/integration/test_explain_service.py

# Run CLI contract tests
pytest tests/contract/test_explain_cli.py
```

## Key Contracts

| Artifact | Location |
|---|---|
| CLI interface | [contracts/explain-measurement-interface.md](contracts/explain-measurement-interface.md) |
| Data model | [data-model.md](data-model.md) |
| Explanation formatters | Plugin entry point group `specmetrics.explanation_formatters` |
| Evidence tracing | `kernel/evidence_graph.py`, `GraphBackend.traverse()` |

## Scenarios Covered

| Scenario | Command | Expected Result |
|---|---|---|
| Explain all metrics | `specmetrics explain <run_id>` | Exit 0, shows all metrics with elements and evidence |
| Explain single metric | `specmetrics explain <run_id> --metric functional_size` | Exit 0, shows only that metric |
| Compare two runs | `specmetrics explain <run_id> --compare <baseline>` | Exit 0, shows changes with per-element diff |
| Unknown run ID | `specmetrics explain bad-id` | Exit 1, run not found error |
| Unknown metric | `specmetrics explain <run_id> --metric bad` | Exit 1, metric not found error |
| JSON output | `specmetrics explain <run_id> --format json` | Exit 0, valid JSON on stdout |
