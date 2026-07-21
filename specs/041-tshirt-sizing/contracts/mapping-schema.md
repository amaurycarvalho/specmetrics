# Contract: T-Shirt Mapping Configuration

**Feature**: 041-tshirt-sizing  
**Format**: Python list of `TShirtSize` dicts (passed via pipeline metadata or direct API)  

## Schema

A mapping is an ordered list of size definitions. Each entry defines one T-shirt size and the range of Story Point values it covers.

```
[
  {
    "label": "XS",                # T-shirt size label (unique within mapping)
    "story_point_range": [1, 1],  # [min, max] inclusive Story Point range
    "ordinal": 1                   # Ordinal position for sorting (1-based)
  },
  ...
]
```

## Default Mapping (updated)

```json
[
  { "label": "XS",  "story_point_range": [1, 1],   "ordinal": 1 },
  { "label": "S",   "story_point_range": [2, 3],   "ordinal": 2 },
  { "label": "M",   "story_point_range": [5, 5],   "ordinal": 3 },
  { "label": "L",   "story_point_range": [8, 13],  "ordinal": 4 },
  { "label": "XL",  "story_point_range": [20, 40], "ordinal": 5 },
  { "label": "XXL", "story_point_range": [100, 100], "ordinal": 6 }
]
```

## Mapping Coverage

| Story Point Value | Mapped Size | Previous Size |
|---|---|---|
| 1 | XS | XS (unchanged) |
| 2 | S | S (unchanged) |
| 3 | S | S (unchanged) |
| 5 | **M** | M (unchanged) |
| 8 | **L** | M (was M) |
| 13 | **L** | L (unchanged) |
| 20 | **XL** | XL (unchanged) |
| 40 | **XL** | XXL (was XXL) |
| 100 | **XXL** | XXL (unchanged) |

Two values change classification: 8 moves from M → L, 40 moves from XXL → XL.

## Validation Rules

1. The list must contain at least 1 entry
2. All `label` values must be unique within the mapping
3. For each entry: `story_point_range[0] <= story_point_range[1]`
4. Ranges must not overlap: for consecutive entries (sorted by min), `entry[i].max < entry[i+1].min`
5. `ordinal` values should be unique and sequential starting from 1

## Custom Mapping Support

Users can provide an alternative mapping via pipeline metadata. Example of a custom mapping with only 4 sizes:

```json
[
  { "label": "S",   "story_point_range": [1, 3],   "ordinal": 1 },
  { "label": "M",   "story_point_range": [5, 8],   "ordinal": 2 },
  { "label": "L",   "story_point_range": [13, 20], "ordinal": 3 },
  { "label": "XL",  "story_point_range": [40, 100], "ordinal": 4 }
]
```

Custom mappings must still pass all validation rules. Unknown labels are allowed. The default mapping is used when no override is provided.

## Classifier Contract

```
classify(story_point_value: int) -> tuple[str, str]
```

- **Input**: A normalized Story Point value (integer)
- **Output**: A tuple of `(size_label, mapping_rule)`
  - `size_label`: The T-shirt size label (e.g., "L") or "UNKNOWN" if no range matches
  - `mapping_rule`: Human-readable rule string (e.g., `"default: 8-13 → L"`)
- **Behavior**: Iterates mapping entries in order, returns the first entry whose range contains the input value
- **Determinism**: Same input + same mapping → always same output
