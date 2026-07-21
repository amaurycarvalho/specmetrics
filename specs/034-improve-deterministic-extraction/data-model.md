# Data Model: Deterministic Extraction Improvements

**Feature**: 034-improve-deterministic-extraction

## Entity Changes

### Operation (existing, now populated by deterministic engine)

Previously only populated by LLM extraction. Now produced by deterministic rules.

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `id` | str | — | Node ID from evidence graph |
| `name` | str | — | Cleaned element text |
| `description` | str | — | Original element text |
| `parent_process_id` | str | — | Set during CFM build |
| `evidence` | EvidenceRef | — | Source document reference |
| `metadata.direction` | str | — | "input" (GIVEN/WHEN), "output" (THEN), "query" (Scenario) |

### FunctionalProcess (existing, now built from deterministic operations)

Previously only built when LLM-extracted operations existed. Now built for any document containing operation elements.

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `id` | str | — | `fp_{document_id}` |
| `name` | str | — | `"Functional Process — {document_id}"` |
| `operation_ids` | list[str] | **New population** | Operation IDs grouped by document |
| `data_group_ids` | list[str] | **New population** | Data group IDs from same document |
| `actor_ids` | list[str] | **New population** | Actor IDs from same document |
| `evidence` | EvidenceRef | — | Derived from first operation's evidence |

### Actor (existing, improved classification)

Previously all entities classified as data_group. Now some entities correctly classified as actors.

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `id` | str | — | Node ID from evidence graph |
| `name` | str | — | Cleaned entity name |
| `actor_type` | str | — | Default "role" |
| `evidence` | EvidenceRef | — | Source document reference |

### semantic_marker metadata (new metadata field on all CFM elements)

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `metadata.semantic_marker` | str | **New** | One of: `presentation_interface`, `data_operation`, `operational_feature`, `technical_interface` |

### Rule Pack Changes (YAML, no code schema change)

| Rule ID | File | Change |
|---------|------|--------|
| `gwt-given-operation` | `default_rule_pack.yaml` | **New** — keyword match for `**GIVEN**` / `**Given**` |
| `gwt-when-operation` | `default_rule_pack.yaml` | **New** — keyword match for `**WHEN**` / `**When**` |
| `gwt-then-operation` | `default_rule_pack.yaml` | **New** — keyword match for `**THEN**` / `**Then**` |
| `speckit-gwt-numbered` | `speckit_rules.yaml` | **Changed** — `type: "fact"` → `type: "operation"` |
| `speckit-gwt-multiline-given` | `speckit_rules.yaml` | **Changed** — `type: "fact"` → `type: "operation"` |
| `speckit-gwt-multiline-when` | `speckit_rules.yaml` | **Changed** — `type: "fact"` → `type: "operation"` |
| `speckit-gwt-multiline-then` | `speckit_rules.yaml` | **Changed** — `type: "fact"` → `type: "operation"` |

## State Transitions

No new state machines. Existing flow:

1. **Extraction**: Markdown document → rules match → `ExtractedElement` with `type="operation"` or `type="entity"`
2. **Graph**: `ExtractedElement` → `GraphNode` with `semantic_type="operation"` or `"entity"`
3. **CFM Build**: `GraphNode` → `Operation` or `Actor`/`DataGroup` with `semantic_marker` metadata
4. **Measurement**: `Operation` → `FunctionalProcess` → `MeasuredFunction` (FPA) / `FunctionalWorkItem` (Story Points)
