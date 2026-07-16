# Quickstart: SFP Measurement Engine

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

### Scenario 1: Basic SFP Measurement

```bash
specmetrics measure --method sfp
```

**Expected outcome**: Measurement completes automatically. Output includes total SFP, component counts (Functional Processes and Logical Functions), and evidence references for each component.

### Scenario 2: Measurement Determinism

```bash
specmetrics measure --method sfp --output result1.json
specmetrics measure --method sfp --output result2.json
diff result1.json result2.json
```

**Expected outcome**: Repeated executions on the same CFM produce byte-identical results (SC-001).

### Scenario 3: Explainable Measurement

```bash
specmetrics measure --method sfp --explain
```

**Expected outcome**: Each measured component includes originating CFM element, applied rule, contribution value, and evidence references down to the specification fragment (SC-002, FR-033).

### Scenario 4: Rule Pack Customization

```bash
specmetrics measure --method sfp --rule-pack my-org-rules.yml
```

**Expected outcome**: Rule Pack exclusions and overrides are applied. Excluded components are reported with applied rule identifiers. Total SFP reflects the customized counting rules.

### Scenario 5: Incremental Recalculation

```bash
specmetrics measure --method sfp --incremental
```

**Expected outcome**: Only modified functional components are recalculated (SC-004, FR-040). Output includes execution statistics showing the reduced computation scope.

### Scenario 6: Empty CFM

```bash
specmetrics measure --method sfp --empty-cfm
```

**Expected outcome**: Measurement completes with zero counts. No errors generated. Warnings may indicate the empty input.

### Scenario 7: Performance Benchmark

```bash
# Medium-sized CFM (≤500 Functional Processes, ≤300 Logical Functions)
specmetrics measure --method sfp --benchmark
```

**Expected outcome**: Measurement completes in under 5 seconds (SC-003).

## Contracts Reference

- [Measurement Plugin Interface](contracts/measurement-plugin-interface.md) — Plugin interface, discovery, and Rule Pack contract

## Data Model Reference

- [Data Model](data-model.md) — Full field definitions and validation rules
