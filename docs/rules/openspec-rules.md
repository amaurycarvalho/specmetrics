# OpenSpec Rule Pack

**File**: `specmetrics/kernel/rules/openspec_rules.yaml`
**Version**: 1.0.0
**Framework**: openspec

## Document Types

- specification
- proposal
- design
- tasks
- delta

## Rules

| Rule ID | Type | Confidence | Priority | Pattern |
|---------|------|-----------|----------|---------|
| openspec-use-case | entity | 1.00 | 95 | Heading: Use Case |
| openspec-actor | entity | 1.00 | 95 | Heading: Actor |
| openspec-requirement | entity | 1.00 | 95 | Heading: Requirement |
| openspec-precondition | fact | 1.00 | 95 | Heading: Precondition |
| openspec-req-heading | fact | 0.95 | 80 | `^### Requirement: (.+)$` |
| openspec-deve-statement | fact | 0.95 | 78 | `(O sistema\|O [A-Z][a-zA-Z]+\|[A-Z][a-zA-Z]+) (DEVE\|NÃO DEVE\|DEVEM\|NÃO DEVEM) (.+)` |
| openspec-shall-statement | fact | 0.90 | 75 | `(The system\|[A-Z][a-zA-Z]+) (SHALL\|SHALL NOT\|SHOULD\|MAY) (.+)` |
| openspec-scenario-heading | operation | 0.95 | 80 | `^#### Scenario: (.+)$` |
| openspec-given-precondition | fact | 0.90 | 75 | `^-\s+\*\*GIVEN\*\* (.+)$` |
| openspec-when-trigger | operation | 0.95 | 78 | `^-\s+\*\*WHEN\*\* (.+)$` |
| openspec-then-assertion | fact | 0.90 | 75 | `^-\s+\*\*THEN\*\* (.+)$` |
| openspec-capability-id | entity | 0.85 | 70 | `\b(FS\d{3}\|DC\d{3}\|DR\d{3}\|DT\d{3}\|DP\d{3}\|IC\d{3}\|LC\d{3}\|REQ-[A-Z0-9-]+)\b` |
| openspec-decision-colon | fact | 0.95 | 80 | `^### Decision (\d+): (.+)$` |
| openspec-decision-dot | fact | 0.90 | 78 | `^### (\d+)\. (.+)$` |
| openspec-risk | fact | 0.90 | 75 | `^-\s+\[Risk\] (.+) → Mitigation: (.+)$` |
| openspec-tradeoff | fact | 0.90 | 75 | `^-\s+\[Trade-off\] (.+) → Acceptable because (.+)$` |
| openspec-why-section | fact | 0.90 | 70 | `^## Why$` |
| openspec-what-changes | fact | 0.90 | 70 | `^## What Changes$` |
| openspec-context-section | fact | 0.90 | 70 | `^## Context$` |
| openspec-goals-section | fact | 0.90 | 70 | `^## Goals / Non-Goals$` |
| openspec-new-capabilities | entity | 0.95 | 80 | `^### New Capabilities$` |
| openspec-modified-capabilities | fact | 0.90 | 75 | `^### Modified Capabilities$` |
| openspec-task-category | fact | 0.85 | 65 | `^## (\d+)\. (.+)$` |
| openspec-task-item | fact | 0.85 | 65 | `^-\s+\[([ xX])\]\s+(\d+\.\d+)\s+(.+)$` |
| openspec-domain-entity | entity | 0.85 | 65 | `\b(TradeDay\|AggregatedMetrics\|DominanceClassification\|...)\b` |
| openspec-purpose | entity | 0.90 | 70 | `^## Purpose$` |
| openspec-actor-ref | entity | 0.80 | 60 | `\b(Usuário\|Sistema\|Cliente\|Analista\|Operador\|User\|System\|Client\|Analyst\|Operator)\b` |
| openspec-added-requirements | entity | 0.95 | 85 | `^## ADDED Requirements$` |
| openspec-modified-requirements | fact | 0.95 | 85 | `^## MODIFIED Requirements$` |
| openspec-substitui-marker | fact | 0.90 | 70 | `\(substitui .+?\)` |
| openspec-no-change | fact | 1.00 | 10 | `No specification changes required` |
| openspec-and-clause | fact | 0.85 | 70 | `^-\s+\*\*AND\*\* (.+)$` |
