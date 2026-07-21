# Quickstart: T-Shirt Sizing Improvements

**Feature**: 041-tshirt-sizing  
**Date**: 2026-07-21

## Prerequisites

- SpecMetrics project with existing T-Shirt Sizing plugin
- Story Points measurement engine operational
- At least one specification file processed through the full measurement pipeline

## Validation Scenarios

### Scenario 1: Corrected Mapping — Value 8

**Purpose**: Verify that Story Point value 8 now maps to L (not M).

**Steps**:
1. Run T-Shirt Sizing on a specification containing an entity with Story Point value 8.
2. Inspect the entity's classification.

**Expected**: `tshirt_size == "L"`, `mapping_rule == "default: 8-13 → L"`.

### Scenario 2: Corrected Mapping — Value 40

**Purpose**: Verify that Story Point value 40 now maps to XL (not XXL).

**Steps**:
1. Run T-Shirt Sizing on a specification containing an entity with Story Point value 40.
2. Inspect the entity's classification.

**Expected**: `tshirt_size == "XL"`, `mapping_rule == "default: 20-40 → XL"`.

### Scenario 3: Full Mapping Coverage

**Purpose**: Verify all 9 Fibonacci values are covered across the 6 T-shirt sizes.

**Steps**:
1. Run T-Shirt Sizing on a specification with entities having Story Point values 1, 2, 3, 5, 8, 13, 20, 40, 100.
2. Collect all unique T-shirt sizes from the output.

**Expected**: All six sizes (XS, S, M, L, XL, XXL) appear. No `"UNKNOWN"` classifications. Each Fibonacci value maps to exactly one size.

### Scenario 4: measure.json Total

**Purpose**: Verify measure.json shows the correct total (not 0).

**Steps**:
1. Run a full pipeline on a specification with 10+ entities.
2. Open `.specmetrics/runs/<measure_id>/measure.json`.
3. Find the T-Shirt entry.

**Expected**: `"metric": "tshirt"`, `"total"` equals the number of entities classified (≥ 10), `"total" > 0`.

### Scenario 5: measure.json Breakdown

**Purpose**: Verify measure.json includes per-size counts.

**Steps**:
1. Run a full pipeline.
2. Inspect the T-Shirt entry's `breakdown` object.

**Expected**: `breakdown` contains entries for each size present, each with a `count` field. Sum of all `count` values equals the `total`.

### Scenario 6: metrics.json Unit and Fields

**Purpose**: Verify metrics.json uses `"entities"` unit and correct entity fields.

**Steps**:
1. Run a full pipeline.
2. Open `.specmetrics/runs/<measure_id>/metrics.json`.
3. Find the T-Shirt entry.

**Expected**:
- `"unit": "entities"`
- `"total"` equals entity count
- `"entities"` array has entries with `id`, `name`, `type`, `story_point_value`, `tshirt_size`, `mapping_rule`
- `"metadata"` contains `"scale"` and `"mapping"`

### Scenario 7: CLI Display

**Purpose**: Verify CLI output shows the correct total and breakdown.

**Steps**:
1. Run `specmetrics measure` on a specification.
2. Inspect the terminal output.

**Expected**: The T-Shirt line shows `TShirt: N entities` (not `TShirt: 0`). Below it, a breakdown line shows per-size counts.

### Scenario 8: No Story Points Edge Case

**Purpose**: Verify behavior when Story Points result is unavailable.

**Steps**:
1. Run T-Shirt Sizing without a preceding Story Points measurement.

**Expected**: `total: 0`, empty `breakdown`, warning with code `"NO_STORY_POINTS"`.

### Scenario 9: Custom Mapping Override

**Purpose**: Verify custom mapping support.

**Steps**:
1. Provide a custom mapping via pipeline metadata with 4 sizes (S: 1-3, M: 5-8, L: 13-20, XL: 40-100).
2. Run T-Shirt Sizing.

**Expected**: Classifications follow the custom mapping. Entity with SP=8 maps to "M" under custom mapping (even though the new default would map it to "L").

## Test Commands

```bash
# Run all T-Shirt unit tests
pytest tests/unit/test_tshirt_classifier.py tests/unit/test_tshirt_models.py -v

# Run contract tests
pytest tests/contract/test_tshirt_measurement.py -v

# Run integration tests
pytest tests/integration/test_tshirt_pipeline.py -v

# Full T-Shirt test suite
pytest tests/unit/test_tshirt_*.py \
       tests/contract/test_tshirt_measurement.py \
       tests/integration/test_tshirt_pipeline.py -v
```
