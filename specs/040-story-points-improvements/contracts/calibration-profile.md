# Contract: Story Points Calibration Profile

**Feature**: 040-story-points-improvements  
**Format**: YAML  
**Location**: Discovered by the shared calibration loader from a configured `calibration_dir`

## Schema

```yaml
# Story Points Calibration Profile
# All fields are optional — missing fields load with documented defaults.

version: "1.0"                    # Profile format version

content_multiplier: 0.1           # Multiplier for content token contribution (0.0 disables)

factor_coefficients:              # Weights for the 6 structural factors (FPs only)
  business_interactions: 1.0      #   Actors associated with the FP
  logical_information: 1.0        #   Data groups + operations linked to the FP
  external_integrations: 2.0      #   "communicates_with" relationships
  business_rule_density: 1.5      #   Business rules referencing the FP
  workflow_breadth: 1.0           #   Operations whose parent is this FP
  exception_handling: 3.0         #   Conditional/branching/exception operations (binary)

csm_base_weights:                 # Base weights for CSM element types
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

cfm_base_weights:                 # Base weights for non-FP CFM element types
  business_rule: 4.0
  operation: 3.0
  data_group: 3.0
  relationship: 1.0
  actor: 1.0

default_fallback_weight: 1.0      # Weight for element types not in the mappings

fibonacci_scale:                  # Output Fibonacci values (sorted, at least 2 entries)
  - 1
  - 2
  - 3
  - 5
  - 8
  - 13
  - 20
  - 40
  - 100

ranking_strategy: "percentile"    # Band distribution: "percentile" (default)
```

## Validation Rules

1. `content_multiplier` must be `>= 0.0`
2. All weight values in `factor_coefficients`, `csm_base_weights`, and `cfm_base_weights` must be `>= 0.0`
3. `default_fallback_weight` must be `>= 0.0`
4. `fibonacci_scale` must contain at least 2 values, sorted in ascending order
5. `fibonacci_scale` values must be positive integers
6. `ranking_strategy` must be one of: `"percentile"`
7. Unknown top-level keys are ignored (forward compatibility)
8. Unknown element type keys in weight mappings are preserved (user-defined types)

## Backward Compatibility

Old calibration YAML files that lack the new fields load normally:

- Missing `content_multiplier` → defaults to `0.1`
- Missing `factor_coefficients` → defaults to the 6 standard coefficients
- Missing `csm_base_weights` → defaults to the 13 CSM weights
- Missing `cfm_base_weights` → defaults to the 5 CFM weights
- Missing `default_fallback_weight` → defaults to `1.0`
- Missing `fibonacci_scale` → defaults to `[1,2,3,5,8,13,20,40,100]`
- Missing `ranking_strategy` → defaults to `"percentile"`

## Minimal Valid Profile

```yaml
version: "1.0"
```

All parameters default to documented values. This is sufficient for a basic run with all defaults.

## Customization Example

```yaml
version: "1.0"
content_multiplier: 0.05           # Halve content influence
factor_coefficients:
  exception_handling: 5.0          # Increase exception handling weight
csm_base_weights:
  decision: 8.0                    # Decisions carry more weight
  risk: 2.0                        # Risks carry less weight
cfm_base_weights:
  actor: 0.5                       # Actors are lighter
default_fallback_weight: 0.5
fibonacci_scale:
  - 1
  - 2
  - 3
  - 5
  - 8
  - 13
  - 20
```
