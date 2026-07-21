# Research: T-Shirt Sizing Improvements

**Feature**: 041-tshirt-sizing  
**Date**: 2026-07-21

## 1. Mapping Table Correction

**Decision**: Update `DEFAULT_MAPPING` in `classifier.py` to: XS=[1], S=[2,3], M=[5], L=[8,13], XL=[20,40], XXL=[100].

**Rationale**: The current mapping (M=[5,8], L=[13], XL=[20], XXL=[40,100]) creates uneven groupings. Story Point value 8 grouped with 5 in M is misleading — 8 is 60% larger than 5 in the Fibonacci scale. Similarly, 40 grouped with 100 in XXL makes XXL cover a 2.5x range. The corrected mapping distributes 9 Fibonacci values into 6 buckets with proportional groupings: XS/S cover the small end (1-3), M is the midpoint (5), L covers the moderate range (8-13), XL covers large (20-40), and XXL is the extreme (100).

**Alternatives considered**:
- 1-1-1-1-1 mapping (each Fibonacci value gets its own T-shirt size): rejected — would require 9 T-shirt sizes instead of 6, and the user explicitly defined the 6-size mapping.
- Weighted proportional mapping: rejected — T-shirt sizes are ordinal categories, not continuous values. Simple integer ranges are sufficient.

## 2. measure.json Payload Key Fix

**Decision**: Add a `tshirt` top-level key to the T-Shirt handler's payload with the total entity count value. Additionally add a `tshirt_breakdown` key with the per-size distribution.

**Current problem**: The orchestrator's `_build_stage_entities()` (line 594-605 in `orchestrator.py`) maps `"tshirt": ("tshirt", None)` — it reads `mr.get("tshirt")` from the measurement result dict to get the total. But the T-Shirt handler's `_finalize()` only writes `"total_items"` and `"distribution"` keys, never `"tshirt"`. Hence the orchestrator gets `None` → `0`.

**Solution**: In `TShirtHandler._finalize()`, add to the payload dict:
```python
"tshirt": result.total_items,
"tshirt_breakdown": {k: {"count": v} for k, v in result.distribution.items()},
```

This ensures the orchestrator finds the `"tshirt"` key and reads the correct total. The `tshirt_breakdown` key provides the structured breakdown needed for `measure.json`.

**Alternatives considered**:
- Change the orchestrator key map to `"tshirt": ("tshirt_total_items", None)`: rejected — breaks the convention used by all other metrics (`fpa_total_function_points`, `storypoints_total_story_points`, etc. where the key name matches the metric name).
- Have T-Shirt emit the `MEASUREMENT_COMPLETED` event like other metrics: rejected — T-Shirt depends on Story Points completing first, so it needs its own later event.

## 3. metrics.json Entity Fields Update

**Decision**: Update `metrics_json.py` `build_tshirt_entity()` to populate all six required fields (`id`, `name`, `type`, `story_point_value`, `tshirt_size`, `mapping_rule`) and change `METRIC_UNIT_MAP["tshirt"]` from `"story_points"` to `"entities"`.

**Current implementation**: `build_tshirt_entity()` (line 242-257) reads `element_id`, `element_name`, maps `story_point_value` to a `score` field, and includes `tshirt_size` and `mapping_rule` in metadata. The entity `type` is hardcoded to `"functional_process"`. The unit is `"story_points"`.

**Solution**:
- Change `METRIC_UNIT_MAP["tshirt"]` to `"entities"`
- Update `build_tshirt_entity()` to include `story_point_value` as a direct field (not just `score`), use the actual element type from the source data, and ensure `tshirt_size` is a top-level field.
- Update `_build_metric_metadata()` for tshirt to return the scale and mapping object.

**Rationale**: The total is an entity count, not a Story Points sum. `"entities"` accurately describes the unit.

**Alternatives considered**:
- Keep `"story_points"` unit: rejected — the T-shirt total is not a Story Point sum; it's a count of classified entities.

## 4. CLI Display Fix

**Decision**: Update `format_text_result()` in `cli/formatters.py` to read the correct tshirt total key from `metric_results` and render the breakdown line.

**Current problem**: The formatter reads `metric_results` and for each metric looks up the total. For tshirt, the orchestrator's `_build_metric_results()` returns whatever `mr.get("tshirt")` resolves to — currently 0 because the key is missing.

**Solution**: Once the payload fix (#2 above) is in place, the orchestrator correctly reads the tshirt total. The formatter then needs to also render the breakdown line from `tshirt_breakdown` if available. Add special handling: if a metric has a `breakdown` key in its result, render it as a sub-line.

**Alternatives considered**:
- Generic breakdown rendering for all metrics: considered but rejected — only T-Shirt has a categorical breakdown by design. Other metrics use continuous scores.

## 5. Orchestrator Key Mapping Fix

**Decision**: In `orchestrator.py`, add `"tshirt_breakdown"` to the tshirt entry in `_build_stage_entities()` key_map so the breakdown is passed to `measure.json`.

**Current code**: `"tshirt": ("tshirt", None)` — only reads total. The second tuple element (breakdown key) is `None`.

**Solution**: Change to `"tshirt": ("tshirt", "tshirt_breakdown")` so the measure.json stage entity includes both total and breakdown.

## 6. RFC Documentation

**Decision**: Create `docs/rfcs/RFC-042 - T-Shirt Sizing.md` following the pattern established by existing RFCs (RFC-028 Token Points, RFC-029 Cognitive Points, RFC-041 Story Points).

**Decision on number**: 042 is the next available after 041 (Story Points).

**Sections**: Methodology overview, relationship to Story Points, mapping table with rationale, output format specifications (measure.json, metrics.json, CLI), calibration/customization, cross-specification comparison guidance, Kanban usage appendix.
