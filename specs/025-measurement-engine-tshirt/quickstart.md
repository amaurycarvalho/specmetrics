# Quickstart: T-Shirt Sizing Measurement Engine

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `025-measurement-engine-tshirt`
- Story Points Measurement Engine (024) must be operational (T-Shirt consumes its output)
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
```

## Validation Scenarios

### Scenario 1: Classify from known SP results

```bash
pytest tests/unit/test_tshirt_classifier.py -v -k test_classify_from_known_sp
```

**Expected**: Each Story Point value maps to the correct T-Shirt size per FR-015. SP=1→XS, SP=2→S, SP=3→S, SP=5→M, SP=8→M, SP=13→L, SP=20→XL, SP=40→XXL, SP=100→XXL.

**Data model reference**: `specs/025-measurement-engine-tshirt/data-model.md`

### Scenario 2: Custom mapping via Rule Pack

```bash
pytest tests/unit/test_tshirt_classifier.py -v -k test_custom_mapping
```

**Expected**: A 5-level override (XS, S, M, L, XL) with custom SP ranges is accepted and used. Overlapping ranges are rejected (FR-019).

### Scenario 3: Missing Story Points gracefully degrades

```bash
pytest tests/unit/test_tshirt_classifier.py -v -k test_missing_sp_result
```

**Expected**: When Story Points result is None, engine returns empty result with warnings. Pipeline continues without failure.

### Scenario 4: Deterministic classification

```bash
pytest tests/unit/test_tshirt_classifier.py -v -k test_deterministic
```

**Expected**: Identical SP input → identical T-Shirt classifications (all fields equal).

### Scenario 5: Empty CFM (via empty SP result)

```bash
pytest tests/unit/test_tshirt_classifier.py -v -k test_empty_sp_result
```

**Expected**: Empty items list → zero total items, empty distribution, no errors.

### Scenario 6: Full pipeline integration

```bash
pytest tests/integration/test_tshirt_pipeline.py -v
```

**Expected**: Pipeline executes CFM → Story Points → T-Shirt Sizing. T-Shirt result contains per-item classifications. Event payload includes distribution and timing.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/025-measurement-engine-tshirt/data-model.md` |
| Measurement API | `specs/025-measurement-engine-tshirt/contracts/measurement-api.md` |
| Spec | `specs/025-measurement-engine-tshirt/spec.md` |
