# Quickstart: Refactor Pipeline Orchestrator for Maintainability

**Feature**: [spec.md](./spec.md) | **Phase**: 1 | **Date**: 2026-08-04

Validation scenarios that prove the refactor is complete and safe. This is a run/validation
guide — implementation belongs in `tasks.md`.

## Prerequisites

- Python 3.13 virtualenv at `.venv` (established by the project Makefile).
- `make install` or `pip install -e .[dev,quality]` (dev deps for pytest/coverage; quality
  deps provide `radon`, `ruff`, `xenon`, `lizard`).

## Scenario 1 — Maintainability gate passes (SC-001 / FR-001)

Validate the orchestrator module scores **MI > 30** and no module stays below the blocking
threshold.

```bash
.venv/bin/radon mi -s specmetrics/application/orchestrator.py
```

**Expected**: scores above `30` (worst >= 30, target >= 30 is the gate; >= 70 is a pass).
Then run the whole complexity gate:

```bash
make complexity
# scripts/complexity_metrics.py runs radon mi and must exit 0:
.venv/bin/python scripts/complexity_metrics.py
```

**Expected**: `complexity_metrics.py` prints `... worst N >= 30` / no `[Blocking] Maintainability Index` line, and exits `0`. No `[Blocking]` violations for the orchestrator. (Halstead lines may be Warnings only — never blocking.)

## Scenario 2 — Full test suite passes unmodified (SC-002 / FR-006)

```bash
make test
# or:
.venv/bin/python -m pytest --tb=short --cov=. --cov-report=term-missing --cov-fail-under=85
```

**Expected**: 100% of existing tests pass with NO changes to test code and no changes to public signatures (contract [`orchestrator-public-api.md`](./contracts/orchestrator-public-api.md)). Coverage ≥ 85%.

## Scenario 3 — Behavioral equivalence (SC-003 / SC-004 / FR-002, US-2)

Prove identical pipeline results before/after the refactor using the run-artifact round-trip.

1. Take a representative sample specification project (any under `specs/`, e.g. `specs/045-refactor-orchestrator-mi`).
2. Record run artifacts before the refactor (from `main`/the pre-refactor commit) and after:

```bash
.venv/bin/specmetrics measure --project <sample-project> --output-format json \
  --output-path /tmp/specmetrics-before
# ...after the refactor...
.venv/bin/specmetrics measure --project <sample-project> --output-format json \
  --output-path /tmp/specmetrics-after
diff -r /tmp/specmetrics-before /tmp/specmetrics-after && echo "IDENTICAL"
```

**Expected**: `diff -r` produces no differences (stages executed, metrics, stage entities,
statuses, and error results byte-for-byte equivalent; SC-003) and success/failure status
distribution is identical (SC-004). For the CLI measure flow, `save_run_artifacts` writes
`<project>/.specmetrics/runs/<id>/`; compare those run folders the same way, or via
`read_run_artifacts`.

## Scenario 4 — Error paths preserved (US-2 / FR-005, Edge Cases)

- Invalid/missing project path → `execute` returns `PipelineResult(status=FAILED, error="Project path not found: <path>")`.
- Kernel `PipelineError` path → `FAILED` result with the error string.
- Optional plugin / adapter / exporter load failure → fail-loud-with-warning, pipeline continues.
- Config system load failure → tolerated; pipeline proceeds without config.
- No diagnostics / no measurement / no canonical model → identical empty results.

Covered by existing tests in `tests/application/test_orchestrator.py` and integration
pipeline tests; verify they pass in Scenario 2.

## Scenario 5 — Maintainer separability (US-3 / FR-003)

Inspect the refactored `specmetrics/application/` package and confirm each responsibility
lives in its own module (see [data-model.md](./data-model.md#refactor-unit-boundaries)):
entity building, metric assembly, stage/result assembly, artifact persistence, structured
export, stage/event mapping, truncation — with a thin `orchestrator.py` entry point.

```bash
find specmetrics/application -name "*.py"
```

**Expected**: `orchestrator.py` is small/thin; each named unit module exists; `list_plugins`,
`discover_plugins`, `set_config_system`, `get_version_info`, `execute`, plus module functions
`save_run_artifacts`/`read_run_artifacts` remain importable from `specmetrics.application.orchestrator`.

## References

- Public API contract: [orchestrator-public-api.md](./contracts/orchestrator-public-api.md)
- Data model & unit boundaries: [data-model.md](./data-model.md)
- Research (MI measurement, test-coupling findings): [research.md](./research.md)