# Research: Cognitive Points Breakdown

**Feature**: 042-cognitive-points-breakdown
**Date**: 2026-07-21

## Research Task 1: Contribution List Assembly Point

### Finding

In `specmetrics/plugins/measurement/cognitive_points/plugin.py`, the `handle()` method (line 33) already assembles `all_cognitive_contributions` by concatenating spec and func contribution lists:

```python
all_cognitive_contributions = (
    result.specification_review_effort.contributions
    + result.functional_validation_effort.contributions
)
```

Each `CognitiveContribution` has `bloom_level: str` and `partial_score: float`. The breakdown can be computed immediately after this line by grouping contributions by `bloom_level` and summing `partial_score`. No additional data needs to be fetched or transformed.

### Decision

Compute `cognitive_bloom_breakdown` inline in `handle()` using a simple aggregation loop over `all_cognitive_contributions`. This is O(n) and runs on data already in memory.

### Alternatives Considered

- **Compute in the calculator**: Rejected — would require modifying the `CognitivePointsMeasurement` model or the `calculate()` return value. Adding a new field to the measurement model is heavier than adding a payload key computed from existing data.
- **Compute in orchestrator from cognitive_entities list**: Rejected — the orchestrator should not know about CognitiveContribution internals. The aggregation is properly scoped to the plugin.

---

## Research Task 2: Orchestrator measure.json Mapping

### Finding

In `specmetrics/application/orchestrator.py`, the `_build_stage_entities()` method (around line 590) builds the measure stage entries. The `key_map` for cognitive_points is currently:

```python
"cognitive_points": ("cognitive_raw_score", None),
```

The second tuple element (`None`) means no breakdown key. The existing pattern for metrics with breakdown is:

```python
"tshirt": ("tshirt", "tshirt_breakdown"),
"function_points": ("fpa_total_function_points", "fpa_breakdown"),
```

Lines 619-620 check if the breakdown key exists in the payload and add it to the entry:

```python
if breakdown_key and breakdown_key in mr:
    entry["breakdown"] = mr[breakdown_key]
```

The `cognitive_raw_score` is used for the total field. The breakdown key should map to `cognitive_bloom_breakdown`.

### Decision

Change the cognitive_points entry in key_map from `("cognitive_raw_score", None)` to `("cognitive_raw_score", "cognitive_bloom_breakdown")`. The existing breakdown-adding logic (lines 619-620) will automatically include the breakdown if present in the payload.

The payload value is a flat `dict[str, float]` (e.g., `{"understand": 890.0}`). For the measure.json format requested by the user, this needs to be wrapped into `{level: {total: value}}`. The wrapping is done in the orchestrator to keep the payload format simple. Alternatively, the payload could emit the nested format directly.

**Decision update**: Since the wrapping logic in the orchestrator currently passes the payload value through as-is, the plugin should emit the breakdown in the requested measure.json format directly: `{"understand": {"total": 890.0}}`. This avoids adding transformation logic in the orchestrator and keeps the payload consistent with how the data should appear.

### Alternatives Considered

- **Emit flat dict and wrap in orchestrator**: Would require modifying orchestrator logic for this one metric, breaking the generic pass-through pattern.
- **Emit nested format from plugin**: Cleaner. The plugin owns its output format. Chosen approach.

---

## Research Task 3: CLI Formatter Pattern for Breakdowns

### Finding

In `specmetrics/cli/formatters.py`, the `format_text_result()` function already displays breakdowns for two metrics using `result.measurement_result_raw`:

1. **TShirt** (lines 43-51): Reads `tshirt_breakdown` dict and formats as inline `S: N  M: N ...` pattern.
2. **Function Points** (lines 53-67): Reads from `result.measurement.breakdown` (a MeasurementResult model field, older pattern).

For Cognitive Points, the breakdown should follow the Function Points pattern of indented lines, but use a simpler format without tree characters:

```
Cognitive Points: 44474.5
  Understand: 890
  Apply: 1500
```

The data is read from `result.measurement_result_raw`, which is the `measurement_result` dict from the pipeline context. The key `cognitive_bloom_breakdown` will be available there.

### Decision

Add a new block in `format_text_result()` after the cognitive points display line (around line 41), checking `result.measurement_result_raw` for `cognitive_bloom_breakdown`. If present and non-empty, iterate over the dict and output indented lines.

The Bloom levels should be displayed in cognitive complexity order: Remember, Understand, Apply, Analyze, Evaluate, Create. Since the payload dict uses this insertion order (plugin controls it), the natural iteration order is correct.

The display uses capitalized level names. A simple mapping or `str.capitalize()` / `str.title()` is sufficient since all bloom level names are single words in lowercase.

### Alternatives Considered

- **Add to MeasurementResult model**: Over-engineering for a display concern. The `measurement_result_raw` pattern is already established (tshirt breakdown uses it) and requires no model changes.
- **Use tree characters**: The Function Points breakdown uses `├─` to indicate hierarchical sub-breakdown (EI, EO, EQ are sub-types of FP). Cognitive Points bloom levels are siblings, not children. Simple indentation is clearer.

---

## Research Task 4: Bloom Level Display Order

### Finding

The Bloom taxonomy has a well-known hierarchy from lowest to highest cognitive complexity:

1. Remember (1.0)
2. Understand (2.0)
3. Apply (3.0)
4. Analyze (4.0)
5. Evaluate (5.0)
6. Create (8.0)

The `cognitive_bloom_distribution` dict in the payload uses whatever insertion order the calculator produces. The `BloomClassifier._DEFAULT_BLOOM_WEIGHTS` dict (in `bloom_classifier.py`) defines weights in this order already.

### Decision

The plugin should insert levels into `cognitive_bloom_breakdown` in the standard cognitive complexity order (remember → create). This ensures both the payload dict and the CLI display use this natural ordering. The dict is constructed by iterating over the canonical level list rather than relying on arbitrary dict iteration order from the aggregation.

### Alternatives Considered

- **Alphabetical order**: Rejected — loses the cognitive meaning of the taxonomy.
- **By total score descending**: Rejected — inconsistent across runs; harder to compare.
- **By weight ascending**: Same as cognitive complexity order since weights are monotonically increasing. Chosen implicitly.
