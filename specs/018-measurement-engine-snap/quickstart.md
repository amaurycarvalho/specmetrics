# Quickstart: SNAP Measurement Engine

## Prerequisites

- Python 3.13+
- Dependencies installed: `pydantic`, `structlog`, `opentelemetry-api`
- Project structured per `plan.md`

## Setup

```bash
# From repository root
uv sync  # or: pip install -e .
```

## Validation Scenarios

### Scenario 1: Basic SNAP Assessment

```bash
specmetrics measure --method snap
```

**Expected outcome**: Assessment completes automatically. Output includes total SNAP, category breakdowns, item counts per category, and evidence references for each assessed item.

### Scenario 2: Assessment Determinism

```bash
specmetrics measure --method snap --output result1.json
specmetrics measure --method snap --output result2.json
diff result1.json result2.json
```

**Expected outcome**: Repeated executions on the same CFM produce byte-identical results (SC-001).

### Scenario 3: Explainable Assessment

```bash
specmetrics measure --method snap --explain
```

**Expected outcome**: Each assessed item includes originating CFM element, assessment category, applied rule, contribution value, and evidence references down to the specification fragment (SC-002, FR-030).

### Scenario 4: Rule Pack Customization

```bash
specmetrics measure --method snap --rule-pack my-org-rules.yml
```

**Expected outcome**: Rule Pack exclusions and overrides are applied. Excluded items are reported with applied rule identifiers. Total SNAP reflects the customized assessment rules.

### Scenario 5: Incremental Reassessment

```bash
specmetrics measure --method snap --incremental
```

**Expected outcome**: Only modified assessment candidates are recalculated (SC-004, FR-037). Output includes execution statistics showing the reduced computation scope.

### Scenario 6: Empty CFM

```bash
specmetrics measure --method snap --empty-cfm
```

**Expected outcome**: Assessment completes with zero counts. No errors generated. Warnings may indicate the empty input.

### Scenario 7: Performance Benchmark

```bash
# Medium-sized CFM (≤500 assessment candidates)
specmetrics measure --method snap --benchmark
```

**Expected outcome**: Assessment completes in under 5 seconds (SC-003).

## Contracts Reference

- [Measurement Plugin Interface](contracts/measurement-plugin-interface.md) — Plugin interface, discovery, and Rule Pack contract

## Data Model Reference

- [Data Model](data-model.md) — Full field definitions and validation rules
