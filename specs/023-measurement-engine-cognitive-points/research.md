# Research: Cognitive Points Measurement Engine

## 1. Measurement Plugin Architecture

**Decision**: Follow the existing measurement plugin pattern (SFP/FPA/SNAP/Token Points) — a `Plugin` class with `measure()` method consuming CFM + CSM, a `Handler` implementing `EventHandler`, and a `create_*_metadata()` factory.

**Rationale**: Consistent with the three existing measurement plugins and the Token Points plugin (022). The Cognitive Points plugin adds two unique components — Bloom classification and Fibonacci normalization — but follows the same overall structure.

**Alternatives considered**: Extending Token Points plugin with cognitive mode — rejected because cognitive effort is a fundamentally different metric (human HITL vs AI token cost) with different calibration and normalization.

---

## 2. Bloom Classification Algorithm

**Decision**: Element-type-based static classification with per-type mapping configured in the calibration profile.

**Default mapping** (from FR-014a):
| Bloom Level | Elements |
|---|---|
| Remember | Glossary Terms, Actors |
| Understand | Exploration, Assumptions, Data Groups, Relationships |
| Apply | Refinement, Constraints, Acceptance Criteria, Business Rules, Operations |
| Analyze | Clarification, Risks, Open Questions |
| Evaluate | Review, Validation, Decisions |
| Create | Functional Processes |

**Algorithm**: O(1) lookup by element type string → Bloom level. The calibration profile contains a `bloom_mappings: dict[str, str]` map where keys are element type names (e.g., `"decision"`, `"functional_process"`, `"exploration"`) and values are Bloom level strings (`"remember"`, `"understand"`, etc.).

**Fallback**: Elements without a mapping receive the configured `default_bloom_level` (default: `"analyze"`) and are reported in measurement metadata.

**Alternatives considered**: NLP-based classification — rejected (violates determinism requirement, FR-024). LLM-assisted classification — rejected (same reason). The element type is already determined by the CSM/CFM builder's classifier, making type-based lookup deterministic and O(1).

---

## 3. Fibonacci Normalization Algorithm

**Decision**: Threshold-based lookup table. Raw score is compared against ascending thresholds; the corresponding Fibonacci value is returned.

**Default configuration**:
```python
FIBONACCI_TABLE = [
    (0, 1),        # raw_score < threshold_1 → 1
    (threshold_1, 3),
    (threshold_2, 5),
    (threshold_3, 8),
    (threshold_4, 13),
    (threshold_5, 20),
    (threshold_6, 40),
    (threshold_7, 100),  # raw_score >= threshold_7 → 100
]
```

**Default thresholds**: Equidistant based on typical raw score ranges. Example: for a specification with 20 elements averaging Bloom weight 2.0 → raw score ~40. Thresholds at [5, 12, 22, 35, 55, 85, 130] → normalized to Fibonacci values [1, 3, 5, 8, 13, 20, 40, 100].

**Threshold calculation**: `threshold_n = max_score × (n / num_levels)` where `max_score` is an estimate based on typical specification size × average Bloom weight. The default profile uses fixed thresholds; organizations can customize both thresholds and output values.

**Alternatives considered**: Proportional formula `normalized = round_to_nearest_fib(raw_score × scale_factor)` — rejected because it's less intuitive for planning and harder to calibrate. Configurable table was chosen for maximum transparency (FR-023 requires every normalization result to be reported).

---

## 4. Three-Stage Calculation Flow

**Decision**: Strict three-stage separation for clarity and explainability.

```
Stage 1 — Per-component raw score:
  Input: CFM + CSM element collections
  Process: For each element → lookup Bloom level → lookup Bloom weight → add to component sum
  Output: (spec_raw, code_raw)  # two floats

Stage 2 — Total raw score:
  Input: spec_raw, code_raw
  Process: raw_total = spec_raw + code_raw
  Output: raw_total

Stage 3 — Fibonacci normalization:
  Input: raw_total
  Process: Walk FIBONACCI_TABLE thresholds; return first matching Fibonacci value
  Output: normalized Cognitive Points score
```

**Edges cases**:
- Empty CSM → spec_raw = 0, stage 2 proceeds with code_raw only
- Empty CFM → code_raw = 0, stage 2 proceeds with spec_raw only
- Both empty → raw_total = 0, stage 3 returns minimum Fibonacci value (1)

**Performance**: O(n + m) for n CSM + m CFM elements, plus O(1) Fibonacci lookup. Well under the 2-second target for 500 elements.

---

## 5. Calibration Profile YAML Schema

**Decision**: Follow Token Points (022) YAML pattern, extended with Bloom-specific sections.

**YAML schema**:
```yaml
# .specmetrics/calibration/cognitive-points.yml
version: "1.0"
bloom_levels:
  remember: 1.0
  understand: 2.0
  apply: 3.0
  analyze: 4.0
  evaluate: 5.0
  create: 8.0

bloom_mappings:
  # CSM Specification Activities
  exploration: "understand"
  clarification: "analyze"
  refinement: "apply"
  review: "evaluate"
  validation: "evaluate"
  # CSM entities
  decision: "evaluate"
  assumption: "understand"
  constraint: "apply"
  risk: "analyze"
  open_question: "analyze"
  acceptance_criterion: "apply"
  glossary_term: "remember"
  # CFM entities
  functional_process: "create"
  business_rule: "apply"
  operation: "apply"
  data_group: "understand"
  relationship: "understand"
  actor: "remember"

default_bloom_level: "analyze"

fibonacci_normalization:
  thresholds: [5, 12, 22, 35, 55, 85, 130]
  output_values: [1, 3, 5, 8, 13, 20, 40, 100]
```

**Alternatives considered**: Embedding Bloom config inside Token Points calibration — rejected because Token Points doesn't use Bloom taxonomy. Separate file keeps concerns isolated.

---

## 6. Explainability

**Decision**: Each CognitiveContribution carries element identity, Bloom level, cognitive weight, partial score, normalized contribution, and evidence reference. An additional report method constructs the ordered breakdown.

**Report structure**:
```json
{
  "total_cognitive_points": 13,
  "raw_score": 42.5,
  "specification_review_effort": { "total_raw": 18.5, "contributions": [...], "bloom_breakdown": {"analyze": 5, "evaluate": 3} },
  "functional_validation_effort": { "total_raw": 24.0, "contributions": [...], "bloom_breakdown": {"create": 2, "apply": 4} },
  "fibonacci_normalization": { "raw_score": 42.5, "threshold_applied": "35", "output_value": 13 },
  "top_contributors": [...]
}
```

---

## 7. CSM Integration (Graceful Degradation)

**Decision**: Same pattern as Token Points — CSM is optional. When CSM is absent, Specification Review Effort defaults to 0 with a warning.

**Rationale**: CSM (feature 021) may not be implemented when Cognitive Points ships. The engine should produce useful output (Functional Validation Effort only) rather than failing.
