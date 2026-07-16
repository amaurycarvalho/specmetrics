# Quickstart: Validation Pipeline

## Prerequisites

- Python 3.13+
- SpecMetrics installed (`pip install -e .` or `uv sync`)
- A specification file following the project's spec template

## Setup

No additional setup required. Validation is built into the `specmetrics` CLI.

## Validate a Single Specification

```bash
# Basic validation
specmetrics validate specs/015-validation-pipeline/spec.md

# Expected output (pass):
# ✓ validated specs/015-validation-pipeline/spec.md — 7/7 rules passed

# With JSON output
specmetrics validate specs/015-validation-pipeline/spec.md --format json
```

## Validate with Failures

```bash
# Validate a spec missing mandatory sections
specmetrics validate specs/001-mvp-release-outline/spec.md

# Expected output (fail):
# ✗ specs/001-mvp-release-outline/spec.md — 5/7 rules passed
#   FAIL: mandatory-sections-exist — Missing section: "Constitution Check"
#   FAIL: mandatory-sections-exist — Missing section: "Assumptions"
```

## Batch Validation

```bash
# Validate all specs in the specs directory
specmetrics validate specs/ --batch

# Expected output:
# ✓ specs/015-validation-pipeline/spec.md — 7/7 passed
# ✓ specs/014-configuration-system/spec.md — 7/7 passed
# ✗ specs/001-mvp-release-outline/spec.md — 5/7 passed
# Batch: 3 documents, 2 passed, 1 failed
```

## Constitutional Compliance Only

```bash
specmetrics validate specs/015-validation-pipeline/spec.md --constitution-only
```

## Test Suite

```bash
# Run validation unit tests
pytest tests/unit/validation/

# Run integration tests
pytest tests/integration/test_validation_pipeline.py

# Run CLI contract tests
pytest tests/contract/test_validate_cli.py
```

## Key Contracts

| Artifact | Location |
|---|---|
| CLI interface | [contracts/validation-pipeline-interface.md](contracts/validation-pipeline-interface.md) |
| Data model | [data-model.md](data-model.md) |
| Validation rules | Plugin entry point group `specmetrics.validation_rules` |
| Rule config | `.specmetrics/rules/validation-rules.yml` |

## Scenarios Covered

| Scenario | Command | Expected Result |
|---|---|---|
| Valid spec | `specmetrics validate valid_spec.md` | Exit 0, all rules pass |
| Missing section | `specmetrics validate incomplete_spec.md` | Exit 1, lists missing sections |
| Unreadable file | `specmetrics validate nonexistent.md` | Exit 1, file error message |
| Empty file | `specmetrics validate empty.md` | Exit 1, empty document error |
| Batch run | `specmetrics validate specs/ --batch` | Exit 0/1, per-file summary |
| Constitutional check | `specmetrics validate spec.md --constitution-only` | Exit 0/1, principle checks |
