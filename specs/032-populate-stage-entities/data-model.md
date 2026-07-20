# Data Model: Stage Entities for Run Artifacts

## Overview

This document defines the data structures used to carry per-stage entity data from pipeline execution to JSON artifact serialization. All entity schemas below represent the JSON structure written to `.specmetrics/runs/<run_id>/<stage>.json`.

## PipelineResult Extension

### `stage_entities: dict[str, list[dict]]`

A new field on `PipelineResult` mapping stage name to its entity list:

```python
@dataclass
class PipelineResult:
    # ... existing fields ...
    stage_entities: dict[str, list[dict]] = field(default_factory=dict)
```

Each entry is keyed by stage name (`"discover"`, `"extract"`, `"graph"`, `"csm"`, `"cfm"`, `"rule"`, `"measure"`, `"export"`).

## Configuration Model

### `RunArtifactsSettings`

Added to `CoreConfig` in `specmetrics/infrastructure/config/schema.py`:

```python
class RunArtifactsSettings(BaseModel):
    max_entities_per_stage: int = 5000
```

Available in config.yml as:
```yaml
run_artifacts:
  max_entities_per_stage: 5000
```

## Per-Stage Entity Schemas

### Discover Stage — `discover.json`

```json
{
  "name": "discover",
  "count": 244,
  "count_type": "documents",
  "duration_ms": 356,
  "entities": [
    {
      "id": "uuid-v4",
      "document_type": "sdd",
      "path": "specs/auth/spec.md"
    }
  ]
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Document UUID from adapter |
| `document_type` | string | Adapter-reported type (`sdd`, `openspec`, `markdown`) |
| `path` | string | Relative path from project root |

**Truncation**: First N entities overall.

---

### Extract Stage — `extract.json`

```json
{
  "name": "extract",
  "count": 1077,
  "count_type": "items",
  "duration_ms": 8402,
  "entities": [
    {
      "id": "uuid-v4",
      "type": "constraint",
      "content": "the system MUST validate user identity before...",
      "confidence": 0.95,
      "evidence": {
        "document_id": "speckit:auth:spec.md",
        "section_id": "sec-3.1",
        "text": "the system MUST validate user identity..."
      }
    }
  ]
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Extracted element UUID |
| `type` | string | One of: `fact`, `entity`, `relationship`, `operation` |
| `content` | string | First 200 characters of element content |
| `confidence` | float | Confidence score (0.0–1.0) |
| `evidence` | object | `{ document_id, section_id, text }` with `text` truncated to 200 chars |

**Truncation**: First N entities overall.

---

### Graph Stage — `graph.json`

```json
{
  "name": "graph",
  "count": 1916,
  "count_type": "items",
  "duration_ms": 175,
  "entities": [
    {
      "id": "uuid-v4",
      "node_type": "extracted_element",
      "semantic_type": "entity",
      "document_id": "speckit:auth:spec.md",
      "section_id": null,
      "text": "SpecMetrics"
    },
    {
      "node_type": "graph_summary",
      "edge_count": 958,
      "run_id": "20260720-141815-8803cdf8"
    }
  ]
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `id` | string (opt) | Node UUID (absent for summary entity) |
| `node_type` | string | `extracted_element`, `evidence`, or `graph_summary` |
| `semantic_type` | string (opt) | `fact`, `entity`, `relationship`, `operation` |
| `document_id` | string (opt) | Source document identifier |
| `section_id` | string (opt) | Section within document |
| `text` | string (opt) | Node text, first 200 chars |
| `edge_count` | int (summary) | Total edges in graph |
| `run_id` | string (summary) | Pipeline run identifier |

**Truncation**: First N entities overall (graph nodes); summary entity is always appended last.

---

### CSM Stage — `csm.json`

```json
{
  "name": "csm",
  "count": 960,
  "count_type": "items",
  "duration_ms": 614,
  "entities": [
    {
      "type": "decision",
      "id": "uuid-v4",
      "description": "Use JWT tokens for API authentication...",
      "evidence_references": [
        {
          "graph_node_id": "uuid-v4",
          "document_id": "speckit:auth:spec.md",
          "section_id": "sec-4.2",
          "text": "decided to use JWT tokens..."
        }
      ],
      "status": "active",
      "rationale": "Industry standard, stateless verification"
    },
    {
      "type": "constraint",
      "id": "uuid-v4",
      "description": "System must handle 10k concurrent...",
      "evidence_references": [
        {
          "graph_node_id": "uuid-v4",
          "document_id": "speckit:perf:spec.md",
          "section_id": "sec-2.1",
          "text": "System MUST support at least 10k..."
        }
      ],
      "status": "active",
      "constraint_type": "technical"
    }
  ]
}
```

**Fields** (per CSM category):

| CSM Category | Extra Fields |
|---|---|
| `specification_activity` | `activity_type`, `activity_status`, `linked_decisions` |
| `decision` | `rationale`, `alternatives`, `timestamp` |
| `assumption` | `validated_date` |
| `constraint` | `constraint_type` (regulatory/technical/organizational), `source` |
| `risk` | `probability`, `impact`, `mitigation` |
| `open_question` | `resolved`, `resolution` |
| `acceptance_criterion` | `verification_method` (test/review/inspection) |
| `glossary_term` | `aliases` |
| `reference` | `original_label` |

**Common fields**: `id` (string), `description` (first 200 chars), `evidence_references` (list of `{ graph_node_id, document_id, section_id, text }`), `status` (active/superseded).

**Truncation**: First N entities per category (e.g., first 5000 decisions, first 5000 constraints, etc.).

---

### CFM Stage — `cfm.json`

```json
{
  "name": "cfm",
  "count": 960,
  "count_type": "items",
  "duration_ms": 123,
  "entities": [
    {
      "type": "actor",
      "id": "uuid-v4",
      "name": "AuthenticationService",
      "actor_type": "system",
      "evidence": {
        "graph_node_id": "uuid-v4",
        "document_id": "speckit:auth:spec.md",
        "section_id": "sec-1.2",
        "text": "AuthenticationService is responsible for..."
      }
    },
    {
      "type": "business_rule",
      "id": "uuid-v4",
      "name": "PasswordValidationRule",
      "description": "Password must contain at least 8 characters...",
      "rule_type": "constraint",
      "evidence": { "...": "..." }
    },
    {
      "type": "data_group",
      "id": "uuid-v4",
      "name": "UserAccount",
      "data_type": "internal",
      "evidence": { "...": "..." }
    }
  ]
}
```

**Fields** (per CFM category):

| CFM Category | Extra Fields |
|---|---|
| `actor` | `name`, `actor_type` (person/system/role) |
| `functional_process` | `name`, `description`, `actor_ids`, `operation_ids` |
| `business_rule` | `name`, `description`, `rule_type` (constraint/condition/policy/derivation) |
| `data_group` | `name`, `description`, `data_type` (internal/external/shared) |
| `operation` | `name`, `description`, `parent_process_id` |
| `relationship` | `source_id`, `target_id`, `relationship_type` |
| `unclassified` | `original_type`, `content` |

**Common fields**: `id` (string), `name` (string), `evidence` (single `{ graph_node_id, document_id, section_id, text }`).

**Truncation**: First N entities per category.

---

### Rule Stage — `rule.json`

```json
{
  "name": "rule",
  "count": 960,
  "count_type": "items",
  "duration_ms": 19,
  "entities": [
    {
      "type": "applied_rule_pack",
      "rule_pack_name": "org-banking-rules",
      "description": "Banking domain adaptations for FPA counting",
      "version": "1.2.0"
    },
    {
      "type": "modification_summary",
      "entities_modified": 12,
      "vaf_applied": 1.08
    }
  ]
}
```

**Fields**:

| Entity Type | Fields |
|---|---|
| `applied_rule_pack` | `rule_pack_name`, `description`, `version` |
| `modification_summary` | `entities_modified` (int), `vaf_applied` (float) |

**Truncation**: First N entities overall.

---

### Measure Stage — `measure.json`

```json
{
  "name": "measure",
  "count": 8,
  "count_type": "metrics",
  "duration_ms": 110,
  "entities": [
    {
      "metric": "function_points",
      "total": 45,
      "status": "completed",
      "duration_ms": 15,
      "breakdown": {
        "external_inputs": { "low": 3, "average": 5, "high": 0, "total_ufp": 15 },
        "external_outputs": { "low": 2, "average": 3, "high": 1, "total_ufp": 12 },
        "external_inquiries": { "low": 1, "average": 0, "high": 0, "total_ufp": 3 },
        "internal_logical_files": { "low": 0, "average": 2, "high": 1, "total_ufp": 10 },
        "external_interface_files": { "low": 1, "average": 0, "high": 0, "total_ufp": 5 }
      }
    }
  ]
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `metric` | string | Metric name (e.g., `function_points`) |
| `total` | int | Total score |
| `status` | string | `completed`, `skipped`, `failed` |
| `duration_ms` | int | Duration in milliseconds |
| `breakdown` | object (opt) | Per-complexity or per-function breakdown (metric-specific) |

**Truncation**: Not applicable — metrics count is bounded by the number of measurement plugins.

---

### Export Stage — `export.json`

```json
{
  "name": "export",
  "count": 3,
  "count_type": "items",
  "duration_ms": 45,
  "entities": [
    {
      "format": "json",
      "path": ".specmetrics/output/specmetrics-output.json"
    },
    {
      "format": "csv",
      "path": ".specmetrics/output/specmetrics-output.csv"
    }
  ]
}
```

**Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `format` | string | Export format (`json`, `csv`, `xml`) |
| `path` | string | Relative path from project root |

**Truncation**: First N entities overall.

## Truncation Behavior

When `entities` exceeds the configured limit (default 5000):

```json
{
  "name": "extract",
  "count": 15500,
  "count_type": "items",
  "duration_ms": 12000,
  "entities": [ /* first 5000 elements */ ],
  "_truncated": true,
  "_total_count": 15500
}
```

- `count` always reflects the full total.
- For CSM/CFM: truncation is per-category, so each category gets its first N entries.
- `_truncated` and `_total_count` are appended after the `entities` array in the JSON file structure.

## State Transitions

Entity data flows through:

```
PipelineContext
  ├── adapter_result         → discover entities (dict construction)
  ├── extraction_result      → extract entities (dict construction)
  ├── evidence_graph         → graph entities (node iteration)
  ├── canonical_spec_model   → csm entities (model_dump per category)
  ├── canonical_model        → cfm entities (model_dump per category)
  │                          → rule entities (metadata read)
  ├── measurement_result     → measure entities (dict extraction)
  └── exported_files         → export entities (path iteration)
         │
         ▼
  build_stage_entities()     ← new method in orchestrator
         │
         ▼
  PipelineResult.stage_entities
         │
         ▼
  _serialize_stage_data()     ← modified to read from stage_entities
         │
         ▼
  .specmetrics/runs/<id>/*.json
```
