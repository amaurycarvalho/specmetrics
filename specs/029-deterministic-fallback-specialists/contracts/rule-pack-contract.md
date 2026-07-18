# Rule Pack Contract

## Interface

The deterministic engine loads rule packs via `DeterministicSemanticEngine._load_framework_packs()`. Each rule pack is a YAML file implementing the schema below.

## Contract Rules

1. **Input**: A valid YAML file placed under `specmetrics/kernel/rules/` with filename `<framework>_rules.yaml`.
2. **Schema version**: Determined by the `version` field (semver `major.minor.patch`).
3. **Framework auto-detection**: The engine matches `document.document_type` against `document_types` in the pack metadata.
4. **Rule execution order**: Rules are executed in descending priority order (highest first).
5. **Additive-only**: Specialist rules never override default rules. When a document matches both, both are applied.
6. **Failure isolation**: A failing rule (regex exception) is caught, logged, and skipped — remaining rules continue.

## YAML Schema

```yaml
# spekit_rules.yaml / openspec_rules.yaml
version: "1.0.0"                          # Required: semver
framework: "speckit"                       # Required: framework identifier
document_types:                            # Required: applicable doc types
  - "specification"
  - "design"
  - "tasks"
description: "..."                         # Optional: human-readable description

rules:                                     # Required: ordered list
  - rule_id: "speckit-user-story"          # Required: unique within pack
    pattern: '^### User Story (\d+) [—–-] (.+) \(Priority: (P[1-3])\)'
    semantic_type: "entity"                # Required: entity | fact | operation
    confidence: 0.95                       # Required: 0.0-1.0
    priority: 80                           # Required: 1-100
    target_sections:                        # Optional: scope to these sections
      - "User Scenarios"
    capture_groups:                         # Optional: field mapping
      story_number: 1
      story_title: 2
      priority: 3
    document_type: "specification"          # Optional: doc type filter

  - rule_id: "speckit-fr-requirement"
    pattern: '^-\s+\*\*FR-(\d{3})\*\*: (.+)$'
    semantic_type: "fact"
    confidence: 0.95
    priority: 70
    target_sections:
      - "Functional Requirements"
    capture_groups:
      fr_number: 1
      description: 2
```

## Confidence Score Reference

| Level | Score | When Applied |
|-------|-------|-------------|
| Explicit heading match | 1.00 | Direct section header match |
| Framework convention | 0.95 | Known pattern from template analysis (User Story, FR-NNN, SC-NNN) |
| Structural heuristic | 0.85 | Pattern-inferred from section context (e.g., list items under Key Entities) |
| Pattern inference | 0.70 | Generic pattern match without specific section context |

## EvidenceReference Output Format

Every extracted element produces an evidence reference:

```json
{
  "document_id": "specs/007-canonical-functional-model/spec.md",
  "section_id": "## Requirements",
  "text_fragment": "FR-001: The CFM Builder MUST accept an EvidenceGraph...",
  "rule_id": "speckit-fr-requirement"
}
```

## Compatibility

- Rule packs with matching major version against engine compatibility range load normally.
- Rule packs with major version mismatch load with a WARN-level log message.
- Minor/patch mismatches load without warning (assumed backward-compatible).
