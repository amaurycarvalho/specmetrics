# Data Model: Token Points Improvements

**Feature**: 038-token-points-improvements

## Overview

Three existing models are updated and one new sub-configuration is added. No new top-level entities.

---

## TokenContribution (Updated)

**File**: `specmetrics/plugins/measurement/token_points/models.py`

| Field | Type | Change | Description |
|-------|------|--------|-------------|
| `element_id` | `str` | Unchanged | Unique element identifier |
| `element_type` | `str` | Unchanged | Collection name (e.g., "functional_processes", "decisions") |
| `element_name` | `str` | Unchanged | Human-readable name |
| `model_source` | `str` | Unchanged | "csm" or "cfm" |
| `applied_weight` | `float` | Unchanged | Type-based weight from calibration |
| `content_token_count` | `int` | **NEW** | Number of tokens in element's text content |
| `content_score` | `float` | **NEW** | `content_token_count × content_multiplier` |
| `partial_score` | `float` | **Changed semantics** | Now equals `applied_weight + content_score` (was just `applied_weight`) |
| `evidence_ref` | `str \| None` | Unchanged | Evidence reference |

**Validation**: `partial_score` MUST equal `applied_weight + content_score` (within floating-point tolerance).

**Content source**: Element's `name` + `" "` + `description` (or just `name` if no description, or `title` + `url` for `references`).

---

## SpecificationCostWeights (Updated)

**File**: `specmetrics/plugins/calibration/models.py`

| Field | Type | Old Default | New Default |
|-------|------|-------------|-------------|
| `activities` | `dict[str, float]` | `{}` (empty dict) | `{"exploration": 2.0, "clarification": 3.0, "refinement": 3.0, "review": 1.5, "validation": 2.0}` |
| `decisions` | `float` | 1.5 | 1.5 (unchanged) |
| `assumptions` | `float` | 1.0 | 1.0 (unchanged) |
| `constraints` | `float` | 1.5 | 1.5 (unchanged) |
| `risks` | `float` | 2.0 | 2.0 (unchanged) |
| `open_questions` | `float` | 1.0 | 1.0 (unchanged) |
| `acceptance_criteria` | `float` | 1.0 | 1.0 (unchanged) |
| `glossary_terms` | `float` | 0.5 | 0.5 (unchanged) |
| `references` | `float` | (did not exist) | **1.0** (NEW) |

---

## CodeGenerationCostWeights (Unchanged)

| Field | Default |
|-------|---------|
| `functional_processes` | 5.0 |
| `business_rules` | 3.0 |
| `operations` | 2.0 |
| `data_groups` | 2.0 |
| `relationships` | 1.0 |
| `actors` | 1.0 |

---

## CalibrationProfile (Updated)

**File**: `specmetrics/plugins/calibration/models.py`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `version` | `str` | Unchanged | Semver |
| `name` | `str \| None` | Unchanged | Profile name |
| `specification_cost` | `SpecificationCostWeights` | Updated defaults | Weights for CSM elements |
| `code_generation_cost` | `CodeGenerationCostWeights` | Unchanged | Weights for CFM elements |
| `content_multiplier` | `float` | **0.1** (NEW) | Multiplier for content token contribution to score |

**Validation**: `content_multiplier` MUST be >= 0.0. When set to 0.0, content-based estimation is effectively disabled (scores revert to type-weight only), enabling backward compatibility with workflows that rely on the old flat-weight behavior.

---

## Payload Extensions (plugin.py)

The handler payload (`measurement_result` dict) gains two new keys:

| Key | Type | Description |
|-----|------|-------------|
| `token_content_multiplier` | `float` | The content_multiplier used for this run |
| `token_content_tokens` | `dict[str, int]` | Total content token count per element type |

The existing `token_element_counts` dict is extended per entry:

| Field | Type | Change |
|-------|------|--------|
| `count` | `int` | Unchanged — number of elements of this type |
| `total` | `float` | Unchanged — sum of partial_scores |
| `content_tokens` | `int` | **NEW** — sum of content_token_count for elements of this type |

---

## Updated Calculation Flow

```
for each CSM element:
    type_weight = calibration.specification_cost[element_type]
    content_tokens = count_tokens(element.name + " " + element.description)
    content_score = content_tokens × content_multiplier
    partial_score = type_weight + content_score
    specification_cost += partial_score

for each CFM element:
    type_weight = calibration.code_generation_cost[element_type]
    content_tokens = count_tokens(element.name + " " + element.description)
    content_score = content_tokens × content_multiplier
    partial_score = type_weight + content_score
    code_generation_cost += partial_score

Token Points = specification_cost + code_generation_cost
```
