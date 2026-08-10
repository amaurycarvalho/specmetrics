# Data Model: Apply Quality Rules and Make the Quality Gate Pass

**Date**: 2026-08-04
**Source**: `specs/044-apply-quality-rules/spec.md` (Key Entities + FRs) + `research.md` (R-1, R-4, R-5)
**Note**: This feature is primarily behavior-preserving refactoring and gate-tooling correction. It introduces no new persistent entities and no new runtime data store; it reuses the gate's existing report model (from feature 043) and adds the corrected maintainability-index severity contract. The entities below define the evaluation contract the gate must satisfy.

## Entities

### ComplexityBlock

A single function, method or class evaluated for cyclomatic complexity (FR-002).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `location` | string | File path and line (e.g., `kernel/deterministic_engine.py:197`) | FR-002 |
| `name` | string | Block identifier (class/method/function name) | FR-002 |
| `ccn` | number | Cyclomatic complexity number | FR-002 |
| `grade` | enum(A..F) | Radon grade derived from CCN | FR-002 |
| `rank_type` | enum(block, module) | Whether this is a block or a whole-module rank | FR-002/FR-004 |

**Validation rules**: Block is acceptable iff `ccn ≤ 10` and `grade ≤ B` (FR-002). Severity of violation = blocking (FR-002). Module rank acceptable iff `grade ≤ B` and the count of modules ranked B-or-worse ≤ 20 (FR-004).

### ComplexityModuleRank

Per-module complexity disposition used by the `--max-modules=20` ceiling (FR-004).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `module` | string | Module path | FR-004 |
| `worst_block_grade` | enum(A..F) | The worst block grade in the module (drives module rank) | R-3 |
| `rank` | enum(A..F) | Module rank | FR-004 |

**Validation rules**: The count of modules with `rank ≥ B` MUST be ≤ 20; otherwise the gate fails (blocking) (FR-004, clarification 2026-08-04).

### MaintainabilityIndexReading

Corrected evaluation of the maintainability index (FR-007 + clarification).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `worst_mi` | number | Minimum MI score across evaluated modules | FR-007 |
| `value_source` | string | Parser used (must be the trailing `<grade> (<score>)` token) | R-4 |

**Validation rules**: `worst_mi ≥ 70` → pass; `30 ≤ worst_mi < 70` → warning (non-blocking); `worst_mi < 30` → **blocking** (gate fails). A parser returning an empty/wrong value must not silently pass or warn (FR-014, R-4).

### QualityCheck (reused from feature 043)

A single tool evaluation in one gate run — component coverage, mutation survival, duplication, security findings, lint, Halstead (difficulty/effort/bugs), lines/function, and MI.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `name` | string | Metric/check name | FR-006 |
| `value` | number/string | Measured value | FR-006 |
| `threshold` | number/string | Configured threshold | FR-006 |
| `severity` | enum(blocking, warning, informational) | Blocks the run or is informational | FR-005 |
| `status` | enum(pass, warn, fail) | Outcome | FR-005 |
| `evidence` | list[string] | Affected files/sections | FR-013 |

**Validation rules**: `status == fail` requires non-empty `evidence` (FR-013). A tool error → `status == fail` (FR-014). `severity == blocking and status == fail` ⇒ gate fails.

## Relationships

```text
ComplexityBlock * ── 1 ComplexityModuleRank        # a module's rank is its worst block
QualityReport 1 ── * QualityCheck                   # one report aggregates all metric checks
QualityCheck * ──1 MaintainabilityIndexReading      # MI captured as one check
```

## State Transitions

- **Gate run** (FR-001): `running → (all blocking checks pass) → pass` | `running → (any blocking check fails OR tool error) → fail`.
- **MaintainabilityIndexReading**: `evaluated`; classification per worst_mi — `≥70 pass`, `30–69 warn`, `<30 block`.
- **Module count**: `28 B-or-worse → (≥ 8 modules raised to A) → 20 or fewer B-or-worse → gate passes`.

## Notes

- No database or new persistence. Entities are configuration/contract definitions consumed by the gate scripts and CI; the canonical inventory lives in `research.md` (R-1, R-5).
- Halstead difficulty/effort/bugs and lines-per-function remain warning/informational and never fail the gate (FR-008/FR-009).
- The `Block Grade Map` (spec Key Entity) maps grade→threshold (Grade B ≤ 10); it is realized as the `xenon --max-absolute=B` + per-block `ccn ≤ 10` contract.