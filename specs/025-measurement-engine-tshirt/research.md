# Research: T-Shirt Sizing Measurement Engine

## 1. Plugin Architecture

**Decision**: Minimal plugin with 4 source files — `plugin.py`, `models.py`, `classifier.py`, `explainer.py`. No calculator, scorer, or normalizer needed since classification is a simple lookup.

**Rationale**: T-Shirt Sizing is a derived/presentation layer over Story Points. It does no independent estimation (FR-013). The entire algorithm is: read SP value → look up in mapping table → emit classification.

**Alternatives considered**: Reusing Story Points plugin with a configuration flag — rejected because T-Shirt is a separate measurement methodology with its own event type, pipeline slot, and output format.

---

## 2. Classification Algorithm

**Decision**: Ordered threshold-based lookup. Story Point values are compared against ascending thresholds derived from the mapping table. O(1) per item.

**Default mapping** (from FR-015):

| SP Range | Size | Sort Ordinal |
|----------|------|-------------|
| 1        | XS   | 1 |
| 2–3      | S    | 2 |
| 5–8      | M    | 3 |
| 13       | L    | 4 |
| 20       | XL   | 5 |
| 40–100   | XXL  | 6 |

**Algorithm**: Store mapping as list of `(min_sp, max_sp, size_label, ordinal)`. For each Story Point value, find the first range where `min_sp <= value <= max_sp`. Return the corresponding size. If no range matches (shouldn't happen with valid config), assign default size and emit warning.

**Validation** (FR-019, FR-020): On load, validate that:
- Every SP value 1–100 maps to exactly one range (no gaps, no overlaps)
- Each range is non-empty (min ≤ max)
- All size labels are non-empty and unique

**Alternatives considered**: Continuous formula `size = index(round(raw_score / bucket_width))` — rejected because explicit ranges support irregular mappings (e.g., SP=1 maps to XS but SP=2–3 maps to S).

---

## 3. Pipeline Integration

**Decision**: New `EventType.TSHIRT_CLASSIFICATION_COMPLETED` in `CANONICAL_EVENT_ORDER` after `MEASUREMENT_COMPLETED`. T-Shirt handler subscribes to this event, reads `ctx.measurement_result` (set by Story Points), classifies, writes its own result.

**CANONICAL_EVENT_ORDER update**:
```python
CANONICAL_EVENT_ORDER = [
    ...
    EventType.MEASUREMENT_COMPLETED,                 # Story Points runs here
    EventType.TSHIRT_CLASSIFICATION_COMPLETED,        # T-Shirt runs here (new)
    EventType.EXPORT_COMPLETED,
    ...
]
```

**Handler flow**:
1. Read `ctx.measurement_result` — expects StoryPoints format
2. If None or not SP format → return empty result with warnings (graceful degradation)
3. Extract `items` list from SP result → look up each SP value in mapping table
4. Build distribution and evidence chain
5. Write `ctx.with_stage_output("measurement_result", payload)`

**No additional PipelineContext field needed** — reuses `measurement_result` since T-Shirt is the last measurement to run.

---

## 4. Rule Pack Customization

**Decision**: Rule Packs can redefine the mapping table (size labels and SP ranges) per FR-021/FR-022. The classifier reads overrides from the annotated CFM or calibration context.

**Override mechanism**: Rule Pack provides a new mapping table that completely replaces the default (not a merge — FR-019 warns that overlapping with defaults is an error). The classifier validates the override table before use.

**Example Rule Pack override** (5-level scale):
```yaml
tshirt_mapping:
  - size: XS
    range: [1, 2]
  - size: S
    range: [3, 5]
  - size: M
    range: [8, 13]
  - size: L
    range: [20, 40]
  - size: XL
    range: [100, 100]
```

---

## 5. Explainability

**Decision**: Each FunctionalWorkItem carries its SP value, the mapping rule that produced its size, and evidence refs. The distribution aggregates counts per size.

**Report structure**:
```json
{
  "method": "TShirtSizing",
  "scale": "XS-S-M-L-XL-XXL",
  "total_items": 37,
  "items": [
    {
      "element_id": "fp-001",
      "element_name": "Process Order",
      "story_point_value": 8,
      "tshirt_size": "M",
      "mapping_rule": "default: 5-8 → M",
      "evidence_refs": [{"element_id": "fp-001", "story_point_value": 8}]
    }
  ],
  "distribution": {"XS": 3, "S": 8, "M": 14, "L": 7, "XL": 3, "XXL": 2},
  "execution_metadata": {"duration_ms": 2.1, "version": "1.0"}
}
```

---

## 6. Infrastructure Changes

**Decision**: Two existing files modified:

1. `specmetrics/kernel/events.py` — add to `EventType` enum:
   ```python
   TSHIRT_CLASSIFICATION_COMPLETED = "tshirt_classification_completed"
   ```

2. `specmetrics/kernel/pipeline_engine.py` — add to `CANONICAL_EVENT_ORDER`:
   ```python
   EventType.MEASUREMENT_COMPLETED,
   EventType.TSHIRT_CLASSIFICATION_COMPLETED,   # new
   EventType.EXPORT_COMPLETED,
   ```
