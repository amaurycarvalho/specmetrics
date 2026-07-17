# Quickstart: Token Points Measurement Engine

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `022-measurement-engine-token-points`
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
```

## Validation Scenarios

### Scenario 1: Measure a known CFM + CSM

```bash
pytest tests/unit/test_token_points_calculator.py -v -k test_calculate_from_known_models
```

**Expected**: Token Points calculated from a sample CFM and CSM. Total = Specification Cost + Code Generation Cost. Every element contributes to the breakdown.

**Data model reference**: `specs/022-measurement-engine-token-points/data-model.md`

### Scenario 2: Deterministic measurement

```bash
pytest tests/unit/test_token_points_calculator.py -v -k test_deterministic
```

**Expected**: Measuring identical CFM + CSM twice produces identical `TokenPointsMeasurement` (all fields equal).

### Scenario 3: Missing CSM gracefully degrades

```bash
pytest tests/unit/test_token_points_calculator.py -v -k test_missing_csm
```

**Expected**: When CSM is None, Specification Cost is 0, Code Generation Cost is calculated from CFM alone. A warning is emitted.

### Scenario 4: Missing CFM gracefully degrades

```bash
pytest tests/unit/test_token_points_calculator.py -v -k test_missing_cfm
```

**Expected**: When CFM is None, Code Generation Cost is 0, Specification Cost is calculated from CSM alone.

### Scenario 5: Calibration profile loading

```bash
pytest tests/unit/test_token_points_calibration.py -v -k test_load_default_calibration
```

**Expected**: Default calibration loaded with all weights present. Organization override file overrides specific keys while keeping defaults for others.

### Scenario 6: Performance benchmark

```bash
pytest tests/unit/test_token_points_calculator.py -v -k test_performance_500_elements --benchmark-only
```

**Expected**: 500 canonical elements (250 CFM + 250 CSM) measured in under 2 seconds (SC-006).

### Scenario 7: Measurement contract conformance

```bash
pytest tests/contract/test_token_points_measurement.py -v
```

**Expected**: Plugin metadata conforms to `PluginType.MEASUREMENT`. Handler subscribes to `MEASUREMENT_COMPLETED`. Result model includes all required fields.

### Scenario 8: Full pipeline integration

```bash
pytest tests/integration/test_token_points_pipeline.py -v
```

**Expected**: Pipeline executes with CFM + CSM → Token Points measurement stored in `ctx.measurement_result`. Event payload contains total score, breakdown, element counts.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/022-measurement-engine-token-points/data-model.md` |
| Measurement API | `specs/022-measurement-engine-token-points/contracts/measurement-api.md` |
| Spec | `specs/022-measurement-engine-token-points/spec.md` |
