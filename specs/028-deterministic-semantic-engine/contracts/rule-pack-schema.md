# Contract: Rule Pack Schema

**Version**: 1.0.0 | **Date**: 2026-07-17 | **Spec**: [spec.md](../spec.md) | **Data Model**: [data-model.md](../data-model.md)

---

## Purpose

Defines the schema for external rule pack YAML files. Rule packs are loaded by `RulePackLoader` and used by `PatternLibrary` to match structural observations against known specification patterns.

---

## File Format

Rule packs are YAML files containing a single `rules` key with an array of rule definitions.

```yaml
rules:
  - id: "user-story"
    name: "User Story"
    pattern:
      keywords: ["As a", "I want", "So that"]
      min_matches: 2
    type: "entity"
    confidence: 0.95
    priority: 80

  - id: "gwt"
    name: "Given/When/Then"
    pattern:
      keywords: ["Given", "When", "Then"]
      min_matches: 2
    type: "fact"
    confidence: 0.85
    priority: 70
```

---

## Field Reference

### `id` (string, required)

Unique identifier for the rule within the rule pack. Used in evidence references (`rule_id`) and conflict resolution (tiebreaker).

**Constraints**: Must be non-empty, unique within a single pack, and use lowercase kebab-case (e.g., `"user-story"`, `"business-rule-if-then"`).

### `name` (string, required)

Human-readable name for the rule. Used in logging and diagnostics.

### `pattern` (dict, required)

Defines the structural or textual pattern to match. Supported sub-fields:

| Sub-field | Type | Description |
|-----------|------|-------------|
| `keywords` | `list[str]` | Keywords to search for in observation content; all keywords must be present unless `min_matches` is set |
| `min_matches` | `int` | Minimum number of keywords that must match (default: all keywords) |
| `heading` | `str` or `list[str]` | Heading text to match exactly (case-insensitive); alternative to keywords for heading-based rules |
| `structure` | `str` | Structural pattern type: `"list"`, `"table"`, `"code_block"`, `"quote"` |

### `type` (string, required)

Semantic type of the extracted element.

**Allowed values**: `"fact"`, `"entity"`, `"relationship"`, `"operation"`

### `confidence` (float, required)

Confidence score assigned to elements produced by this rule.

**Constraints**: 0.0–1.0. Use values from the RFC-031 table: explicit heading match = 1.00, framework convention = 0.95, structural heuristic = 0.85, pattern inference = 0.70.

### `priority` (integer, required)

Numeric priority for conflict resolution.

**Constraints**: 1–100. Higher values win when multiple rules match the same observation. Ties are broken by `id` lexicographic order.

---

## Built-in Rule Packs

The following rule packs are shipped with the engine:

| Pack File | Rules Included |
|-----------|----------------|
| `default_rule_pack.yaml` | User Story, GWT, Requirement statements, Business Rules, Actors, Constraints, Assumptions, Decisions, Glossary Terms |
| `openspec_rules.yaml` | OpenSpec framework-specific rules (if detected) |
| `speckit_rules.yaml` | SpecKit framework-specific rules (if detected) |

---

## Custom Rule Pack Example

```yaml
rules:
  - id: "safety-constraint"
    name: "Safety Constraint"
    pattern:
      keywords: ["Safety", "Constraint", "Must ensure"]
      min_matches: 2
    type: "fact"
    confidence: 0.90
    priority: 85

  - id: "performance-target"
    name: "Performance Target"
    pattern:
      keywords: ["Performance", "Target", "Under", "Seconds"]
      min_matches: 2
    type: "fact"
    confidence: 0.85
    priority: 80
```

---

## Validation Rules

When `RulePackLoader` processes a rule pack:

1. Each rule MUST have all required fields (`id`, `name`, `pattern`, `type`, `confidence`, `priority`).
2. `id` MUST be non-empty and unique within the pack.
3. `type` MUST be one of `"fact"`, `"entity"`, `"relationship"`, `"operation"`.
4. `confidence` MUST be in range [0.0, 1.0].
5. `priority` MUST be in range [1, 100].
6. `pattern` MUST contain at least one of: `keywords`, `heading`, or `structure`.
7. Invalid rules are skipped with a logged warning; valid rules continue to load.

---

## File Location

Rule pack files are loaded from the `specmetrics/kernel/rules/` directory. The engine's `default_rule_pack` config option can point to any path, but the convention is to place built-in packs in this directory.
