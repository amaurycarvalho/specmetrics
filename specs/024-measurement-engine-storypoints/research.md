# Research: Story Points Measurement Engine

## 1. Measurement Plugin Architecture

**Decision**: Follow the existing measurement plugin pattern (SFP/FPA/SNAP) — a `Plugin` class with `measure()` method consuming CFM, a `Handler` implementing `EventHandler`, and a `create_*_metadata()` factory.

**Rationale**: Consistent with all existing measurement plugins. Story Points is the simplest plugin — it only consumes CFM (no CSM dependency, unlike Token Points and Cognitive Points).

**Alternatives considered**: Embedding logic in existing SFP plugin — rejected because Story Points is an independent methodology (per spec assumptions) with different scoring semantics.

---

## 2. Multi-Factor Weighted Sum Algorithm

**Decision**: For each Functional Process, score each factor independently, multiply by configurable coefficient, and sum for raw effort score.

```
raw_score = Σ(factor_score(f) × coefficient(f)) for f in active_factors
```

**Default factors and coefficients** (from FR-016b):

| Factor | Source | Default Coefficient |
|---|---|---|
| business_interactions | Count of related actors + external entities | 1.0 |
| logical_information | Count of related data groups + operations | 1.0 |
| external_integrations | Count of relationships with external data groups | 2.0 |
| business_rule_density | Count of associated business rules | 1.5 |
| workflow_breadth | Number of operations and sub-processes | 1.0 |
| exception_handling | 1 if conditional/branching logic present, else 0 | 3.0 |

**Factor scoring rules**:
- `business_interactions`: Count distinct actors (via `FunctionalProcess.actor_ids`) + external entities referenced
- `logical_information`: Count related data groups (`FunctionalProcess.data_group_ids`) + operations (`FunctionalProcess.operation_ids`)
- `external_integrations`: Count relationships where `Relationship.relationship_type == "communicates_with"` involving the Functional Process
- `business_rule_density`: Count business rules where `BusinessRule.related_process_ids` contains the Functional Process's ID
- `workflow_breadth`: Count operations where `Operation.parent_process_id` matches the Functional Process's ID
- `exception_handling`: Check if any related operation metadata contains branching/conditional indicators

**Inherited CFM relationships**: All factor scoring uses existing `CanonicalFunctionalModel` fields: `actor_ids`, `data_group_ids`, `operation_ids` on the `FunctionalProcess` entity, plus `BusinessRule.related_process_ids`, `Relationship.source_id`/`target_id`.

**Alternatives considered**: SFP-based weight per component type — rejected because Story Points need multi-factor granularity for explainability (FR-027). Lookup table — rejected because it doesn't support configurable coefficients (FR-023).

---

## 3. Modified Fibonacci Normalization

**Decision**: Threshold-based lookup table mapped to the Modified Fibonacci scale: 1, 2, 3, 5, 8, 13, 20, 40, 100.

**Default thresholds** (equidistant):
```python
FIBONACCI_TABLE = [
    (0, 1),         # raw_score < t1 → 1
    (t1, 2),        # t1 ≤ raw_score < t2 → 2
    (t2, 3),        # t2 ≤ raw_score < t3 → 3
    (t3, 5),        # t3 ≤ raw_score < t4 → 5
    (t4, 8),        # t4 ≤ raw_score < t5 → 8
    (t5, 13),       # t5 ≤ raw_score < t6 → 13
    (t6, 20),       # t6 ≤ raw_score < t7 → 20
    (t7, 40),       # t7 ≤ raw_score < t8 → 40
    (t8, 100),      # raw_score ≥ t8 → 100
]
```

**Threshold estimation**: Based on typical raw score range for a small-to-medium Functional Process. Default thresholds at raw score values: [2, 4, 8, 14, 22, 35, 55, 85]. Organizations tune via Rule Packs (FR-021, FR-024).

**Clamping**: Raw scores below the minimum threshold return 1. Raw scores above the maximum threshold return 100. FR-020 prohibits values outside the configured scale.

**Alternatives considered**: Continuous formula `ceil_to_nearest_fib(raw_score × factor)` — rejected because threshold tables are more transparent and configurable.

---

## 4. Incremental Execution (FR-033/FR-034)

**Decision**: Compare SHA-256 content fingerprints (defined in FR-014) of each Functional Process against cached fingerprints from the previous run. Only re-estimate processes whose fingerprints differ.

**Mechanism**: The calculator maintains a `fingerprint_cache: dict[str, str]` mapping `element_id → sha256(document_id, section_id, text, semantic_type)`. On subsequent runs, compute fresh fingerprints, diff against cache, re-estimate only changed IDs.

**Limitation**: v0.1 uses in-memory cache only (lost between pipeline runs). Persistent caching is a future enhancement.

**Alternatives considered**: Timestamp-based detection — rejected because CFM doesn't track modification timestamps per element. Pipeline-level change tracking — rejected because it requires PipelineContext changes.

---

## 5. Duplicate Detection (FR-014)

**Decision**: Use the existing `fingerprint_node()` function from `specmetrics/kernel/evidence_graph.py` — SHA-256 of `document_id`, `section_id`, `text`, `semantic_type`. Functional Processes with identical fingerprints are merged (only the first occurrence is estimated; duplicates are reported in metadata).

**Implementation**: Before estimation, deduplicate the Functional Process list by fingerprint. Store fingerprint in each work item's metadata for traceability.

---

## 6. OpenTelemetry Integration (FR-036)

**Decision**: Follow the same pattern as SFP (see `sfp/plugin.py`) — initialize metrics at module level:

```python
_meter = otel_metrics.get_meter("specmetrics.storypoints")
_duration_histogram = _meter.create_histogram("storypoints.estimation.duration", ...)
_item_gauge = _meter.create_gauge("storypoints.estimated_items", ...)
_distribution_histogram = _meter.create_histogram("storypoints.distribution", ...)
```

**Alternatives considered**: Skipping metrics — rejected because FR-036 explicitly requires them.

---

## 7. Explainability (FR-027)

**Decision**: Each FunctionalWorkItem exposes a complete factor breakdown. The report includes both per-item detail and aggregate distribution.

**Report structure**:
```json
{
  "method": "StoryPoints",
  "scale": "ModifiedFibonacci",
  "total_story_points": 196,
  "estimated_items": 37,
  "items": [
    {
      "element_id": "uuid",
      "element_name": "Process Order",
      "raw_score": 14.5,
      "normalized_value": 8,
      "factor_breakdown": {
        "business_interactions": 3.0,
        "logical_information": 4.0,
        "business_rule_density": 4.5,
        "workflow_breadth": 3.0
      },
      "evidence_refs": [...]
    }
  ],
  "distribution": {"3": 8, "5": 12, "8": 10, "13": 5, "20": 2},
  "execution_metadata": {"duration_ms": 45, "version": "1.0"}
}
```
