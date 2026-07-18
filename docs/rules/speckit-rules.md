# Speckit Rule Pack

**File**: `specmetrics/kernel/rules/speckit_rules.yaml`
**Version**: 1.0.0
**Framework**: speckit

## Document Types

- specification
- plan
- tasks
- data-model

## Rules

| Rule ID | Type | Confidence | Priority | Pattern |
|---------|------|-----------|----------|---------|
| speckit-feature | entity | 1.00 | 95 | Heading: Feature |
| speckit-scenario | entity | 1.00 | 95 | Heading: Scenario |
| speckit-background | entity | 1.00 | 95 | Heading: Background |
| speckit-user-story | entity | 0.95 | 80 | `^### User Story (\d+) [—–-] (.+) \(Priority: (P[1-3])\)` |
| speckit-priority-justification | fact | 0.80 | 75 | `^\*\*Why this priority\*\*: (.+)$` |
| speckit-gwt-numbered | fact | 0.90 | 75 | `^(\d+)\. \*\*Given\*\* (.+), \*\*When\*\* (.+), \*\*Then\*\* (.+)$` |
| speckit-gwt-multiline-given | fact | 0.90 | 75 | `^-\s+\*\*Given\*\* (.+)$` |
| speckit-gwt-multiline-when | fact | 0.90 | 75 | `^-\s+\*\*When\*\* (.+)$` |
| speckit-gwt-multiline-then | fact | 0.90 | 75 | `^-\s+\*\*Then\*\* (.+)$` |
| speckit-fr-requirement | fact | 0.95 | 70 | `^-\s+\*\*FR-(\d{3})\*\*: (.+)$` |
| speckit-sc-success-criteria | fact | 0.95 | 70 | `^-\s+\*\*SC-(\d{3})\*\*: (.+)$` |
| speckit-key-entity | entity | 0.90 | 65 | `^-\s+\*\*(.+)\*\*: (.+)$` |
| speckit-actor-entity | entity | 0.85 | 68 | `^-\s+\*\*([A-Z][a-zA-Z]+)\*\*: (.+)$` |
| speckit-assumption | fact | 0.90 | 60 | `^-\s+(.+)$` |
| speckit-engaged-principles | fact | 0.95 | 75 | `^\*\*Engaged Principles\*\*: (.+)$` |
| speckit-edge-case | fact | 0.85 | 60 | `^-\s+What happens (.+)\? (.+)$` |
| speckit-imp-note | fact | 0.90 | 65 | `^-\s+\*\*IMP-\d+\*\*: (.+)$` |
| speckit-task-line | fact | 0.90 | 60 | `^-\s+\[([ xX])\]\s+(T\d{3})(?:\s+\[P\])?\s*(?:\[(US[1-4])\])?\s*(.+)$` |
