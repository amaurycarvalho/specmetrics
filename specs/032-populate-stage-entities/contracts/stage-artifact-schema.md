# Contract: Stage Artifact JSON Schema

## File Location

`.specmetrics/runs/<run_id>/<stage_name>.json`

Where `<run_id>` is the measure ID (timestamp-uuid format) and `<stage_name>` is one of: `discover`, `extract`, `graph`, `csm`, `cfm`, `rule`, `measure`, `export`.

## Top-Level Structure

```typescript
{
  /* Always present */
  name: string;          // Stage name matching filename
  count: number;         // Total entities (never truncated)
  count_type: string;    // "documents" | "items" | "metrics"
  duration_ms: number;   // Stage execution time

  /* Populated by this feature */
  entities: Entity[];    // Stage-specific entities

  /* Present only when truncation occurs */
  _truncated?: boolean;  // true if entities list was truncated
  _total_count?: number; // Actual total before truncation
}
```

## Entity Type Definitions

See [data-model.md](../data-model.md) for per-stage entity schemas including:
- Field types and descriptions
- Truncation strategy
- Optional vs required fields

## Versioning

- This schema is version 1.0.
- All new fields are additive — older consumers reading newer files will safely ignore unknown fields.
- The `entities` field was previously always `[]` — consumers already handle this.
- The `_truncated` and `_total_count` fields are additive.
- Schema changes are governed by the Evolution Without Disruption principle (Constitution XIII).

## Validation Rules

1. `count` MUST equal `entities.length` when `_truncated` is absent or `false`.
2. When `_truncated` is `true`, `count` MUST equal `_total_count` and `_total_count` MUST be greater than `entities.length`.
3. `_truncated` MUST be `true` when the original entity count exceeds `max_entities_per_stage`.
4. Entity `description` and `text` fields MUST NOT exceed 200 characters.
5. `duration_ms` MUST be 0 for skipped stages.
6. `count` MUST be 0 for skipped or failed stages.
7. Evidence references MUST contain at minimum `document_id` and `text`.
