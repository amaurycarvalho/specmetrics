# Research: Token Points Measurement Engine

## 1. Measurement Plugin Architecture

**Decision**: Follow the existing SFP/FPA/SNAP pattern — a `Plugin` class with `measure()` method, a `Handler` implementing `EventHandler`, and a `create_*_metadata()` factory.

**Rationale**: The three existing measurement plugins (SFP, FPA, SNAP) all use this pattern consistently:
- `plugin.py` — `Plugin` class + `Handler` class + `create_*_metadata()` factory
- `models.py` — Pydantic result models
- `counter.py` — core counting/calculation logic
- `explainer.py` — explanation builder

The Token Points plugin will follow the same structure. Since Token Points consumes both CFM and CSM (unlike SFP/FPA/SNAP which only consume CFM), the `measure()` method signature is extended to accept CSM as a second parameter.

**Alternatives considered**: Embedding in kernel — rejected because measurement plugins are externalizable and should follow the plugin architecture.

---

## 2. CSM Integration Strategy

**Decision**: The Token Points engine is designed to consume both CFM and CSM, with CSM being optional for graceful degradation when feature 021 is not yet implemented.

**Rationale**: Feature 021 (Canonical Specification Model) has been planned but not yet implemented. Token Points can still deliver value using only the CFM (Code Generation Cost = total Token Points, Specification Cost = 0 with a warning). Once the CSM stage is operational, Specification Cost activates automatically.

**Handler logic**:
1. Read `ctx.canonical_model` (CFM) — always available
2. Read `ctx.canonical_spec_model` (CSM) — available after feature 021 is implemented
3. If CSM is available: calculate both Specification Cost and Code Generation Cost
4. If CSM is None: calculate Code Generation Cost only, emit warning about missing CSM

**Pipeline event**: Subscribe to `EventType.MEASUREMENT_COMPLETED` (same as SFP/FPA/SNAP), which fires after `RULE_PACK_APPLIED` in `CANONICAL_EVENT_ORDER`.

**Alternatives considered**: Creating a new event type — rejected because all measurement plugins share the same subscription point for consistency.

---

## 3. Calibration Profile YAML Schema

**Decision**: Hierarchical YAML structure with two top-level sections matching the cost components.

**YAML schema**:
```yaml
# .specmetrics/calibration/token-points.yml
version: "1.0"
specification_cost:
  activities:
    exploration: 2.0
    clarification: 3.0
    refinement: 2.5
    review: 1.5
    validation: 2.0
  decisions: 1.5
  assumptions: 1.0
  constraints: 1.5
  risks: 2.0
  open_questions: 1.0
  acceptance_criteria: 1.0
  glossary_terms: 0.5

code_generation_cost:
  functional_processes: 5.0
  business_rules: 3.0
  operations: 2.0
  data_groups: 2.0
  relationships: 1.0
  actors: 1.0
```

**Override mechanism**: Organization profiles in the same directory with higher priority override specific keys. YAML merge semantics: deeper keys override, not full file replacement.

**Alternatives considered**: JSON schema — rejected (no comment support). Flat key-value — rejected (poor organization for two cost components).

---

## 4. Default Weight Values

**Decision**: Heuristic starting values (above) based on relative complexity of each element type. These are starting points, not calibrated values — organizations should tune via Rule Packs.

**Rationale**: No historical telemetry exists for the initial release. Weights are based on:
- Specification Activities: clarification (3.0) is most expensive (resolving ambiguity), review (1.5) is least
- Decisions: higher than assumptions because they involve analysis of alternatives
- Functional Processes (5.0) are the most complex CFM element — they orchestrate operations, data, rules
- Glossary Terms (0.5) are lightweight — single concept definitions

**Calibration philosophy**: The initial defaults are intentionally conservative (under-estimation is safer than over-estimation for planning). Organizations collect telemetry and refine.

---

## 5. Calculation Algorithm

**Decision**: Single-pass O(n) algorithm iterating over CFM and CSM element collections, applying weights, accumulating contributions.

**Algorithm**:
```
token_points = 0
contributions = []

for each element in csm.specification_activities:
    weight = calibration.specification_cost.activities[element.activity_type]
    contributions.append(TokenContribution(...))
    token_points += weight

for each (category, collection) in csm_category_map:
    for each element in collection:
        weight = calibration.specification_cost[category]
        contributions.append(TokenContribution(...))
        token_points += weight

# Same pattern for CFM entities
spec_cost = sum(spec contributions)
code_cost = sum(code contributions)
total = spec_cost + code_cost
```

**Performance**: O(n+m) for n CSM elements and m CFM elements. With 500 elements total, well under the 2-second target.

**Alternatives considered**: Hash-join approach for cross-referencing CSM/CFM — rejected because they are independent models with no direct element-level relationships.

---

## 6. Explainability

**Decision**: Each TokenContribution carries element identity, weight, partial score, and evidence reference. An additional static method computes ranked breakdown (highest contributors first).

**Rationale**: FR-016 through FR-018 require every contribution to be individually reported with applied weight and cumulative score. The simplest approach is a flat list of contributions where the consumer can sort/filter/aggregate.

**Report structure**:
```json
{
  "total": 47.5,
  "specification_cost": { "total": 18.5, "contributions": [...] },
  "code_generation_cost": { "total": 29.0, "contributions": [...] },
  "top_contributors": [
    {"element": "Login Process", "score": 5.0, "weight": 5.0},
    ...
  ]
}
```

---

## 7. Calibration Plugin

**Decision**: Create a shared `plugins/calibration/` plugin that loads YAML calibration profiles from `.specmetrics/calibration/`, validates them, and injects them into PipelineContext for consumption by measurement plugins.

**Rationale**: Multiple measurement plugins (Token Points, future methods) need calibration data. A shared calibration plugin avoids duplication and provides a single discovery/loading/validation mechanism.

**Calibration pipeline flow**:
1. Calibration plugin subscribes to `MEASUREMENT_COMPLETED` (or runs before measurement)
2. Discovers YAML files in `.specmetrics/calibration/`
3. Loads and merges profiles (built-in defaults → organization overrides)
4. Stores merged `CalibrationProfile` in context metadata
5. Token Points handler reads calibration from context

**NOTE**: For v0.1, calibration loading can be embedded directly in the Token Points plugin (simpler). The shared calibration plugin is a future refinement.
