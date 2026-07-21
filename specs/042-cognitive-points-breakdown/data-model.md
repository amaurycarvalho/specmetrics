# Data Model: Cognitive Points Breakdown

**Feature**: 042-cognitive-points-breakdown

## Overview

No existing models are modified. One new payload key is added in the plugin, and one measure.json field format is extended. This is a purely additive change at the serialization layer.

---

## Payload Extension (plugin.py)

**File**: `specmetrics/plugins/measurement/cognitive_points/plugin.py`

### New Payload Key

| Key | Type | Description |
|-----|------|-------------|
| `cognitive_bloom_breakdown` | `dict[str, dict[str, float]]` | Per-Bloom-level score totals in the format `{level: {total: float}}` |

### Value Format

```python
# Example value for cognitive_bloom_breakdown:
{
    "remember": {"total": 120.0},
    "understand": {"total": 890.0},
    "apply": {"total": 2345.0},
    "analyze": {"total": 4560.0},
    "evaluate": {"total": 7890.5},
    "create": {"total": 28669.0},
}
```

- Only levels with non-zero total appear.
- The dict is built from the `all_cognitive_contributions` list by grouping on `bloom_level` and summing `partial_score`.
- Order follows Bloom taxonomy cognitive complexity: remember, understand, apply, analyze, evaluate, create.

### Computation

Inserted in `handle()` after line 66 (after `cognitive_entities` is computed):

```python
bloom_breakdown: dict[str, float] = {}
for c in all_cognitive_contributions:
    level = c.bloom_level
    bloom_breakdown[level] = bloom_breakdown.get(level, 0.0) + c.partial_score

# Wrap into measure.json format and ensure canonical order
bloom_levels = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
cognitive_bloom_breakdown = {
    level: {"total": bloom_breakdown[level]}
    for level in bloom_levels
    if bloom_breakdown.get(level, 0.0) > 0
}
```

### Validation

- Sum of all `total` values in `cognitive_bloom_breakdown` MUST equal `cognitive_raw_score` (within floating-point tolerance of 0.01).
- This is guaranteed by the computation: summing `partial_score` across all contributions by definition equals `raw_score`.

---

## measure.json Output Extension (orchestrator.py)

**File**: `specmetrics/application/orchestrator.py`

### key_map Change

| Metric | Old key_map | New key_map |
|--------|------------|-------------|
| `cognitive_points` | `("cognitive_raw_score", None)` | `("cognitive_raw_score", "cognitive_bloom_breakdown")` |

### Output Format

The existing breakdown logic (lines 619-620) adds the payload value to the entry unchanged:

```json
{
  "metric": "cognitive_points",
  "total": 44474.5,
  "status": "completed",
  "duration_ms": 0,
  "breakdown": {
    "remember": {"total": 120.0},
    "understand": {"total": 890.0},
    "apply": {"total": 2345.0},
    "analyze": {"total": 4560.0},
    "evaluate": {"total": 7890.5},
    "create": {"total": 28669.0}
  }
}
```

When `cognitive_bloom_breakdown` is empty (no elements), the `breakdown` field is absent (no empty dict emitted, maintaining the existing pattern).

---

## CLI Display Extension (formatters.py)

**File**: `specmetrics/cli/formatters.py`

### New Display Block

After the Cognitive Points total line (currently line 41), add a breakdown display block following the tshirt breakdown pattern:

```python
if mr.name == "cognitive_points" and result.measurement_result_raw:
    cp_breakdown = result.measurement_result_raw.get("cognitive_bloom_breakdown")
    if isinstance(cp_breakdown, dict) and cp_breakdown:
        for level_name, level_data in cp_breakdown.items():
            if isinstance(level_data, dict):
                total = level_data.get("total", 0)
            else:
                total = level_data
            lines.append(f"    {level_name.title()}: {total}")
```

### Display Format

```
Cognitive Points: 44474.5
    Remember: 120.0
    Understand: 890.0
    Apply: 2345.0
    Analyze: 4560.0
    Evaluate: 7890.5
    Create: 28669.0
```

### Edge Cases

| Case | Behavior |
|------|----------|
| Empty dict (`{}`) | No lines output |
| Missing key | No lines output (backward compatible with pre-feature payloads) |
| Single level present | One indented line |
| `level_data` is a plain float (not dict) | `total = level_data` (robust against format variations) |
