# Data Model: Measure Metrics Breakdown

**Feature**: 036-measure-metrics-breakdown

## Overview

The `metrics.json` file is a JSON array of `MetricBreakdownEntry` objects, one per executed metric. Each entry contains aggregated totals plus an `entities` array of `EntityScore` objects with the uniform schema.

## Canonical Entity Type Vocabulary

```text
data_group              operation               functional_process
specification_activity  business_rule           actor
relationship            decision                assumption
constraint              risk                    open_question
acceptance_criteria     glossary_term
```

All metrics MUST use only these values for the entity `type` field.

## Entity Definitions

### MetricBreakdownEntry

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Metric CLI identifier (e.g., `"fpa"`, `"sp"`) |
| `metric` | `str` | Yes | Metric JSON name (e.g., `"function_points"`, `"story_points"`) |
| `total` | `float` | Yes | Aggregate score for this metric |
| `unit` | `str` | Yes | Measurement unit (e.g., `"ufp"`, `"story_points"`, `"tokens"`) |
| `entity_count` | `int` | Yes | Number of entities in `entities` array |
| `entities` | `list[EntityScore]` | Yes | Per-entity score breakdowns |
| `status` | `str` | Yes | `"success"` or `"failed"` |
| `errors` | `list[str]` | No | Error messages (present when `status` is `"failed"`) |
| `warnings` | `list[str]` | No | Warning messages for partial failures |
| `metadata` | `dict[str, Any]` | No | Metric-specific auxiliary data |

**Validation rules**:
- `entity_count` MUST equal `len(entities)`
- `total` MUST equal `sum(e.score for e in entities)` when status is `"success"`
- `errors` MUST be present and non-empty when `status` is `"failed"`
- `entities` MUST be an empty list when `status` is `"failed"`

### EntityScore

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Compound URI: `<source_model>:<entity_category>:<element_name>` (e.g., `"cfm:data_group:user-profile"`) |
| `name` | `str` | Yes | Human-readable entity name |
| `type` | `CanonicalEntityType` | Yes | Canonical entity category (see vocabulary above) |
| `score` | `float` | Yes | Numeric contribution to the metric total |
| `metadata` | `dict[str, Any]` | No | Metric-specific auxiliary data |

**Validation rules**:
- `id` MUST match the pattern `<source_model>:<category>:<name>` where `source_model` is `"cfm"` or `"csm"`
- `type` MUST be one of the 14 canonical entity types
- `score` MUST be >= 0
- `metadata` (when present) MUST be a flat dict (no nested `metadata` key)

### CanonicalEntityType

```python
CanonicalEntityType = Literal[
    "data_group",
    "operation",
    "functional_process",
    "specification_activity",
    "business_rule",
    "actor",
    "relationship",
    "decision",
    "assumption",
    "constraint",
    "risk",
    "open_question",
    "acceptance_criteria",
    "glossary_term",
]
```

## Metric-Specific Entity Metadata Schemas

Each metric's entities carry domain-specific data in their `metadata` dict:

### FPA

```json
{
  "id": "cfm:data_group:user-profile",
  "name": "User Profile",
  "type": "data_group",
  "score": 10,
  "metadata": {
    "function_type": "ILF",
    "complexity": "Low",
    "det_count": 5,
    "ret_count": 1
  }
}
```

### Story Points

```json
{
  "id": "cfm:functional_process:place-order",
  "name": "Place Order",
  "type": "functional_process",
  "score": 8,
  "metadata": {
    "raw_score": 10.5,
    "normalized_value": 8,
    "factor_breakdown": {
      "business_interactions": 2.0,
      "logical_information": 3.0,
      "external_integrations": 2.0,
      "business_rule_density": 1.5,
      "workflow_breadth": 1.0,
      "exception_handling": 1.0
    },
    "applied_rules": ["default_threshold_v1"]
  }
}
```

### Token Points

```json
{
  "id": "csm:specification_activity:review-requirements",
  "name": "Review Requirements",
  "type": "specification_activity",
  "score": 15.0,
  "metadata": {
    "applied_weight": 3.0,
    "model_source": "csm",
    "element_type": "specification_activity"
  }
}
```

### Cognitive Points

```json
{
  "id": "cfm:business_rule:valid-email-format",
  "name": "Valid Email Format",
  "type": "business_rule",
  "score": 8.0,
  "metadata": {
    "bloom_level": "Analyzing",
    "cognitive_weight": 4.0,
    "model_source": "cfm",
    "element_type": "business_rule"
  }
}
```

### BCP

```json
{
  "id": "cfm:functional_process:onboard-user",
  "name": "Onboard User",
  "type": "functional_process",
  "score": 12,
  "metadata": {
    "component_breakdown": { "login": 4, "profile_setup": 5, "email_verification": 3 }
  }
}
```

### TShirt

```json
{
  "id": "cfm:functional_process:place-order",
  "name": "Place Order",
  "type": "functional_process",
  "score": 8,
  "metadata": {
    "tshirt_size": "M",
    "mapping_rule": "default_v1"
  }
}
```

## Metric-Level Metadata Schemas

### FPA

```json
{
  "metadata": {
    "method": "ifpug",
    "vaf": 1.0
  }
}
```

### Story Points

```json
{
  "metadata": {
    "method": "fibonacci_factor_based",
    "scale": "fibonacci"
  }
}
```

### Token Points

```json
{
  "metadata": {
    "calibration_version": "1.0",
    "specification_cost": 120.0,
    "code_generation_cost": 350.0
  }
}
```

### Cognitive Points

```json
{
  "metadata": {
    "calibration_version": "1.0",
    "raw_score": 245.0,
    "fibonacci_normalization": {
      "raw_score": 245.0,
      "threshold_applied": "100-139",
      "output_value": 100
    }
  }
}
```

## Complete Example

```json
[
  {
    "name": "fpa",
    "metric": "function_points",
    "total": 42,
    "unit": "ufp",
    "status": "success",
    "entity_count": 5,
    "warnings": [],
    "metadata": {
      "method": "ifpug",
      "vaf": 1.0
    },
    "entities": [
      {
        "id": "cfm:data_group:user-profile",
        "name": "User Profile",
        "type": "data_group",
        "score": 10,
        "metadata": {
          "function_type": "ILF",
          "complexity": "Low",
          "det_count": 5,
          "ret_count": 1
        }
      },
      {
        "id": "cfm:operation:register",
        "name": "Register User",
        "type": "operation",
        "score": 4,
        "metadata": {
          "function_type": "EI",
          "complexity": "Average",
          "det_count": 8,
          "ftr_count": 2
        }
      }
    ]
  },
  {
    "name": "sp",
    "metric": "story_points",
    "total": 21,
    "unit": "story_points",
    "status": "success",
    "entity_count": 3,
    "warnings": [],
    "metadata": {
      "method": "fibonacci_factor_based",
      "scale": "fibonacci"
    },
    "entities": [
      {
        "id": "cfm:functional_process:place-order",
        "name": "Place Order",
        "type": "functional_process",
        "score": 8,
        "metadata": {
          "raw_score": 10.5,
          "normalized_value": 8,
          "factor_breakdown": {
            "business_interactions": 2.0,
            "logical_information": 3.0,
            "external_integrations": 2.0,
            "business_rule_density": 1.5,
            "workflow_breadth": 1.0,
            "exception_handling": 1.0
          }
        }
      }
    ]
  }
]
```
