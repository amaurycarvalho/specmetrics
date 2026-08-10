# Data Model: Quality Gate for CI and Release Builds

**Date**: 2026-08-03
**Source**: `specs/043-quality-gate-implementation/spec.md` (Key Entities + FRs)
**Research**: `research.md` (R-4, R-5)

## Entities

### QualityCheck

A single tool execution in one gate run.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `name` | string | Metric/check name (e.g., "coverage", "complexity", "security") | FR-006 |
| `value` | number/string | Measured value | FR-006 |
| `threshold` | number/string | Configured threshold | FR-006 |
| `severity` | enum(blocking, warning) | Blocks the run or is informational | FR-005 |
| `status` | enum(pass, warn, fail) | Outcome of the check | FR-006 |
| `evidence` | list[string] | Affected files / sections justifying outcome | FR-007 |

**Validation rules**: `status == fail` requires `evidence` non-empty (FR-007). A check whose tool errors is `status == fail` (FR-008).

### QualityReport

Consolidated record of one gate run (US3).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `run_id` | string | Unique identifier of the run | US3 |
| `python_version` | string | Version under which checks ran | FR-010 |
| `checks` | list[QualityCheck] | All evaluated metrics | FR-006 |
| `overall_status` | enum(pass, fail) | Derived: fail if any blocking check fails or any tool errors | FR-001 |
| `timestamp` | datetime | When the run completed | US3 |

**Validation rules**: `overall_status == pass` iff no `blocking` check is `fail` (FR-005). Exactly one report per run per Python version (US3).

### QualityException

Documented, approved waiver for pre-existing debt (FR-011).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `id` | string | Unique identifier | FR-011 |
| `check` | string | Which check is waived | FR-011 |
| `scope` | string | Files/patterns excluded | FR-011 |
| `expires` | date | Duration of the waiver | FR-011 |
| `rationale` | string | Justification | FR-011 |
| `approved_by` | string | Reviewer approval reference | FR-011 |

**Validation rules**: Exemptions MUST be explicit, reviewed, time-boxed; never automatic (FR-011).

### ReleaseVerification

Links a published artifact to the passing gate run that authorized it (SC-005).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `version` | string | Released version (validated by FR-009) | SC-005 |
| `run_id` | string | Passing quality run id | SC-005 |
| `artifact` | string | Published artifact reference | SC-005 |

## Relationships

```text
QualityReport 1 ── * QualityCheck
QualityReport * ── 1 PythonVersion
ReleaseVerification 1 ── 1 QualityReport (passing)
QualityException * ── 1 QualityCheck (waived)
```

## State Transitions

- **QualityReport**: `running → (all blocking checks pass) → pass` | `running → (any blocking check fails OR tool errors) → fail`
- **Release (build-wheel)**: `triggered → ci+gate success → build → publish` | `triggered → ci+gate failure → aborted (no artifact)`

## Notes

- No persistent database is introduced (Storage: N/A). These entities are represented as report artifacts, CI statuses and configuration records, consistent with the Assumptions (single shared report per run, per-PR bots deferred).
- Identity: `QualityReport.run_id` is the CI run id; uniqueness enforced by CI.
