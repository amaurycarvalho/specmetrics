# Research: Cognitive Points Improvements

**Feature**: 039-cognitive-points-improvements
**Date**: 2026-07-21

## Research Task 1: Sub-Type Attribute Availability on CSM/CFM Elements

### Finding

CSM and CFM elements have type-specific attributes that carry sub-type information:

**CSM elements:**
| Element Type | Sub-Type Attribute | Possible Values |
|---|---|---|
| SpecificationActivity | `activity_type` | exploration, clarification, refinement, review, validation |
| Decision | (none) | N/A |
| Assumption | (none) | N/A |
| Constraint | (none) | N/A |
| Risk | (none) | N/A |
| OpenQuestion | (none) | N/A |
| AcceptanceCriterion | (none) | N/A |
| GlossaryTerm | (none) | N/A |

**CFM elements:**
| Element Type | Sub-Type Attribute | Possible Values |
|---|---|---|
| BusinessRule | `rule_type` | constraint, condition, policy, derivation |
| Operation | `operation_type` | standard, conditional, iterative, transactional |
| FunctionalProcess | (none currently) | N/A |
| DataGroup | (none) | N/A |
| Relationship | (none) | N/A |
| Actor | (none) | N/A |

### Decision

Only BusinessRule and Operation have sub-type attributes worth classifying. SpecificationActivity already has its own Bloom mapping (5 activity types map to different levels — but these are already separate element types in the current mapping, not sub-types). The sub-type classification applies primarily to BusinessRules and Operations, which are currently all classified as a single Bloom level ("apply" for both).

### Alternatives Considered

- **Sub-type classification for all element types**: Rejected — most element types don't have meaningful sub-type attributes.
- **Ignore sub-types and only add content-based scoring**: Rejected — the spec explicitly requires sub-type differentiation (FR-005, FR-006, SC-003).

---

## Research Task 2: Current Bloom Classifier Interface

### Finding

The `BloomClassifier` class in `bloom_classifier.py` has:
- `classify(element_type: str) -> str` — takes a type string, returns a bloom level name
- Internal `_mappings: dict[str, str]` — type → bloom level
- `_default_bloom_level: str` — fallback

The `DefaultBloomClassifier` subclass hardcodes the default mappings in `__init__`.

The classifier is called from `calculator.py` at line 169 (CSM loop) and line 248 (CFM loop), passing the result of `rstrip("s")` on collection names or the activity's `activity_type` attribute.

### Decision

Change the `classify()` signature to accept an optional `element` object:
```python
def classify(self, element_type: str, element: Any = None) -> str
```

When `element` is provided and has a sub-type attribute, the classifier looks up `base_type.sub_type_value`. When `element` is `None` (backward compat), it falls back to the base type lookup.

### Alternatives Considered

- **New `classify_with_subtype()` method**: Creates two classification paths — rejected for code duplication.
- **Pass sub-type as a separate string parameter**: Requires callers to extract sub-types themselves — rejected, better to have the classifier own the sub-type extraction logic.

---

## Research Task 3: Bloom Weights and Cognitive Science Basis

### Finding

The 6 Bloom levels and their weights are based on Anderson & Krathwohl's revision of Bloom's taxonomy (2001). The hierarchy from lowest to highest cognitive demand is:

1. **Remember** (1.0): Recall facts, terms, basic concepts
2. **Understand** (2.0): Explain ideas, interpret, summarize
3. **Apply** (3.0): Use information in new situations
4. **Analyze** (4.0): Draw connections, differentiate, organize
5. **Evaluate** (5.0): Justify decisions, critique, judge
6. **Create** (8.0): Produce new work, design, construct

The weight 8.0 for "create" (vs. 5.0 for "evaluate") reflects the cognitive load gap between synthesis and analysis — creating is roughly 2x more demanding than evaluating. This is consistent with widely-used Cognitive Load Theory weightings.

### Decision

Bloom weights remain unchanged. They are well-established and adding content-based scoring already addresses the "no differentiation within same Bloom level" limitation. The sub-type classification changes which Bloom level an element maps to, but does not change the level weights themselves.

### Alternatives Considered

- **Fine-tune Bloom weights based on empirical data**: Requires telemetry infrastructure not yet available. Deferred to future.
- **Make Bloom weights configurable per sub-type**: Over-complicates calibration. Sub-types already affect classification (different Bloom levels = different weights).

---

## Research Task 4: Impact of Default Change from "analyze" to "understand"

### Finding

The current default is "analyze" (4.0). Changing to "understand" (2.0) halves the cognitive weight assigned to unrecognized element types. This primarily affects:

1. **Unknown CSM element types**: If a new CSM element type is added in a future framework adapter, it will default to 2.0 instead of 4.0.
2. **Unknown CFM element types**: Same — new CFM element types default to 2.0.
3. **Elements with missing type information**: Edge case where type string is empty or malformed.

In a typical specification with all element types mapped, the default change has zero impact — no elements hit the fallback. The change only affects edge cases and future-proofing.

### Decision

Change the default to "understand" (2.0). The more conservative default is:
- More justifiable: if we don't know what an element is, assuming medium-low cognitive effort is safer than assuming medium-high
- More accurate for new frameworks: new element types are more likely to be "understanding-level" concepts than "analysis-level"
- Consistent with the spec's goal of more realistic estimation

### Alternatives Considered

- **Keep "analyze" default**: Rejected — too aggressive for unknown types.
- **Make default configurable**: Adds calibration complexity for an edge case. The default can still be overridden in calibration YAML.
