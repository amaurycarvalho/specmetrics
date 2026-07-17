# Quickstart: Story Points Measurement Engine

## Prerequisites

- Python >= 3.12 with `uv` or `pipx`
- Clone of `specmetrics` at branch `024-measurement-engine-storypoints`
- Dependencies installed: `uv sync` (or `pip install -e ".[dev]"`)

## Setup

```bash
# From repo root
uv sync
```

## Validation Scenarios

### Scenario 1: Estimate from a known CFM

```bash
pytest tests/unit/test_storypoints_calculator.py -v -k test_estimate_from_known_cfm
```

**Expected**: Story Points calculated via multi-factor weighted sum. Each Functional Process has raw_score + normalized_value. Total equals sum of items.

**Data model reference**: `specs/024-measurement-engine-storypoints/data-model.md`

### Scenario 2: Multi-factor scoring

```bash
pytest tests/unit/test_storypoints_factor_scorer.py -v
```

**Expected**: Each default factor (business_interactions, logical_information, etc.) scores correctly from CFM relationships. Empty CFM produces zero scores.

### Scenario 3: Fibonacci normalization

```bash
pytest tests/unit/test_storypoints_normalizer.py -v
```

**Expected**: Raw scores normalize to correct Fibonacci values per threshold table. Scale: 1, 2, 3, 5, 8, 13, 20, 40, 100. Values outside scale are clamped.

### Scenario 4: Deterministic measurement

```bash
pytest tests/unit/test_storypoints_calculator.py -v -k test_deterministic
```

**Expected**: Identical CFM → identical Story Points (all fields equal, including factor_breakdown).

### Scenario 5: Empty CFM

```bash
pytest tests/unit/test_storypoints_calculator.py -v -k test_empty_cfm
```

**Expected**: Zero items estimated. Total story points = 0. No errors.

### Scenario 6: Duplicate detection

```bash
pytest tests/unit/test_storypoints_calculator.py -v -k test_duplicate_merge
```

**Expected**: Functional Processes with identical content fingerprints are merged. Duplicates counted in execution_metadata.fps_merged_as_duplicates.

### Scenario 7: Performance benchmark

```bash
pytest tests/unit/test_storypoints_calculator.py -v -k test_performance_500_fps --benchmark-only
```

**Expected**: 500 Functional Processes estimated in under 5 seconds (SC-003).

### Scenario 8: Full pipeline integration

```bash
pytest tests/integration/test_storypoints_pipeline.py -v
```

**Expected**: Pipeline executes CFM → Story Points stored in `ctx.measurement_result`. Event payload includes total, distribution, and timing.

## Key Contracts

| Artifact | Path |
|----------|------|
| Data model | `specs/024-measurement-engine-storypoints/data-model.md` |
| Measurement API | `specs/024-measurement-engine-storypoints/contracts/measurement-api.md` |
| Spec | `specs/024-measurement-engine-storypoints/spec.md` |
