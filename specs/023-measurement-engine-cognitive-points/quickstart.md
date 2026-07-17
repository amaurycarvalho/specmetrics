# Quickstart: Cognitive Points Measurement Engine

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `023-measurement-engine-cognitive-points`
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
```

## Validation Scenarios

### Scenario 1: Measure a known CFM + CSM

```bash
pytest tests/unit/test_cognitive_points_calculator.py -v -k test_calculate_from_known_models
```

**Expected**: Cognitive Points calculated via three-stage formula. Each element classified into a Bloom level with correct weight. Raw score equals sum of both components. Fibonacci normalization applied.

**Data model reference**: `specs/023-measurement-engine-cognitive-points/data-model.md`

### Scenario 2: Bloom classification

```bash
pytest tests/unit/test_cognitive_points_bloom.py -v
```

**Expected**: Each canonical element type maps to the correct default Bloom level. Unknown types fall back to `default_bloom_level`. Custom mappings override defaults.

### Scenario 3: Fibonacci normalization

```bash
pytest tests/unit/test_cognitive_points_normalizer.py -v
```

**Expected**: Raw scores normalize to correct Fibonacci values per threshold table. Scores below minimum threshold return 1. Scores above max threshold return the max value (100).

### Scenario 4: Missing CSM gracefully degrades

```bash
pytest tests/unit/test_cognitive_points_calculator.py -v -k test_missing_csm
```

**Expected**: When CSM is None, Specification Review Effort is 0, Functional Validation Effort calculated from CFM alone.

### Scenario 5: Deterministic measurement

```bash
pytest tests/unit/test_cognitive_points_calculator.py -v -k test_deterministic
```

**Expected**: Identical CFM + CSM + calibration → identical Cognitive Points (all fields equal).

### Scenario 6: Performance benchmark

```bash
pytest tests/unit/test_cognitive_points_calculator.py -v -k test_performance_500_elements --benchmark-only
```

**Expected**: 500 canonical elements measured in under 2 seconds (SC-006).

### Scenario 7: Full pipeline integration

```bash
pytest tests/integration/test_cognitive_points_pipeline.py -v
```

**Expected**: Pipeline executes with CFM + CSM → Cognitive Points stored in `ctx.measurement_result`. Event payload contains normalized score, Bloom distribution, and Fibonacci normalization details.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/023-measurement-engine-cognitive-points/data-model.md` |
| Measurement API | `specs/023-measurement-engine-cognitive-points/contracts/measurement-api.md` |
| Spec | `specs/023-measurement-engine-cognitive-points/spec.md` |
