# Research: OpenSpec Operation Extraction Rules

**Feature**: 035-openspec-operation-rules
**Date**: 2026-07-20

## Decision: Repurpose 9 fact-typed rules as operation-typed

### Decision
Change the `type` field from `"fact"` to `"operation"` for 9 existing rules in `openspec_rules.yaml`. No new rules, no deleted rules, no pattern changes — only the semantic type is corrected.

### Rationale
The deterministic engine already supports `type: "operation"` — rules with this type produce `ExtractedElement` instances with `semantic_type="operation"`, which the CFM classifier routes to `Operation` entities. The CFM builder's `_infer_operation_direction()` infers direction from GWT keywords in the operation text. No engine or builder code changes are needed.

The 9 rules were originally classified as `"fact"` but describe system behaviors, actions, and decisions that are operation-level concepts. This is a semantic correction, not a functional change to extraction logic.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Add new overlapping operation rules instead of changing existing ones | Would create duplicate extraction (same content matched by both fact and operation rules). The rule conflict resolution picks the higher-priority one, but creates confusion and noise. |
| Keep all as fact, rely on CFM classifier to reclassify | Violates separation of concerns. The extraction engine should produce correct semantic types; the classifier's job is CFM-level classification (actor vs data_group), not fixing extraction-level misclassifications. |
| Change only THEN/AND/WHEN, skip task/decision rules | Task items and decision records, while not behavioral operations in the strict sense, describe implementation and design operations. They enrich the functional process model and provide structural context. |

### Rules Changed

| Rule ID | Original Type | New Type | Line | Pattern | Priority |
|---------|--------------|----------|------|---------|----------|
| `openspec-req-heading` | fact | operation | 50 | `### Requirement: (.+)` | 80 |
| `openspec-deve-statement` | fact | operation | 59 | `(DEVE\|NÃO DEVE) (.+)` | 78 |
| `openspec-shall-statement` | fact | operation | 69 | `(SHALL\|SHALL NOT) (.+)` | 75 |
| `openspec-then-assertion` | fact | operation | 104 | `**THEN** (.+)` | 75 |
| `openspec-decision-colon` | fact | operation | 122 | `### Decision (\d+): (.+)` | 80 |
| `openspec-what-changes` | fact | operation | 170 | `## What Changes` | 70 |
| `openspec-task-category` | fact | operation | 217 | `## (\d+). (.+)` | 65 |
| `openspec-task-item` | fact | operation | 226 | `[ ] (\d+.\d+) (.+)` | 65 |
| `openspec-and-clause` | fact | operation | 299 | `**AND** (.+)` | 70 |

### Rules NOT Changed (rationale)

| Rule ID | Reason Preserved |
|---------|-----------------|
| `openspec-scenario-heading` | Already `type: "operation"` (line 77) — correct |
| `openspec-when-trigger` | Already `type: "operation"` (line 95) — correct |
| `openspec-given-precondition` | Kept as `"fact"` — GIVEN is a precondition, not an operation. Preconditions are contextual facts. |
| `openspec-precondition` | Kept as `"entity"` — section heading marker |
| `openspec-decision-dot` | Kept as `"fact"` — Portuguese format `### N. Title`. Less common; colon format covers most decisions. |
| `openspec-modified-capabilities` | Kept as `"fact"` — modified capability marker, not a behavioral operation. |
| `openspec-modified-requirements` | Kept as `"fact"` — delta spec section marker. |
| `openspec-substitui-marker` | Kept as `"fact"` — annotation marker, not behavioral. |
| `openspec-why-section` | Kept as `"fact"` — section heading, not behavioral. |
| `openspec-context-section` | Kept as `"fact"` — section heading. |
| `openspec-goals-section` | Kept as `"fact"` — section heading. |
| `openspec-risk` | Kept as `"fact"` — risk statement, not an operation. |
| `openspec-tradeoff` | Kept as `"fact"` — trade-off statement. |
| `openspec-no-change` | Kept as `"fact"` — passive marker. |

### Direction Inference

The CFM builder's `_infer_operation_direction()` (in `cfm/builder.py:38-42`) already handles:

| Text Pattern | Direction |
|-------------|-----------|
| Contains `**WHEN**` or `**GIVEN**` | `"input"` |
| Contains `**THEN**` | `"output"` |
| Contains `#### Scenario:` | `"query"` |
| Fallback (DEVE, SHALL, etc.) | `"input"` |

Changed rules produce text that maps as follows:
- `openspec-then-assertion` → text contains `**THEN**` → `"output"` ✓
- `openspec-and-clause` → text contains `**AND**` → fallback `"input"` (deferred per clarification)
- Remaining 7 rules → fallback `"input"` (acceptable default for behavioral operations)

### No-code-change guarantee

The `ExtractedElement` type field is a free string. `GraphNode.semantic_type` is typed as `Literal["fact", "entity", "relationship", "operation"]`. The rule loader (`engine_rule.py`) passes rule.type directly. Changing `"fact"` → `"operation"` in YAML is all that's needed.
