# Data Model: OpenSpec Operation Extraction Rules

**Feature**: 035-openspec-operation-rules

## Entity Changes

No new entities, no schema changes, no code changes. This feature is a YAML-only modification.

### OpenSpec Rule (existing, semantic type corrected)

9 entries in `openspec_rules.yaml` change their `type` field from `"fact"` to `"operation"`. This is a data value change, not a schema change.

| Field | Change | Description |
|-------|--------|-------------|
| `type` | `"fact"` → `"operation"` | Semantic classification of the extracted element |

### Downstream Impact

The type change propagates through the existing pipeline without modification:

1. **Extraction**: `ExtractedElement.type = "operation"` (was `"fact"`)
2. **Graph**: `GraphNode.semantic_type = "operation"` (was `None` — facts were mapped to `business_rule`, see classifier)
3. **CFM Classifier**: `classify_node()` → `semantic_type == "operation"` → returns `"operation"` category
4. **CFM Builder**: Creates `Operation` entity with `metadata["direction"]` from `_infer_operation_direction()`
5. **Functional Process**: Operations grouped by document_id → `FunctionalProcess` with non-empty `operation_ids`
6. **Measurement**: FPA counts operations as EI/EO/EQ, Story Points iterates functional_processes

### State Transition (correction applied)

**Before** (fact-type rules):
```
Extraction → element.type="fact" → GraphNode.semantic_type=None → CFM classifier → "business_rule"
```

**After** (operation-type rules):
```
Extraction → element.type="operation" → GraphNode.semantic_type="operation" → CFM classifier → "operation"
```
