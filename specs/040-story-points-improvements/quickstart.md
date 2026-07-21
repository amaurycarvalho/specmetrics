# Quickstart: Story Points Improvements

**Feature**: 040-story-points-improvements  
**Date**: 2026-07-21

## Prerequisites

- Python 3.13 with `tiktoken` installed (or fallback character-count mode)
- SpecMetrics project with existing Story Points plugin
- At least one specification file processed through the semantic extraction pipeline (producing both CFM and CSM canonical models)

## Validation Scenarios

### Scenario 1: Content-Based Estimation

**Purpose**: Verify that content depth affects raw scores.

**Steps**:
1. Create a calibration profile with `content_multiplier: 0.1` (default).
2. Process a specification with at least one functional process that has a non-trivial description (>100 tokens).
3. Run Story Points measurement.
4. Inspect the `WorkItem` for that functional process.

**Expected**: `content_tokens > 0`, `content_score == content_tokens * 0.1`, `raw_score == structural_score + content_score`.

**Regression check**: Set `content_multiplier: 0.0`, re-run. `content_score` must be `0.0` and `raw_score` must equal `structural_score`.

### Scenario 2: CSM Element Estimation

**Purpose**: Verify that CSM elements contribute to the total score.

**Steps**:
1. Process a specification containing at least 5 decisions, 3 assumptions, and 10 acceptance criteria.
2. Run Story Points measurement.
3. Inspect `specification_effort_total` and `items` filtered by `source_model == "CSM"`.

**Expected**: `specification_effort_total > 0`. Items with `element_type` in `["decision", "assumption", "acceptance_criterion"]` appear with `source_model == "CSM"` and non-null `base_weight`.

### Scenario 3: Relative Ranking Normalization

**Purpose**: Verify that lower raw scores map to lower Fibonacci values.

**Steps**:
1. Run Story Points on a specification with at least 9 elements (to exercise all 9 Fibonacci bands).
2. Extract the `items` list sorted by `raw_score` ascending.
3. Verify the mapping of `rank_position` to `normalized_value`.

**Expected**:
- Item with `rank_position == 0` has `normalized_value == 1`.
- Item with `rank_position == N-1` (highest) has `normalized_value == 100`.
- `normalized_value` is non-decreasing as `raw_score` increases.
- The distribution histogram (`distribution` dict) covers the Fibonacci scale values.

### Scenario 4: Cross-Specification Comparability Payload

**Purpose**: Verify output fields enabling specification comparison.

**Steps**:
1. Run Story Points on any specification.
2. Inspect the measurement result payload.

**Expected**: The result contains:
- `content_multiplier` (float)
- `specification_effort_total` (float)
- `implementation_effort_total` (float)
- `content_tokens_by_type` (dict)
- `specification_effort_total + implementation_effort_total == total_raw_score`

### Scenario 5: Backward Compatibility

**Purpose**: Verify old calibration profiles and zero-content-multiplier behavior.

**Steps**:
1. Create a calibration YAML file with only `version: "1.0"`.
2. Run Story Points measurement.
3. Run again with `content_multiplier: 0.0` and compare raw scores against the current factor-only engine.

**Expected**:
- Profile with only `version` loads without errors and uses all defaults.
- `content_multiplier: 0.0` produces FP raw scores identical to the current engine's `calculate()` output (within floating-point tolerance).

### Scenario 6: Fallback Weight for Unknown Types

**Purpose**: Verify behavior when an element type is not in the base weight mappings.

**Steps**:
1. Create or inject an element with a type not in `csm_base_weights` or `cfm_base_weights`.
2. Run Story Points measurement.

**Expected**: The element uses `default_fallback_weight` as its `base_weight`. A `MeasurementWarning` with code `"UNKNOWN_ELEMENT_TYPE"` is emitted.

### Scenario 7: No Functional Processes

**Purpose**: Verify behavior when a specification has CSM elements but zero functional processes.

**Steps**:
1. Process a specification with only CSM elements (decisions, assumptions, etc.) and no functional processes.
2. Run Story Points measurement.

**Expected**: A result is produced from CSM element contributions. A `MeasurementWarning` with code `"NO_FPS_FOUND"` is emitted. `implementation_effort_total` may be 0 but `specification_effort_total > 0`.

## Test Commands

```bash
# Run all Story Points unit tests
pytest tests/unit/test_storypoints_*.py -v

# Run contract tests
pytest tests/contract/test_storypoints_measurement.py -v

# Run integration tests
pytest tests/integration/test_storypoints_pipeline.py -v

# Run with coverage
pytest tests/unit/test_storypoints_*.py \
       tests/contract/test_storypoints_measurement.py \
       tests/integration/test_storypoints_pipeline.py \
       --cov=specmetrics.plugins.measurement.storypoints -v
```
