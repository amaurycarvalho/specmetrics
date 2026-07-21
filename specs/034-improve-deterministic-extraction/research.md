# Research: Deterministic Extraction Improvements

**Feature**: 034-improve-deterministic-extraction
**Date**: 2026-07-20

## Decision 1: Operation Rule Design

### Decision
Add `type: "operation"` rules to `default_rule_pack.yaml` and `speckit_rules.yaml` that detect GWT (Given/When/Then) patterns and assign direction based on the matched keyword.

### Rationale
The existing rule packs define rules with `type: "entity"` and `type: "fact"` only. The `ExtractedElement.type` maps directly to `GraphNode.semantic_type`, which the CFM classifier reads. `semantic_type="operation"` is already supported by the classifier (`classify_node` returns `"operation"` for this type, and the builder creates `Operation` objects with direction metadata from `_infer_operation_direction`).

Adding operation rules is the simplest, least invasive path — no code changes needed in the extraction engine, classifier, or builder for operation support. Only YAML rules need updating.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Add hardcoded operation detection in `deterministic_engine.py` | Violates Principle IX (Rule Externalization). Rules should be in YAML packs. |
| Use LLM for operation detection only | Violates Principle IV (LLM-Assisted, Deterministic Results). Must work without LLM. |
| Create a new `OperationVisitor` in `engine_visitors.py` | Over-engineering. Existing rule-matching infrastructure handles pattern detection. |

### Rule Design

**Keyword match rules** — use the existing `keywords` pattern type:

```yaml
- id: "gwt-given-operation"
  name: "GIVEN as Input Operation"
  pattern:
    keywords: ["**GIVEN**", "**Given**"]
    min_matches: 1
  type: "operation"
  confidence: 0.85
  priority: 72

- id: "gwt-when-operation"
  name: "WHEN as Input Operation"
  pattern:
    keywords: ["**WHEN**", "**When**"]
    min_matches: 1
  type: "operation"
  confidence: 0.85
  priority: 72

- id: "gwt-then-operation"
  name: "THEN as Output Operation"
  pattern:
    keywords: ["**THEN**", "**Then**"]
    min_matches: 1
  type: "operation"
  confidence: 0.85
  priority: 72
```

**Regex match rules** — for existing speckit patterns that currently use `type: "fact"`:

Change existing rules from `type: "fact"` to `type: "operation"` for GWT patterns:
- `speckit-gwt-numbered` (line 58): Change `type: "fact"` → `type: "operation"`
- `speckit-gwt-multiline-given` (line 68): Change `type: "fact"` → `type: "operation"`  
- `speckit-gwt-multiline-when` (line 78): Change `type: "fact"` → `type: "operation"`
- `speckit-gwt-multiline-then` (line 88): Change `type: "fact"` → `type: "operation"`

Direction inference: The CFM builder's `_infer_operation_direction()` already maps `**GIVEN**`/`**WHEN**` → `"input"` and `**THEN**` → `"output"` (line 30-35 of `cfm/builder.py`). No code changes needed.

### Conflict Resolution
Existing `speckit-gwt-numbered` has priority 75. New keyword rules should have priority 72 to avoid conflicts. The regex rules from speckit take precedence for exact format matches; keyword rules catch remaining bold GWT patterns.

---

## Decision 2: SNAP Semantic Marker Inference

### Decision
Add a `_infer_semantic_marker()` function to the CFM builder that assigns `semantic_marker` metadata based on the element's CFM type and document section context from its evidence reference.

### Rationale
SNAP requires `metadata["semantic_marker"]` on every CFM element. Currently no element has this, causing 100% `MISSING_SEMANTIC_MARKER` warnings. The section identifier in `evidence.section_id` provides context for inferring the marker (e.g., "Data Model" → data_operation, "User Scenarios" → presentation_interface).

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| Add marker to extraction rules (YAML) | Markers are CFM-level concepts; extraction rules produce generic semantic types. Separation of concerns. |
| Require manual marker assignment via rule packs | Too burdensome for users. Default inference provides a working baseline. |
| Skip inference, keep SNAP at zero | Defeats purpose of the feature. SNAP is a supported methodology. |

### Marker-to-Section Mapping

| semantic_marker | CFM Element Types | Section Patterns |
|-----------------|-------------------|------------------|
| `presentation_interface` | business_rule | "User Scenarios", "User Story", "Scenario", "Acceptance", "UI" |
| `data_operation` | data_group | "Data Model", "Key Entities", "Entities", "Schema" |
| `operational_feature` | business_rule, operation | "Functional Requirements", "Features", "Requirements", "Specification" |
| `technical_interface` | business_rule | "Integration", "API", "Contracts", "Technical", "Architecture" |

Fallback: Elements that don't match any section pattern get `semantic_marker` based on their CFM type: data_group → `data_operation`, operation → `operational_feature`, business_rule → `operational_feature`, actor → `operational_feature`.

### Implementation Location
`cfm/builder.py` — called during `build()` when constructing each CFM element (Actor, BusinessRule, DataGroup, Operation). The `element.evidence.section_id` provides the section context string.

---

## Decision 3: Actor Classification Heuristics

### Decision
Enhance `_classify_entity()` in `cfm/classifier.py` to add section-context-aware actor detection and expand the ACTOR_PATTERNS list with additional role keywords.

### Rationale
Currently all 61 entities are classified as `data_group` because none match the strict actor patterns. The classifier's Rule A (exact name match against 24 keywords) doesn't catch entity names that contain role words in larger text strings. Adding section-context awareness and key phrase matching improves recall.

### Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| ML-based entity classification | Over-engineering. Heuristic rules are sufficient for deterministic extraction. |
| Always classify entities as data_group first, then reclassify | Creates complexity. Actor-first ordering (FR-009) is simpler. |
| Add actor patterns only via YAML rule packs | Heuristics are core classification logic, not organizational policy. Rule packs are for extraction, not CFM classification. |

### Improvements

1. **Section-context detection**: If entity appears under a heading containing "Actor", "Role", "User", or "Persona", classify as actor regardless of name patterns.

2. **Key phrase detection**: If entity text contains role-describing phrases like "acts as", "is a user", "represents a person", or "external system", classify as actor.

3. **Expanded ACTOR_PATTERNS**: Add more role keywords: "stakeholder", "moderator", "subscriber", "visitor", "guest", "consumer", "provider", "vendor", "partner".

4. **Priority adjustment**: Currently Rule A (exact match) has highest priority. Keep this ordering but add section-context check before the data-like check (Rule B). This satisfies FR-009 (actor precedence).

### Implementation Changes
`cfm/classifier.py:37-45` — Modify `_classify_entity()` to include section-context and key phrase checks between existing Rule A and Rule B.

---

## Edge Cases Addressed

| Edge Case | Resolution |
|-----------|-----------|
| Code blocks with GWT-like strings (false positives) | The existing `markdown-it-py` parser separates code blocks. The `CodeBlockVisitor` in `engine_visitors.py` already excludes code block content from observation generation. |
| Bullet lists instead of bold GWT | Not detected by keyword rules (require bold markers). Covered by speckit multiline rules (regex-based). |
| Entity matching both actor and data patterns | Actor classification takes precedence (FR-009). Section context and key phrases provide additional signals. |
| Section not matching any marker mapping | Fallback to CFM-type-based default marker assignment. |
| Mixed SpecKit/plain markdown project | Rules without `target_sections` apply to all documents. Framework-specific rules filter by `document_type`. |
