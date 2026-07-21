# RFC-041: Story Points Measurement Engine

**Status**: Draft  
**Date**: 2026-07-21  
**Author**: SpecMetrics  
**Supersedes**: Current Story Points implementation (pre-RFC fixed-threshold normalization)

## Methodology Overview

Story Points estimate relative implementation effort from specification content. The engine analyzes two canonical models — the Canonical Functional Model (CFM) and the Canonical Specification Model (CSM) — and produces a per-element effort score that combines structural complexity with content depth.

### Measurement Formula

For each element `e`:

```
raw_score(e) = structural_score(e) + content_tokens(e) * content_multiplier
```

Where:

- **structural_score(e)**: For functional processes, the weighted sum of 6 structural factors. For all other elements, the element type's base weight from the calibration profile.
- **content_tokens(e)**: The token count of `name + " " + description` using `tiktoken` (GPT-4/GPT-3.5 tokenizer), falling back to character count.
- **content_multiplier**: Configurable coefficient (default: 0.1) that scales content contribution.

### Normalization

Raw scores are converted to a [Modified Fibonacci scale](https://framework.scaledagile.com/blog/glossary_term/modified-fibonacci-sequence) (1, 2, 3, 5, 8, 13, 20, 40, 100) using relative ranking:

1. All element raw scores are sorted ascending.
2. Entities are divided into 9 equal-proportion percentile bands.
3. Each band maps to a Fibonacci value (lowest band → 1, highest band → 100).
4. When fewer than 9 entities exist, direct rank-to-Fibonacci mapping is used.

This makes Story Points a relative metric — normalized values reflect estimation priority within a specification, not absolute magnitude.

### Output Fields

| Field                         | Description                                   |
| ----------------------------- | --------------------------------------------- |
| `total_raw_score`             | Sum of all raw scores (cross-spec comparison) |
| `total_normalized_points`     | Sum of all normalized Fibonacci values        |
| `specification_effort_total`  | Sum of raw scores from CSM elements           |
| `implementation_effort_total` | Sum of raw scores from CFM elements           |
| `content_multiplier`          | Multiplier used for this run                  |
| `content_tokens_by_type`      | Total tokens per element type                 |
| `calibration_version`         | Calibration profile version used              |

## Factor Definitions

Six structural factors are computed for each functional process. Each factor has a configurable coefficient:

| Factor                  | Default Coefficient | Description                       | Measurement                                                                            |
| ----------------------- | ------------------- | --------------------------------- | -------------------------------------------------------------------------------------- |
| `business_interactions` | 1.0                 | Actors associated with the FP     | Count of unique actors in `actor_ids`                                                  |
| `logical_information`   | 1.0                 | Data groups and operations        | Count of `data_group_ids` + `operation_ids`                                            |
| `external_integrations` | 2.0                 | External system interactions      | Count of `communicates_with` relationships involving the FP                            |
| `business_rule_density` | 1.5                 | Business rules relevant to the FP | Count of business rules where FP is in `related_process_ids`                           |
| `workflow_breadth`      | 1.0                 | Sub-operations under the FP       | Count of operations with `parent_process_id == fp_id`                                  |
| `exception_handling`    | 3.0                 | Exception/conditional logic       | Binary: 1.0 if any child operation has type `conditional`, `branching`, or `exception` |

The structural score for a functional process is:

```
structural_score(fp) = Σ(factor_i * coefficient_i)
```

## Element Coverage

### CSM Element Types (Specification Model)

| Type                 | Default Base Weight | Source Container                                       |
| -------------------- | ------------------- | ------------------------------------------------------ |
| exploration          | 4.0                 | specification_activities (activity_type=exploration)   |
| clarification        | 5.0                 | specification_activities (activity_type=clarification) |
| refinement           | 5.0                 | specification_activities (activity_type=refinement)    |
| review               | 3.0                 | specification_activities (activity_type=review)        |
| validation           | 3.0                 | specification_activities (activity_type=validation)    |
| decision             | 5.0                 | decisions                                              |
| assumption           | 2.0                 | assumptions                                            |
| constraint           | 3.0                 | constraints                                            |
| risk                 | 4.0                 | risks                                                  |
| open_question        | 2.0                 | open_questions                                         |
| acceptance_criterion | 3.0                 | acceptance_criteria                                    |
| glossary_term        | 1.0                 | glossary_terms                                         |
| reference            | 0.5                 | references                                             |

### CFM Element Types (Functional Model)

| Type               | Default Base Weight | Notes                                                 |
| ------------------ | ------------------- | ----------------------------------------------------- |
| functional_process | —                   | Uses 6-factor weighted scoring instead of base weight |
| business_rule      | 4.0                 | Non-FP CFM element                                    |
| operation          | 3.0                 | Non-FP CFM element                                    |
| data_group         | 3.0                 | Non-FP CFM element                                    |
| relationship       | 1.0                 | Non-FP CFM element                                    |
| actor              | 1.0                 | Non-FP CFM element                                    |

Elements with unknown types use `default_fallback_weight` (default: 1.0).

## Normalization Algorithm

### Percentile-Band Ranking

Given N entities with raw scores `s_1 ≤ s_2 ≤ ... ≤ s_N`:

1. Sort all entity raw scores in ascending order.
2. Divide into 9 bands, each containing approximately N/9 entities.
3. Map bands to the Modified Fibonacci scale: [1, 2, 3, 5, 8, 13, 20, 40, 100].
4. When `N < 9`: use direct rank mapping where rank 0 → 1 and rank N-1 → 100.

The normalized values are non-decreasing with respect to raw scores: if `s_i <= s_j`, then `normalized_value_i <= normalized_value_j`.

## Calibration Reference

### YAML Schema

```yaml
version: "1.0"
content_multiplier: 0.1
factor_coefficients:
  business_interactions: 1.0
  logical_information: 1.0
  external_integrations: 2.0
  business_rule_density: 1.5
  workflow_breadth: 1.0
  exception_handling: 3.0
csm_base_weights:
  exploration: 4.0
  clarification: 5.0
  refinement: 5.0
  review: 3.0
  validation: 3.0
  decision: 5.0
  assumption: 2.0
  constraint: 3.0
  risk: 4.0
  open_question: 2.0
  acceptance_criterion: 3.0
  glossary_term: 1.0
  reference: 0.5
cfm_base_weights:
  business_rule: 4.0
  operation: 3.0
  data_group: 3.0
  relationship: 1.0
  actor: 1.0
default_fallback_weight: 1.0
fibonacci_scale: [1, 2, 3, 5, 8, 13, 20, 40, 100]
ranking_strategy: "percentile"
```

### Configurable Parameters

| Parameter                 | Default                  | Validation                        |
| ------------------------- | ------------------------ | --------------------------------- |
| `content_multiplier`      | 0.1                      | >= 0.0                            |
| `factor_coefficients.*`   | per-factor defaults      | >= 0.0                            |
| `csm_base_weights.*`      | per-type defaults        | >= 0.0                            |
| `cfm_base_weights.*`      | per-type defaults        | >= 0.0                            |
| `default_fallback_weight` | 1.0                      | >= 0.0                            |
| `fibonacci_scale`         | [1,2,3,5,8,13,20,40,100] | Sorted ascending, len >= 2        |
| `ranking_strategy`        | "percentile"             | Must be "percentile" (extensible) |

### Backward Compatibility

Old calibration files lacking new fields load with defaults:

- Missing `content_multiplier` → 0.1
- Missing factor coefficients → standard 6 coefficients
- Missing CSM weights → 13 standard weights
- Missing CFM weights → 5 standard weights
- Missing `default_fallback_weight` → 1.0
- Missing `fibonacci_scale` → default 9-value scale
- Missing `ranking_strategy` → "percentile"

Minimal valid profile:

```yaml
version: "1.0"
```

## Cross-Specification Comparison

Raw scores enable cross-specification comparison because they are independent of ranking context:

- **`total_raw_score`**: Sum of all element raw scores. A specification with higher `total_raw_score` represents more estimated effort.
- **`specification_effort_total`**: CSM element contribution (decisions, assumptions, etc.).
- **`implementation_effort_total`**: CFM element contribution (functional processes, business rules, etc.).

Normalized values (Fibonacci) are within-specification relative rankings and should not be compared across specifications.

## Kanban Usage Appendix

Story Points are designed for manual Kanban-style work item sizing:

1. Run measurement on a specification to obtain per-element raw scores and normalized Fibonacci values.
2. Use the `distribution` histogram to understand the effort profile at a glance.
3. Assign work items to sprints based on total normalized points per sprint capacity.
4. Use `total_raw_score` trends across specification versions to track effort growth.

**No automatic chunking**: Story Points produce estimates for individual elements, not decomposed work items. Decomposition into actionable tasks remains a manual practice.
